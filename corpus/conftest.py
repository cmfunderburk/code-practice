"""The corpus's program tests: each language's core tests, and the shared smoke suite.

    uv run pytest corpus                       # everything
    uv run pytest corpus/easy/Hangman          # one program
    uv run pytest corpus -k python             # one language

Per program:
- `python/test_solution.py` tests the Python core through the `sub` fixture (a fresh
  import of `python/solution.py`);
- `rust/test_solution.rs` and `c/test_solution.c` test the ports' cores. Each is collected
  as one item, which builds and runs it;
- `test_program.py` is the smoke suite. It reads only SPEC's fixed output, so its
  `run_program` fixture runs it once per language against the whole program.

Rust needs cargo and C needs cc (C23, built with UBSan). A missing toolchain skips its
language. Builds go to `.build/` at the repo root.
"""

import functools
import importlib.util
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parent.parent / ".build"
LANGS = ("python", "rust", "c")
C_FLAGS = ["-std=c23", "-Wall", "-Wextra", "-Wpedantic", "-g", "-O1",
           "-fsanitize=undefined", "-fno-sanitize-recover=undefined", "-fno-omit-frame-pointer"]
TIMEOUT = 10


class BuildError(Exception):
    pass


def _run(args: list, cwd: Path | None = None, env: dict | None = None) -> str:
    """Run a build or test command; its output, or BuildError with that output."""
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True,
                            timeout=300)
    output = result.stdout + result.stderr
    if result.returncode:
        raise BuildError(f"$ {' '.join(map(str, args))}\n{output}")
    return output


def _require(tool: str) -> None:
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} not on PATH")


# --- Rust: a generated crate around the port, with its tests as a child module ---------

def _rust_crate(rust_dir: Path) -> tuple[Path, str]:
    """The harness crate for a port and its package name. Its main.rs is the solution
    plus `mod tests` pointing at test_solution.rs (`use super::*` reaches private items)."""
    manifest = tomllib.loads((rust_dir / "Cargo.toml").read_text())
    package = manifest["package"]
    name = package["name"]
    crate = BUILD / "rust" / name
    (crate / "src").mkdir(parents=True, exist_ok=True)
    deps = "".join(f'{k} = "{v}"\n' for k, v in manifest.get("dependencies", {}).items())
    (crate / "Cargo.toml").write_text(
        f'[package]\nname = "{name}"\nversion = "0.0.0"\nedition = "{package["edition"]}"\n'
        f"publish = false\n\n[dependencies]\n{deps}")
    if (rust_dir / "Cargo.lock").is_file():
        shutil.copy(rust_dir / "Cargo.lock", crate / "Cargo.lock")
    main = (rust_dir / "solution.rs").read_text()
    tests = (rust_dir / "test_solution.rs").resolve()
    (crate / "src" / "main.rs").write_text(
        f'{main}\n#[cfg(test)]\n#[path = "{tests}"]\nmod tests;\n')
    return crate, name


def _cargo(crate: Path, *args: str) -> str:
    env = {**os.environ, "CARGO_TERM_COLOR": "never", "CARGO_TARGET_DIR": str(BUILD / "target")}
    return _run(["cargo", *args, "--quiet"], cwd=crate, env=env)


# --- the whole program, per language ---------------------------------------------------

@functools.cache
def _program(program_dir: Path, lang: str) -> list:
    """The command that runs a program in a language, built once per session."""
    if lang == "python":
        return [sys.executable, str(program_dir / "python" / "solution.py")]
    if lang == "rust":
        crate, name = _rust_crate(program_dir / "rust")
        _cargo(crate, "build")
        return [str(BUILD / "target" / "debug" / name)]
    binary = BUILD / "c" / program_dir.name
    binary.parent.mkdir(parents=True, exist_ok=True)
    _run([shutil.which("cc"), *C_FLAGS, str(program_dir / "c" / "solution.c"), "-o", str(binary)])
    return [str(binary)]


def pytest_generate_tests(metafunc):
    if "run_program" in metafunc.fixturenames:
        metafunc.parametrize("run_program", LANGS, indirect=True)


@pytest.fixture
def run_program(request):
    """Run the whole program on the given stdin; its stdout, asserting exit status 0."""
    lang = request.param
    if lang == "rust":
        _require("cargo")
    if lang == "c":
        _require("cc")
    try:
        command = _program(request.path.parent, lang)
    except BuildError as error:
        pytest.fail(f"{lang} build failed:\n{error}", pytrace=False)

    def run(data: str) -> str:
        result = subprocess.run(command, input=data, capture_output=True, text=True,
                                timeout=TIMEOUT)
        assert result.returncode == 0, result.stderr
        return result.stdout

    return run


@pytest.fixture
def sub(request):
    """The Python implementation, imported fresh for each test."""
    path = request.path.parent / "solution.py"
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["solution"] = module  # dataclasses look their module up while defining
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop("solution", None)


# --- the ports' core tests, as pytest items --------------------------------------------

def pytest_collect_file(parent, file_path):
    if file_path.name in ("test_solution.rs", "test_solution.c"):
        return NativeTests.from_parent(parent, path=file_path)


class NativeTests(pytest.File):
    def collect(self):
        lang = "rust" if self.path.suffix == ".rs" else "c"
        yield NativeTest.from_parent(self, name=f"{lang} core tests", lang=lang)


class NativeTest(pytest.Item):
    def __init__(self, *, lang: str, **kwargs):
        super().__init__(**kwargs)
        self.lang = lang

    def runtest(self):
        port = self.path.parent
        if self.lang == "rust":
            _require("cargo")
            crate, _ = _rust_crate(port)
            _cargo(crate, "test")
            return
        _require("cc")
        binary = BUILD / "c" / f"{port.parent.name}-tests"
        binary.parent.mkdir(parents=True, exist_ok=True)
        # test_solution.c includes solution.c itself, renaming its main.
        _run([shutil.which("cc"), *C_FLAGS, str(self.path), "-o", str(binary)])
        _run([str(binary)], cwd=port)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, BuildError):
            return str(excinfo.value)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, None, self.name
