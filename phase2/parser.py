# parser.py
from tokens import TokenType, Token
from lexer import Lexer
from teslang_ast import *

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        # دریافت اولین توکن به عنوان current_token
        self.current_token = self.lexer.get_next_token()
        # دریافت توکن بعدی برای lookahead
        self.next_token = self.lexer.get_next_token()

    def advance(self):
        """حرکت به توکن بعدی"""
        self.current_token = self.next_token
        self.next_token = self.lexer.get_next_token()

    def consume(self, expected_type: TokenType, error_msg: str = None):
        """بررسی می‌کند توکن جاری از نوع expected_type است، سپس advance می‌کند."""
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

    # ------------------------- قواعد گرامر -------------------------

    def parse_program(self) -> Program:
        """program = { function_decl } EOF"""
        functions = []
        while self.current_token.type != TokenType.EOF:
            functions.append(self.parse_function_decl())
        return Program(functions)

    # در متد parse_function_decl
    def parse_function_decl(self) -> FunctionDecl:
        funk_token = self.current_token  # برای گرفتن line/col
        self.consume(TokenType.FUNK, "Expected 'funk' for function declaration")
        self.consume(TokenType.LESS_THAN, "Expected '<' before return type")
        ret_type = self.parse_type()
        self.consume(TokenType.GREATER_THAN, "Expected '>' after return type")
        func_name_token = self.consume(TokenType.ID, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' for parameter list")
        params = self.parse_parameter_list()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        body = self.parse_block()
        return FunctionDecl(func_name_token.value, ret_type, params, body,
                            line=funk_token.line, col=funk_token.column)

    def parse_parameter_list(self) -> List[Param]:
        """parameter_list = [ param { ',' param } ]"""
        params = []
        if self.current_token.type != TokenType.RPAREN:
            params.append(self.parse_param())
            while self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                params.append(self.parse_param())
        return params

    def parse_param(self) -> Param:
        """param = ID AS type"""
        name = self.consume(TokenType.ID, "Expected parameter name").value
        self.consume(TokenType.AS, "Expected 'as' in parameter")
        param_type = self.parse_type()
        return Param(name, param_type)

    def parse_type(self) -> Type:
        """type = INT | VECTOR | STR | MSTR | BOOL | NULL"""
        tok = self.current_token
        if tok.type in {TokenType.INT, TokenType.VECTOR, TokenType.STR,
                        TokenType.MSTR, TokenType.BOOL, TokenType.NULL}:
            self.advance()
            # NULL در واقع نوع void را نشان می‌دهد (برای توابع بدون خروجی)
            if tok.type == TokenType.NULL:
                return Type("void")
            return Type(tok.type.name.lower())
        else:
            self.error(f"Expected type, got {tok.type.name}", tok.line, tok.column)

    def parse_block(self, use_braces=True) -> List[Statement]:
        """
        بلوک به دو شکل:
        - اگر use_braces == True:  { statement_list }
        - اگر use_braces == False: BEGIN statement_list (پایان توسط caller مدیریت می‌شود)
        """
        if use_braces:
            self.consume(TokenType.LCURLYEBR, "Expected '{' to start block")
            stmts = self.parse_statement_list_until({TokenType.RCURLYEBR})
            self.consume(TokenType.RCURLYEBR, "Expected '}' to end block")
        else:
            self.consume(TokenType.BEGIN, "Expected 'begin' to start block")
            # تا رسیدن به ELSE/ENDIF/ENDWHILE/ENDFOR را نمی‌خوانیم، بلکه به caller واگذار می‌شود.
            # بنابراین فقط BEGIN را مصرف می‌کنیم و هیچ statement ای برنمی‌گردانیم.
            # در عوض در متدهای if/while/for از parse_statements_until استفاده می‌کنیم.
            stmts = []  # اینجا قرار نیست statements خوانده شود
        return stmts

    def parse_statement_list_until(self, stop_tokens: set) -> List[Statement]:
        """خواندن لیست دستورات تا رسیدن به یکی از توکن‌های stop_tokens (بدون مصرف آن توکن)"""
        stmts = []
        while self.current_token.type not in stop_tokens and self.current_token.type != TokenType.EOF:
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self) -> Statement:
        """statement = var_decl | if_stmt | while_stmt | dowhile_stmt | for_stmt
                     | return_stmt | expr_stmt | block | ';' """
        tok = self.current_token

        # تعریف متغیر با ::
        if tok.type == TokenType.ID and self.next_token.type == TokenType.DBL_COLON:
            return self.parse_var_decl()

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
            return Block(self.parse_block(use_braces=True))
        if tok.type == TokenType.SEMI_COLON:
            self.advance()
            return ExprStmt(None)   # دستور خالی

        # در غیر این صورت، یک عبارت معمولی (انتساب، فراخوانی تابع، ...)
        expr = self.parse_expression()
        self.consume(TokenType.SEMI_COLON, "Expected ';' after expression")
        return ExprStmt(expr)

    def parse_var_decl(self) -> VarDecl:
        id_token = self.current_token
        var_name = self.consume(TokenType.ID).value
        self.consume(TokenType.DBL_COLON, "Expected '::' in variable declaration")
        var_type = self.parse_type()
        init_expr = None
        if self.current_token.type == TokenType.EQ:
            self.advance()
            init_expr = self.parse_expression()
        self.consume(TokenType.SEMI_COLON, "Expected ';' after variable declaration")
        return VarDecl(var_name, var_type, init_expr, line=id_token.line, col=id_token.column)
    
    def parse_if_stmt(self) -> IfStmt:
        """if_stmt = IF '(' expression ')' BEGIN statement_list [ ELSE statement_list ] ENDIF"""
        self.consume(TokenType.IF)
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        self.consume(TokenType.BEGIN, "Expected 'begin' after if condition")
        then_stmts = self.parse_statement_list_until({TokenType.ELSE, TokenType.ENDIF})
        else_stmts = None
        if self.current_token.type == TokenType.ELSE:
            self.advance()
            self.consume(TokenType.BEGIN, "Expected 'begin' after else")
            else_stmts = self.parse_statement_list_until({TokenType.ENDIF})
        self.consume(TokenType.ENDIF, "Expected 'endif' to close if statement")
        return IfStmt(condition, then_stmts, else_stmts)

    def parse_while_stmt(self) -> WhileStmt:
        """while_stmt = WHILE '(' expression ')' BEGIN statement_list ENDWHILE"""
        self.consume(TokenType.WHILE)
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        self.consume(TokenType.BEGIN, "Expected 'begin' after while condition")
        body = self.parse_statement_list_until({TokenType.ENDWHILE})
        self.consume(TokenType.ENDWHILE, "Expected 'endwhile' to close while loop")
        return WhileStmt(condition, body)

    def parse_dowhile_stmt(self) -> DoWhileStmt:
        """dowhile_stmt = DO BEGIN statement_list WHILE '(' expression ')' ENDWHILE"""
        self.consume(TokenType.DO)
        self.consume(TokenType.BEGIN, "Expected 'begin' after do")
        body = self.parse_statement_list_until({TokenType.WHILE})
        self.consume(TokenType.WHILE, "Expected 'while' after do body")
        self.consume(TokenType.LPAREN, "Expected '(' after while")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        self.consume(TokenType.ENDWHILE, "Expected 'endwhile' after do-while condition")
        return DoWhileStmt(body, condition)

    def parse_for_stmt(self) -> ForStmt:
        """for_stmt = FOR '(' ID EQ expression TO expression ')' BEGIN statement_list ENDFOR"""
        self.consume(TokenType.FOR)
        self.consume(TokenType.LPAREN, "Expected '(' after 'for'")
        var_name = self.consume(TokenType.ID, "Expected loop variable name").value
        self.consume(TokenType.EQ, "Expected '=' after variable")
        start_expr = self.parse_expression()
        self.consume(TokenType.TO, "Expected 'to' in for loop")
        end_expr = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after for range")
        self.consume(TokenType.BEGIN, "Expected 'begin' before for body")
        body = self.parse_statement_list_until({TokenType.ENDFOR})
        self.consume(TokenType.ENDFOR, "Expected 'endfor' to close for loop")
        return ForStmt(var_name, start_expr, end_expr, body)

    def parse_return_stmt(self) -> ReturnStmt:
        """return_stmt = RETURN [ expression ] ';'"""
        self.consume(TokenType.RETURN)
        expr = None
        if self.current_token.type != TokenType.SEMI_COLON:
            expr = self.parse_expression()
        self.consume(TokenType.SEMI_COLON, "Expected ';' after return statement")
        return ReturnStmt(expr)

    # ---------- تجزیه عبارات با اولویت عملگرها ----------
    def parse_expression(self) -> Expression:
        """expression = assignment"""
        return self.parse_assignment()

    def parse_assignment(self) -> Expression:
        """assignment = logical_or [ '=' assignment ]"""
        left = self.parse_logical_or()
        if self.current_token.type == TokenType.EQ:
            self.advance()
            right = self.parse_assignment()
            return Assign(left, right)
        return left

    def parse_logical_or(self) -> Expression:
        """logical_or = logical_and { '||' logical_and }"""
        left = self.parse_logical_and()
        while self.current_token.type == TokenType.OR:
            op = self.current_token.value
            self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(left, op, right)
        return left

    def parse_logical_and(self) -> Expression:
        """logical_and = equality { '&&' equality }"""
        left = self.parse_equality()
        while self.current_token.type == TokenType.AND:
            op = self.current_token.value
            self.advance()
            right = self.parse_equality()
            left = BinaryOp(left, op, right)
        return left

    def parse_equality(self) -> Expression:
        """equality = comparison { ('==' | '!=') comparison }"""
        left = self.parse_comparison()
        while self.current_token.type in (TokenType.EQUAL, TokenType.NOT_EQUAL):
            op = self.current_token.value
            self.advance()
            right = self.parse_comparison()
            left = BinaryOp(left, op, right)
        return left

    def parse_comparison(self) -> Expression:
        """comparison = addition { ('<' | '>' | '<=' | '>=') addition }"""
        left = self.parse_addition()
        while self.current_token.type in (TokenType.LESS_THAN, TokenType.GREATER_THAN,
                                          TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            op = self.current_token.value
            self.advance()
            right = self.parse_addition()
            left = BinaryOp(left, op, right)
        return left

    def parse_addition(self) -> Expression:
        """addition = multiplication { ('+' | '-') multiplication }"""
        left = self.parse_multiplication()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token.value
            self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(left, op, right)
        return left

    def parse_multiplication(self) -> Expression:
        """multiplication = unary { ('*' | '/' | '%') unary }"""
        left = self.parse_unary()
        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MOD):
            op = self.current_token.value
            self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op, right)
        return left

    def parse_unary(self) -> Expression:
        """unary = ('+' | '-' | '!') unary | primary"""
        if self.current_token.type in (TokenType.PLUS, TokenType.MINUS, TokenType.NOT):
            op = self.current_token.value
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        return self.parse_primary()

    def parse_primary(self) -> Expression:
        tok = self.current_token

        if tok.type == TokenType.NUMBER:
            self.advance()
            return Literal(int(tok.value), "number", line=tok.line, col=tok.column)
        if tok.type == TokenType.STRING:
            self.advance()
            return Literal(tok.value, "string", line=tok.line, col=tok.column)
        if tok.type == TokenType.BOOL:
            self.advance()
            val = (tok.value == 'true')
            return Literal(val, "bool", line=tok.line, col=tok.column)
        if tok.type == TokenType.NULL:
            self.advance()
            return Literal(None, "null", line=tok.line, col=tok.column)

        # توابع توکار و شناسه‌های معمولی
        if tok.type in {TokenType.ID, TokenType.LEN, TokenType.PRINT, TokenType.SCAN,
                        TokenType.LIST, TokenType.EXIT}:
            name = tok.value
            self.advance()
            # فراخوانی تابع
            if self.current_token.type == TokenType.LPAREN:
                self.advance()
                args = self.parse_argument_list()
                self.consume(TokenType.RPAREN, "Expected ')' after function arguments")
                return Call(name, args, line=tok.line, col=tok.column)
            # دسترسی به آرایه (فقط برای متغیرها)
            elif self.current_token.type == TokenType.LSQUAREBR:
                if tok.type != TokenType.ID:
                    self.error(f"Built-in function '{name}' cannot be used as array", tok.line, tok.column)
                self.advance()
                index = self.parse_expression()
                self.consume(TokenType.RSQUAREBR, "Expected ']' after array index")
                return ArrayAccess(Variable(name, line=tok.line, col=tok.column), index, line=tok.line, col=tok.column)
            else:
                # استفاده به عنوان متغیر ساده
                if tok.type != TokenType.ID:
                    self.error(f"Built-in function '{name}' must be called with parentheses", tok.line, tok.column)
                return Variable(name, line=tok.line, col=tok.column)

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')'")
            return expr

        self.error(f"Unexpected token {tok.type.name} in expression", tok.line, tok.column)
        
    def parse_argument_list(self) -> List[Expression]:
        """argument_list = [ expression { ',' expression } ]"""
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args.append(self.parse_expression())
            while self.current_token.type == TokenType.COMMA:
                self.advance()
                args.append(self.parse_expression())
        return args