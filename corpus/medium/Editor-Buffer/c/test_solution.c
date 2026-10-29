// The program's own main is renamed so these tests can include its core.
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <uchar.h>

#define main editor_main
#include "solution.c"
#undef main

static bool text_is(const Editor *editor, const char32_t *expected) {
    size_t len = 0;
    while (expected[len]) len++;
    return editor->text.len == len &&
           (len == 0 || memcmp(editor->text.chars, expected, len * sizeof expected[0]) == 0);
}

static bool insert(Editor *editor, size_t pos, const char *utf8) {
    return editor_insert(editor, pos, utf8, strlen(utf8));
}

static Request parsed(const char *line) { return parse(line, strlen(line)); }

int main(void) {
    // The scripted replay; a new edit clears redo.
    Editor editor = {};
    assert(insert(&editor, 0, "hello") && insert(&editor, 5, " world"));
    assert(editor_delete(&editor, 0, 6) && text_is(&editor, U"world"));
    assert(editor_undo(&editor) && text_is(&editor, U"hello world"));
    assert(editor_undo(&editor) && text_is(&editor, U"hello"));
    assert(editor_redo(&editor) && text_is(&editor, U"hello world"));
    assert(insert(&editor, 0, "big ") && text_is(&editor, U"big hello world"));
    assert(!editor_redo(&editor));
    editor_free(&editor);

    // Refused edits change neither the text nor either history.
    editor = (Editor){};
    assert(insert(&editor, 0, "ab") && editor_undo(&editor));
    assert(!insert(&editor, 5, "x") && !editor_delete(&editor, 0, 5));
    assert(!editor_delete(&editor, 0, 0) && !editor_delete(&editor, SIZE_MAX, SIZE_MAX));
    assert(editor_redo(&editor) && text_is(&editor, U"ab"));
    assert(insert(&editor, 2, "c") && editor_delete(&editor, 0, 3) && text_is(&editor, U""));
    assert(editor_undo(&editor) && editor_undo(&editor) && editor_undo(&editor));
    assert(!editor_undo(&editor) && text_is(&editor, U""));
    editor_free(&editor);

    // Positions count characters, and an empty insert is an edit.
    editor = (Editor){};
    assert(insert(&editor, 0, "héllo") && insert(&editor, 2, "\U0001F600"));
    assert(editor_delete(&editor, 1, 1) && text_is(&editor, U"h\U0001F600llo"));
    assert(editor_undo(&editor) && text_is(&editor, U"hé\U0001F600llo"));
    assert(insert(&editor, 0, "") && !editor_redo(&editor));
    editor_free(&editor);

    // The parser: one space between fields, the text whole after the second.
    Request request = parsed("i 5  world");
    assert(request.verb == 'i' && request.pos == 5 && request.text_len == 6);
    assert(memcmp(request.text, " world", 6) == 0);
    request = parsed("i 0 ");
    assert(request.verb == 'i' && request.text_len == 0);
    request = parsed("d 007 2");
    assert(request.verb == 'd' && request.pos == 7 && request.n == 2);
    assert(parsed("u").verb == 'u' && parsed("q").verb == 'q');
    const char *malformed[] = {
        "",       "x",      "uu",  "u ",      "i",      "i 5",   "i x y",
        "i -1 y", "i  1 y", "d 1", "d 1 2 3", "d 1  2", "d 1 x", "i 99999999999999999999999 y"};
    for (size_t i = 0; i < sizeof malformed / sizeof malformed[0]; i++)
        assert(parsed(malformed[i]).verb == 0);

    puts("all tests passed");
    return 0;
}
