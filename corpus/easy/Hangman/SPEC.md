# Hangman — SPEC

The game every implementation plays, in any language. The Python version
(`python/problem.md`) adds the API. Each implementation is its language's natural
program for this game: how it picks the word, words its output, and handles bad
input is its own. Only the output facts in §4 are fixed.

## 1. The game

The player guesses letters of a secret word, one at a time, with a budget of
**6 wrong guesses**.
- A guessed letter that is in the secret reveals every occurrence.
- A miss counts against the budget.
- The game is **won** when every letter of the secret has been guessed, and
  **lost** when the sixth miss is made.
- Guessing a letter already guessed, hit or miss, is rejected and costs nothing.

The program picks the secret at random, from its language's ordinary random
source, out of its own built-in list of words. Each word is lowercase `a`–`z`
and has at least two different letters, so no single letter wins alone. The
game rules never see a random source: the shell picks the word and hands it to
the core.

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

The exit status is 0 whenever input is well formed UTF-8 text.

## 3. A session (one implementation)

The Python version's shell prints this when it picks `jigsaw`; other
implementations may word it their own way.

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

## 4. Fixed output

These are the only output facts every implementation keeps fixed; all other
wording is each implementation's own:
- When the game ends, one line contains the word `won` or the word `lost` (any
  case) and ends with the secret word (trailing punctuation allowed). No other
  line contains `won` or `lost`, apart from a secret shown as a line's last word.
- Every guess line is answered: a line that is not one letter produces at least
  one line of output.
