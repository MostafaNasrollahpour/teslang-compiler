from tokens import Token, TokenType

class Lexer:
    def __init__(self, text: str):
        if text.startswith('\ufeff'):
            text = text[1:]
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(text)

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.text[idx] if idx < self.length else None

    def advance(self):
        ch = self.text[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace(self):
        while self.pos < self.length:
            ch = self.peek()
            if ch in (' ', '\t', '\n', '\r'):
                self.advance()
            else:
                break

    def read_identifier_or_keyword(self):
        start_line, start_col = self.line, self.col
        value = ''
        while True:
            ch = self.peek()
            if ch is None or (not ch.isalnum() and ch != '_'):
                break
            value += self.advance()
        kw_map = {
            'funk': TokenType.FUNK,
            'int': TokenType.INT,
            'vector': TokenType.VECTOR,
            'str': TokenType.STR,
            'mstr': TokenType.MSTR,
            'bool': TokenType.BOOL,
            'null': TokenType.NULL,
            'as': TokenType.AS,
            'return': TokenType.RETURN,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'endif': TokenType.ENDIF,
            'while': TokenType.WHILE,
            'endwhile': TokenType.ENDWHILE,
            'do': TokenType.DO,
            'for': TokenType.FOR,
            'to': TokenType.TO,
            'begin': TokenType.BEGIN,
            'end': TokenType.END,          # جدید
            'endfor': TokenType.ENDFOR,
            'scan': TokenType.SCAN,
            'print': TokenType.PRINT,
            'list': TokenType.LIST,
            'length': TokenType.LEN,
            'exit': TokenType.EXIT,
        }
        ttype = kw_map.get(value, TokenType.ID)
        return Token(ttype, value, start_line, start_col)

    def read_number(self):
        start_line, start_col = self.line, self.col
        value = ''
        while True:
            ch = self.peek()
            if ch is None or not ch.isdigit():
                break
            value += self.advance()
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def read_string(self, quote_char):
        start_line, start_col = self.line, self.col
        self.advance()
        value = ''
        while True:
            ch = self.peek()
            if ch is None:
                raise SyntaxError(f"Unclosed string at {self.line}:{self.col}")
            if ch == '\\':
                self.advance()
                esc = self.peek()
                if esc is None:
                    raise SyntaxError("Unfinished escape")
                if esc == 'n':
                    value += '\n'
                elif esc == 't':
                    value += '\t'
                else:
                    value += esc
                self.advance()
            elif ch == quote_char:
                self.advance()
                break
            else:
                value += self.advance()
        return Token(TokenType.STRING, value, start_line, start_col)

    def read_multiline_string(self):
        start_line, start_col = self.line, self.col
        for _ in range(3):
            self.advance()
        value = ''
        while True:
            ch = self.peek()
            if ch is None:
                raise SyntaxError("Unclosed multiline string")
            if ch == '"' and self.peek(1) == '"' and self.peek(2) == '"':
                for _ in range(3):
                    self.advance()
                break
            value += self.advance()
        return Token(TokenType.MULTILINE_STRING, value, start_line, start_col)

    def skip_comment(self):
        depth = 1
        while depth > 0 and self.pos < self.length:
            if self.peek() == '<' and self.peek(1) == '/':
                self.advance()
                self.advance()
                depth += 1
            elif self.peek() == '/' and self.peek(1) == '>':
                self.advance()
                self.advance()
                depth -= 1
            else:
                self.advance()
        if depth > 0:
            raise SyntaxError(f"Unclosed comment at {self.line}:{self.col}")

    def get_next_token(self):
        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break

            ch = self.peek()

            if ch == '<' and self.peek(1) == '/':
                self.advance()
                self.advance()
                self.skip_comment()
                continue

            if ch == '"':
                if self.peek(1) == '"' and self.peek(2) == '"':
                    return self.read_multiline_string()
                else:
                    return self.read_string('"')
            if ch == "'":
                return self.read_string("'")

            if ch.isdigit():
                return self.read_number()

            if ch.isalpha() or ch == '_':
                return self.read_identifier_or_keyword()

            start_line, start_col = self.line, self.col
            two_char = ch + (self.peek(1) or '')
            if two_char == '==':
                self.advance(); self.advance()
                return Token(TokenType.EQUAL, '==', start_line, start_col)
            if two_char == '<=':
                self.advance(); self.advance()
                return Token(TokenType.LESS_EQUAL, '<=', start_line, start_col)
            if two_char == '>=':
                self.advance(); self.advance()
                return Token(TokenType.GREATER_EQUAL, '>=', start_line, start_col)
            if two_char == '!=':
                self.advance(); self.advance()
                return Token(TokenType.NOT_EQUAL, '!=', start_line, start_col)
            if two_char == '::':
                self.advance(); self.advance()
                return Token(TokenType.DBL_COLON, '::', start_line, start_col)
            if two_char == '&&':
                self.advance(); self.advance()
                return Token(TokenType.AND, '&&', start_line, start_col)
            if two_char == '||':
                self.advance(); self.advance()
                return Token(TokenType.OR, '||', start_line, start_col)
            if two_char == '=>':
                self.advance(); self.advance()
                return Token(TokenType.ARROW, '=>', start_line, start_col)

            single_map = {
                '<': TokenType.LESS_THAN,
                '>': TokenType.GREATER_THAN,
                '=': TokenType.EQ,
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MOD,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LCURLYEBR,
                '}': TokenType.RCURLYEBR,
                '[': TokenType.LSQUAREBR,
                ']': TokenType.RSQUAREBR,
                ';': TokenType.SEMI_COLON,
                ':': TokenType.COLON,
                ',': TokenType.COMMA,
                '?': TokenType.QUESTION,
                '!': TokenType.NOT,
            }
            if ch in single_map:
                self.advance()
                return Token(single_map[ch], ch, start_line, start_col)

            raise SyntaxError(f"Unexpected character '{ch}' at {self.line}:{self.col}")

        return Token(TokenType.EOF, '', self.line, self.col)