import sys
from lexer import Lexer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer

def main():
    text = sys.stdin.read()
    lexer = Lexer(text)
    parser = Parser(lexer)
    try:
        ast = parser.parse_program()
        # آنالیز معنایی
        analyzer = SemanticAnalyzer()
        analyzer.visit(ast)
        if analyzer.errors:
            for err in analyzer.errors:
                print(err)
            sys.exit(1)
        else:
            print("Parsing and semantic analysis successful! AST:")
            print(ast)
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()