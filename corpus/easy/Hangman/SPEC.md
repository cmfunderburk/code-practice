# Hangman — SPEC

This document specifies a game of Hangman played at a terminal. There are three
versions of it, in Python, C, and Rust, and each is written the way a programmer in
that language would usually write it. All three follow the same rules (§1). They
may differ in how they pick the word, how they word their output, and how they
read lines that are not a plain single letter.

The Python version's API is in `python/problem.md`. Each version has its own
tests, and all three also run the shared tests in `test_program.py`, which check
only the facts in §4.

## 1. The game

The player guesses letters of a secret word, one at a time, with a budget of
**6 wrong guesses**.
- A guessed letter that is in the secret reveals every occurrence.
- A miss counts against the budget.
- The game is **won** when every letter of the secret has been guessed, and
  **lost** when the sixth miss is made.
- Guessing a letter already guessed, hit or miss, is rejected and costs nothing.

The program picks the secret at random from its own built-in list of words, using
the random number source a programmer in its language would usually reach for.
Each word is lowercase `a`–`z` and has at least two different letters, so no
single letter can win the game alone. The code that applies the rules never uses
the random source: `main` picks the word and passes it in when it starts the
game.

## 2. Playing

The program is played at a terminal, one guess per line, on stdin and stdout.
- A guess is one letter `a`–`z`. An uppercase letter counts as its lowercase
  form.
- Before each guess the player can see the secret with its unguessed letters
  hidden, and how many of the 6 misses are used.
- Any other line (empty, two characters, a digit, a non-ASCII letter) is
  answered with a reminder of what a guess is. It costs nothing.
- A repeated guess is answered too, and costs nothing.
- When the game ends, the program says whether the player won or lost, shows the
  word, and stops reading.
- If input ends first, the program stops. It may show the word.

The program exits with status 0 whenever its input is well-formed UTF-8 text.

## 3. A sample session (the Python version)

The Python version prints this when it picks `jigsaw`. The C and Rust versions
print the same lines for this session, but may word their output differently
elsewhere, and read some other lines differently. For example, the Python and
Rust versions ignore spaces around a guess, while the C version answers ` j `
(with spaces) with the reminder.

```
______  wrong: 0/6
> e
______  wrong: 1/6
> I
_i____  wrong: 1/6
> i
already guessed: i
_i____  wrong: 1/6
> 7
one letter a-z, please
_i____  wrong: 1/6
> j
ji____  wrong: 1/6
```

(`> ` marks the player's lines, which a terminal echoes; the program prints no
prompt.)

## 4. What the shared tests check

These are the only facts about the output that every version must share:
- When the game ends, one line contains the word `won` or the word `lost` (in any
  case) and ends with the secret word (punctuation after it is allowed). No other
  line contains the word `won` or `lost` before its last word. (The last word of a
  line is not checked, since it may be the secret.)
- Every line the player types gets an answer: a line that is not one letter
  produces at least one line of output.
