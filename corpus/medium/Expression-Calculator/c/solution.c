// Expression Calculator: whole program.

#include <inttypes.h>
#include <stdckdint.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char kind;
    int64_t value;
} Token;

typedef enum { NUMBER, NEGATE, BINARY } Kind;

typedef struct {
    Kind kind;
    char op;
    int64_t value;
    size_t left, right;
} Node;

typedef struct {
    bool is_float;
    union {
        int64_t integer;
        double real;
    };
} Value;

typedef struct {
    const Token *tokens;
    size_t count, pos;
    Node *nodes;
    size_t used;
    const char **error;
} Parser;

static void *xrealloc(void *block, size_t count, size_t size) {
    size_t bytes = 0;
    void *grown = ckd_mul(&bytes, count, size) ? nullptr : realloc(block, bytes);
    if (grown == nullptr) {
        fputs("out of memory\n", stderr);
        exit(EXIT_FAILURE);
    }
    return grown;
}

static void *reserve(void *block, size_t *capacity, size_t needed, size_t size) {
    if (needed <= *capacity) return block;
    size_t count = 0;
    if (ckd_mul(&count, *capacity, 2) || count < needed) count = needed > 16 ? needed : 16;
    *capacity = count;
    return xrealloc(block, count, size);
}

static bool tokenize(const char *text, size_t len, Token tokens[], size_t *count,
                     const char **error) {
    size_t n = 0;
    for (size_t i = 0; i < len;) {
        char ch = text[i];
        if (ch == ' ' || ch == '\t') {
            i++;
        } else if (ch >= '0' && ch <= '9') {
            int64_t value = 0;
            for (; i < len && text[i] >= '0' && text[i] <= '9'; i++) {
                if (ckd_mul(&value, value, 10) || ckd_add(&value, value, text[i] - '0')) {
                    *error = "number too large";
                    return false;
                }
            }
            tokens[n++] = (Token){.kind = 'n', .value = value};
        } else if (ch != '\0' && strchr("+-*/()", ch)) {
            tokens[n++] = (Token){.kind = ch};
            i++;
        } else {
            *error = "unknown character";
            return false;
        }
    }
    *count = n;
    return true;
}

static size_t add_node(Parser *p, Node node) {
    p->nodes[p->used] = node;
    return p->used++;
}

static bool at(const Parser *p, char kind) {
    return p->pos < p->count && p->tokens[p->pos].kind == kind;
}

static bool parse_expr(Parser *p, size_t *node);

static bool parse_factor(Parser *p, size_t *node) {
    if (p->pos == p->count) {
        *p->error = "unexpected end of input";
        return false;
    }
    Token token = p->tokens[p->pos++];
    if (token.kind == '-') {
        size_t operand = 0;
        if (!parse_factor(p, &operand)) return false;
        *node = add_node(p, (Node){.kind = NEGATE, .left = operand});
        return true;
    }
    if (token.kind == '(') {
        if (!parse_expr(p, node)) return false;
        if (!at(p, ')')) {
            *p->error = "expected )";
            return false;
        }
        p->pos++;
        return true;
    }
    if (token.kind == 'n') {
        *node = add_node(p, (Node){.kind = NUMBER, .value = token.value});
        return true;
    }
    *p->error = "unexpected token";
    return false;
}

static bool parse_term(Parser *p, size_t *node) {
    if (!parse_factor(p, node)) return false;
    while (at(p, '*') || at(p, '/')) {
        char op = p->tokens[p->pos++].kind;
        size_t right = 0;
        if (!parse_factor(p, &right)) return false;
        *node = add_node(p, (Node){.kind = BINARY, .op = op, .left = *node, .right = right});
    }
    return true;
}

static bool parse_expr(Parser *p, size_t *node) {
    if (!parse_term(p, node)) return false;
    while (at(p, '+') || at(p, '-')) {
        char op = p->tokens[p->pos++].kind;
        size_t right = 0;
        if (!parse_term(p, &right)) return false;
        *node = add_node(p, (Node){.kind = BINARY, .op = op, .left = *node, .right = right});
    }
    return true;
}

static bool parse(Parser *p, size_t *root) {
    if (!parse_expr(p, root)) return false;
    if (p->pos != p->count) {
        *p->error = "trailing input";
        return false;
    }
    return true;
}

static double real(Value value) { return value.is_float ? value.real : (double)value.integer; }

static bool apply(char op, Value a, Value b, Value *out, const char **error) {
    if (op == '/') {
        if (real(b) == 0.0) {
            *error = "division by zero";
            return false;
        }
        *out = (Value){.is_float = true, .real = real(a) / real(b)};
        return true;
    }
    if (a.is_float || b.is_float) {
        double x = real(a), y = real(b);
        *out = (Value){.is_float = true, .real = op == '+' ? x + y : op == '-' ? x - y : x * y};
        return true;
    }
    int64_t result = 0;
    bool overflow = op == '+'   ? ckd_add(&result, a.integer, b.integer)
                    : op == '-' ? ckd_sub(&result, a.integer, b.integer)
                                : ckd_mul(&result, a.integer, b.integer);
    if (overflow) {
        *error = "integer overflow";
        return false;
    }
    *out = (Value){.integer = result};
    return true;
}

static bool evaluate(const Node nodes[], size_t index, Value *out, const char **error) {
    Node node = nodes[index];
    if (node.kind == NUMBER) {
        *out = (Value){.integer = node.value};
        return true;
    }
    Value left = {}, right = {};
    if (!evaluate(nodes, node.left, &left, error)) return false;
    if (node.kind == NEGATE) {
        if (left.is_float) {
            left.real = -left.real;
        } else if (ckd_sub(&left.integer, 0, left.integer)) {
            *error = "integer overflow";
            return false;
        }
        *out = left;
        return true;
    }
    if (!evaluate(nodes, node.right, &right, error)) return false;
    return apply(node.op, left, right, out, error);
}

static bool calculate(const char *text, size_t len, Value *result, const char **error) {
    Token *tokens = xrealloc(nullptr, len + 1, sizeof *tokens);
    Node *nodes = xrealloc(nullptr, len + 1, sizeof *nodes);
    Parser parser = {.tokens = tokens, .nodes = nodes, .error = error};
    size_t root = 0;
    bool ok = tokenize(text, len, tokens, &parser.count, error) && parse(&parser, &root) &&
              evaluate(nodes, root, result, error);
    free(tokens);
    free(nodes);
    return ok;
}

static void print_value(Value value) {
    if (value.is_float) {
        printf("%.15g\n", value.real);
    } else {
        printf("%" PRId64 "\n", value.integer);
    }
}

static bool read_line(char **line, size_t *capacity, size_t *len) {
    int ch = getchar();
    if (ch == EOF) return false;
    size_t count = 0;
    for (; ch != EOF && ch != '\n'; ch = getchar()) {
        *line = reserve(*line, capacity, count + 2, 1);
        (*line)[count++] = (char)ch;
    }
    *line = reserve(*line, capacity, count + 1, 1);
    (*line)[count] = '\0';
    *len = count;
    return true;
}

int main(void) {
    char *line = nullptr;
    size_t capacity = 0, len = 0;
    while (read_line(&line, &capacity, &len) && len > 0) {
        Value value = {};
        const char *error = nullptr;
        if (calculate(line, len, &value, &error)) {
            print_value(value);
        } else {
            printf("error: %s\n", error);
        }
    }
    free(line);
    return 0;
}
