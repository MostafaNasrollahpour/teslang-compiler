import sys
from lexer import Lexer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from code_generator import CodeGenerator   # اضافه کن

def main():
    text = sys.stdin.read()
    lexer = Lexer(text)
    parser = Parser(lexer)
    try:
        ast = parser.parse_program()
        analyzer = SemanticAnalyzer()
        analyzer.visit(ast)
        if analyzer.errors:
            for err in analyzer.errors:
                print(err, file=sys.stderr)
            sys.exit(1)
        # اضافه کن:
        gen = CodeGenerator()
        gen.visit(ast)
        with open("output.tsl", "w") as f:
            f.write(gen.get_code())
    except SyntaxError as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()