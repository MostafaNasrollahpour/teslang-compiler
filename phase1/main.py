import sys
from lexer import Lexer
from token import TokenType

def main():
    text = sys.stdin.read()
    lexer = Lexer(text)
    while True:
        tok = lexer.get_next_token()
        if tok.type == TokenType.EOF:
            break
        # Output format: line column TYPE value
        print(f"{tok.line} {tok.column} {tok.type.name} {tok.value}")

if __name__ == "__main__":
    main()