# parser.py
from tokens import TokenType, Token
from lexer import Lexer
from teslang_ast import *

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.next_token = self.lexer.get_next_token()

    def advance(self):
        self.current_token = self.next_token
        self.next_token = self.lexer.get_next_token()

    def consume(self, expected_type: TokenType, error_msg: str = None):
        if self.current_token.type == expected_type:
            token = self.current_token
            self.advance()
            return token
        else:
            if error_msg is None:
                error_msg = f"Expected {expected_type.name}, got {self.current_token.type.name}"
            self.error(error_msg, self.current_token.line, self.current_token.column)

    def error(self, msg: str, line: int, col: int):
        raise SyntaxError(f"[Line {line}, Col {col}] {msg}")

    def consume_double_lsquare(self):
        self.consume(TokenType.LSQUAREBR, "Expected '['")
        self.consume(TokenType.LSQUAREBR, "Expected '['")

    def consume_double_rsquare(self):
        self.consume(TokenType.RSQUAREBR, "Expected ']'")
        self.consume(TokenType.RSQUAREBR, "Expected ']'")

    def parse_program(self) -> Program:
        functions = []
        while self.current_token.type != TokenType.EOF:
            functions.append(self.parse_function_decl())
        return Program(functions)

    def parse_function_decl(self) -> FunctionDecl:
        funk_token = self.current_token
        self.consume(TokenType.FUNK, "Expected 'funk'")
        self.consume(TokenType.LESS_THAN, "Expected '<'")
        ret_type = self.parse_type()
        self.consume(TokenType.GREATER_THAN, "Expected '>'")
        func_name_token = self.consume(TokenType.ID, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '('")
        params = self.parse_parameter_list()
        self.consume(TokenType.RPAREN, "Expected ')'")

        if self.current_token.type == TokenType.ARROW:
            self.advance()
            self.consume(TokenType.RETURN, "Expected 'return'")
            expr = self.parse_expression()
            self.consume(TokenType.SEMI_COLON, "Expected ';' after return")
            body = [ReturnStmt(expr)]
            return FunctionDecl(func_name_token.value, ret_type, params, body,
                                line=funk_token.line, col=funk_token.column)
        else:
            body = self.parse_block()
            return FunctionDecl(func_name_token.value, ret_type, params, body,
                                line=funk_token.line, col=funk_token.column)

    def parse_parameter_list(self) -> List[Param]:
        params = []
        if self.current_token.type != TokenType.RPAREN:
            params.append(self.parse_param())
            while self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                params.append(self.parse_param())
        return params

    def parse_param(self) -> Param:
        name = self.consume(TokenType.ID, "Expected parameter name").value
        self.consume(TokenType.AS, "Expected 'as'")
        param_type = self.parse_type()
        return Param(name, param_type)

    def parse_type(self) -> Type:
        tok = self.current_token
        if tok.type in {TokenType.INT, TokenType.VECTOR, TokenType.STR,
                        TokenType.MSTR, TokenType.BOOL, TokenType.NULL}:
            self.advance()
            if tok.type == TokenType.NULL:
                return Type("void")
            return Type(tok.type.name.lower())
        else:
            self.error(f"Expected type, got {tok.type.name}", tok.line, tok.column)

    def parse_block(self) -> List[Statement]:
        self.consume(TokenType.LCURLYEBR, "Expected '{'")
        stmts = self.parse_statement_list_until({TokenType.RCURLYEBR})
        self.consume(TokenType.RCURLYEBR, "Expected '}'")
        return stmts

    def parse_statement_list_until(self, stop_tokens: set) -> List[Statement]:
        stmts = []
        while self.current_token.type not in stop_tokens and self.current_token.type != TokenType.EOF:
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self) -> Statement:
        tok = self.current_token
        if tok.type == TokenType.ID and self.next_token.type == TokenType.DBL_COLON:
            return self.parse_var_decl()
        if tok.type == TokenType.FUNK:
            return self.parse_function_decl()
        if tok.type == TokenType.IF:
            return self.parse_if_stmt()
        if tok.type == TokenType.WHILE:
            return self.parse_while_stmt()
        if tok.type == TokenType.DO:
            return self.parse_dowhile_stmt()
        if tok.type == TokenType.FOR:
            return self.parse_for_stmt()
        if tok.type == TokenType.RETURN:
            return self.parse_return_stmt()
        if tok.type == TokenType.LCURLYEBR:
            return Block(self.parse_block())
        if tok.type == TokenType.BEGIN:
            stmts = self.parse_statement_list_until({TokenType.END})
            self.consume(TokenType.END, "Expected 'end'")
            return Block(stmts)
        if tok.type == TokenType.SEMI_COLON:
            self.advance()
            return ExprStmt(None)

        expr = self.parse_expression()
        self.consume(TokenType.SEMI_COLON, "Expected ';' after expression")
        return ExprStmt(expr)

    def parse_var_decl(self) -> VarDecl:
        id_token = self.current_token
        var_name = self.consume(TokenType.ID).value
        self.consume(TokenType.DBL_COLON, "Expected '::'")
        var_type = self.parse_type()
        init_expr = None
        if self.current_token.type == TokenType.EQ:
            self.advance()
            init_expr = self.parse_expression()
        self.consume(TokenType.SEMI_COLON, "Expected ';'")
        return VarDecl(var_name, var_type, init_expr, line=id_token.line, col=id_token.column)

    def parse_if_stmt(self) -> IfStmt:
        self.consume(TokenType.IF)
        self.consume_double_lsquare()
        condition = self.parse_expression()
        self.consume_double_rsquare()
        self.consume(TokenType.BEGIN, "Expected 'begin'")
        then_stmts = self.parse_statement_list_until({TokenType.ELSE, TokenType.ENDIF})
        else_stmts = None
        if self.current_token.type == TokenType.ELSE:
            self.advance()
            self.consume(TokenType.BEGIN, "Expected 'begin' after else")
            else_stmts = self.parse_statement_list_until({TokenType.ENDIF})
        self.consume(TokenType.ENDIF, "Expected 'endif'")
        return IfStmt(condition, then_stmts, else_stmts)

    def parse_while_stmt(self) -> WhileStmt:
        self.consume(TokenType.WHILE)
        self.consume_double_lsquare()
        condition = self.parse_expression()
        self.consume_double_rsquare()
        self.consume(TokenType.BEGIN, "Expected 'begin'")
        body = self.parse_statement_list_until({TokenType.ENDWHILE})
        self.consume(TokenType.ENDWHILE, "Expected 'endwhile'")
        return WhileStmt(condition, body)

    def parse_dowhile_stmt(self) -> DoWhileStmt:
        self.consume(TokenType.DO)
        self.consume(TokenType.BEGIN, "Expected 'begin'")
        body = self.parse_statement_list_until({TokenType.WHILE})
        self.consume(TokenType.WHILE, "Expected 'while'")
        self.consume_double_lsquare()
        condition = self.parse_expression()
        self.consume_double_rsquare()
        self.consume(TokenType.ENDWHILE, "Expected 'endwhile'")
        return DoWhileStmt(body, condition)

    def parse_for_stmt(self) -> ForStmt:
        self.consume(TokenType.FOR)
        self.consume(TokenType.LPAREN, "Expected '('")
        var_name = self.consume(TokenType.ID, "Expected loop variable").value
        self.consume(TokenType.EQ, "Expected '='")
        start_expr = self.parse_expression()
        self.consume(TokenType.TO, "Expected 'to'")
        end_expr = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')'")
        self.consume(TokenType.BEGIN, "Expected 'begin'")
        body = self.parse_statement_list_until({TokenType.ENDFOR})
        self.consume(TokenType.ENDFOR, "Expected 'endfor'")
        return ForStmt(var_name, start_expr, end_expr, body)

    def parse_return_stmt(self) -> ReturnStmt:
        self.consume(TokenType.RETURN)
        expr = None
        if self.current_token.type != TokenType.SEMI_COLON:
            expr = self.parse_expression()
        self.consume(TokenType.SEMI_COLON, "Expected ';'")
        return ReturnStmt(expr)

    # ---------------------------- Expression precedence ----------------------------
    def parse_expression(self) -> Expression:
        return self.parse_assignment()

    def parse_assignment(self) -> Expression:
        left = self.parse_ternary()
        if self.current_token.type == TokenType.EQ:
            self.advance()
            right = self.parse_assignment()
            return Assign(left, right)
        return left

    def parse_ternary(self) -> Expression:
        cond = self.parse_logical_or()
        if self.current_token.type == TokenType.QUESTION:
            self.advance()
            then_expr = self.parse_expression()   # May recursively contain another ternary expression
            self.consume(TokenType.COLON, "Expected ':'")
            else_expr = self.parse_ternary()      # right-associative
            return TernaryOp(cond, then_expr, else_expr)
        return cond

    def parse_logical_or(self) -> Expression:
        left = self.parse_logical_and()
        while self.current_token.type == TokenType.OR:
            op = self.current_token.value
            self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(left, op, right)
        return left

    def parse_logical_and(self) -> Expression:
        left = self.parse_equality()
        while self.current_token.type == TokenType.AND:
            op = self.current_token.value
            self.advance()
            right = self.parse_equality()
            left = BinaryOp(left, op, right)
        return left

    def parse_equality(self) -> Expression:
        left = self.parse_comparison()
        while self.current_token.type in (TokenType.EQUAL, TokenType.NOT_EQUAL):
            op = self.current_token.value
            self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op, right)
        return left

    def parse_comparison(self) -> Expression:
        left = self.parse_addition()
        while self.current_token.type in (TokenType.LESS_THAN, TokenType.GREATER_THAN,
                                          TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            op = self.current_token.value
            self.advance()
            right = self.parse_addition()
            left = BinaryOp(left, op, right)
        return left

    def parse_addition(self) -> Expression:
        left = self.parse_multiplication()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token.value
            self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(left, op, right)
        return left

    def parse_multiplication(self) -> Expression:
        left = self.parse_unary()
        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MOD):
            op = self.current_token.value
            self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op, right)
        return left

    def parse_unary(self) -> Expression:
        if self.current_token.type in (TokenType.PLUS, TokenType.MINUS, TokenType.NOT):
            op = self.current_token.value
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        return self.parse_primary()

    def parse_primary(self) -> Expression:
        expr = self.parse_atom()
        while self.current_token.type == TokenType.LSQUAREBR:
            self.advance()
            index = self.parse_expression()
            self.consume(TokenType.RSQUAREBR, "Expected ']'")
            expr = ArrayAccess(expr, index)
        return expr

    def parse_atom(self) -> Expression:
        tok = self.current_token
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Literal(tok.value, "number", line=tok.line, col=tok.column)
        if tok.type == TokenType.STRING:
            self.advance()
            return Literal(tok.value, "string", line=tok.line, col=tok.column)
        if tok.type == TokenType.MULTILINE_STRING:
            self.advance()
            return Literal(tok.value, "mstr", line=tok.line, col=tok.column)
        if tok.type == TokenType.BOOL:
            self.advance()
            val = (tok.value == 'true')
            return Literal(val, "bool", line=tok.line, col=tok.column)
        if tok.type == TokenType.NULL:
            self.advance()
            return Literal(None, "null", line=tok.line, col=tok.column)
        if tok.type == TokenType.LSQUAREBR:
            return self.parse_array_literal()
        if tok.type in {TokenType.ID, TokenType.LEN, TokenType.PRINT, TokenType.SCAN,
                        TokenType.LIST, TokenType.EXIT}:
            name = tok.value
            self.advance()
            if self.current_token.type == TokenType.LPAREN:
                self.advance()
                args = self.parse_argument_list()
                self.consume(TokenType.RPAREN, "Expected ')'")
                return Call(name, args, line=tok.line, col=tok.column)
            else:
                if tok.type != TokenType.ID:
                    self.error(f"Built-in '{name}' must be called with parentheses", tok.line, tok.column)
                return Variable(name, line=tok.line, col=tok.column)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')'")
            return expr
        self.error(f"Unexpected token {tok.type.name} in expression", tok.line, tok.column)

    def parse_argument_list(self) -> List[Expression]:
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args.append(self.parse_expression())
            while self.current_token.type == TokenType.COMMA:
                self.advance()
                args.append(self.parse_expression())
        return args

    def parse_array_literal(self) -> ArrayLiteral:
        start_line, start_col = self.current_token.line, self.current_token.column
        self.consume(TokenType.LSQUAREBR, "Expected '['")
        elements = []
        if self.current_token.type != TokenType.RSQUAREBR:
            elements.append(self.parse_expression())
            while self.current_token.type == TokenType.COMMA:
                self.advance()
                elements.append(self.parse_expression())
        self.consume(TokenType.RSQUAREBR, "Expected ']'")
        return ArrayLiteral(elements, line=start_line, col=start_col)
