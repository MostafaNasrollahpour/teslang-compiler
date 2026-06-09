# semantic_analyzer.py
from teslang_ast import *
from symbol_table import Symbol, Scope
from typing import Optional, List, Dict, Tuple

class SemanticAnalyzer:
    def __init__(self):
        self.current_scope = None
        self.current_function: Optional[FunctionDecl] = None
        self.current_function_has_return = False
        self.functions: Dict[str, Tuple[Type, List[Param]]] = {}   # name -> (return_type, params)
        self.errors = []

    def error(self, msg: str, node: ASTNode):
        self.errors.append(f"[Line {node.line}, Col {node.col}] {msg}")

    # ------------------------------------------------------------------
    # بازدید از گره‌ها
    # ------------------------------------------------------------------
    def visit(self, node: ASTNode):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        for attr in dir(node):
            if attr.startswith('_'):
                continue
            value = getattr(node, attr)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(value, ASTNode):
                self.visit(value)
        return None

    # ------------------------------------------------------------------
    # برنامه و توابع
    # ------------------------------------------------------------------
    def visit_Program(self, node: Program):
        # مرحله اول: ثبت توابع
        global_scope = Scope()
        self.current_scope = global_scope
        for func in node.functions:
            if func.name in self.functions:
                self.error(f"Function '{func.name}' already defined", func)
            else:
                self.functions[func.name] = (func.return_type, func.params)
            # همچنین در scope سراسری برای جلوگیری از تعریف متغیر با همین نام
            sym = Symbol(func.name, func.return_type, func.line, func.col, initialized=True)
            try:
                self.current_scope.define(func.name, sym)
            except Exception as e:
                self.error(f"Function '{func.name}' already defined in global scope", func)

        # مرحله دوم: بررسی بدنه توابع
        for func in node.functions:
            self.visit(func)

    def visit_FunctionDecl(self, node: FunctionDecl):
        # ورود به scope جدید
        self.current_scope = Scope(self.current_scope)
        self.current_function = node
        self.current_function_has_return = False

        # تعریف پارامترها
        for param in node.params:
            sym = Symbol(param.name, param.type, param.line, param.col, initialized=True)
            try:
                self.current_scope.define(param.name, sym)
            except Exception as e:
                self.error(f"Parameter '{param.name}' already defined", param)

        # بررسی بدنه
        for stmt in node.body:
            self.visit(stmt)

        # بررسی وجود return در تابع non-void
        if node.return_type.name != 'void' and not self.current_function_has_return:
            self.error(f"Function '{node.name}' must return a value of type '{node.return_type.name}'", node)

        # خروج از scope
        self.current_scope = self.current_scope.parent
        self.current_function = None

    # ------------------------------------------------------------------
    # دستورات
    # ------------------------------------------------------------------
    def visit_VarDecl(self, node: VarDecl):
        existing = self.current_scope.lookup_local(node.name)
        if existing:
            self.error(f"Variable '{node.name}' already defined in this scope", node)
            return
        sym = Symbol(node.name, node.var_type, node.line, node.col, initialized=(node.initializer is not None))
        self.current_scope.define(node.name, sym)
        if node.initializer:
            init_type = self.visit(node.initializer)
            if not self.is_compatible(node.var_type, init_type):
                self.error(f"Cannot initialize '{node.name}' of type '{node.var_type.name}' with value of type '{init_type.name}'", node.initializer)
            else:
                sym.initialized = True

    def visit_Assign(self, node: Assign):
        right_type = self.visit(node.value)
        if isinstance(node.target, Variable):
            sym = self.current_scope.lookup(node.target.name)
            if not sym:
                self.error(f"Variable '{node.target.name}' is not defined", node.target)
                return
            if not self.is_compatible(sym.type, right_type):
                self.error(f"Cannot assign value of type '{right_type.name}' to variable '{sym.type.name}'", node)
            else:
                sym.initialized = True
        elif isinstance(node.target, ArrayAccess):
            array_type = self.visit(node.target.array)
            if array_type.name != 'vector':
                self.error(f"Expected vector on left side, got '{array_type.name}'", node.target.array)
            else:
                if not self.is_compatible(Type('int'), right_type):
                    self.error(f"Array elements expect int, got '{right_type.name}'", node.value)
            index_type = self.visit(node.target.index)
            if index_type.name != 'int':
                self.error(f"Array index must be int, got '{index_type.name}'", node.target.index)
        else:
            self.error("Invalid left-hand side in assignment", node.target)
        return right_type

    def visit_IfStmt(self, node: IfStmt):
        cond_type = self.visit(node.condition)
        if cond_type.name != 'bool':
            self.error(f"If condition must be bool, got '{cond_type.name}'", node.condition)
        self.current_scope = Scope(self.current_scope)
        for stmt in node.then_body:
            self.visit(stmt)
        self.current_scope = self.current_scope.parent
        if node.else_body:
            self.current_scope = Scope(self.current_scope)
            for stmt in node.else_body:
                self.visit(stmt)
            self.current_scope = self.current_scope.parent

    def visit_WhileStmt(self, node: WhileStmt):
        cond_type = self.visit(node.condition)
        if cond_type.name != 'bool':
            self.error(f"While condition must be bool, got '{cond_type.name}'", node.condition)
        self.current_scope = Scope(self.current_scope)
        for stmt in node.body:
            self.visit(stmt)
        self.current_scope = self.current_scope.parent

    def visit_DoWhileStmt(self, node: DoWhileStmt):
        self.current_scope = Scope(self.current_scope)
        for stmt in node.body:
            self.visit(stmt)
        self.current_scope = self.current_scope.parent
        cond_type = self.visit(node.condition)
        if cond_type.name != 'bool':
            self.error(f"Do-while condition must be bool, got '{cond_type.name}'", node.condition)

    def visit_ForStmt(self, node: ForStmt):
        # scope جدید برای کل حلقه (متغیر حلقه و بدنه)
        self.current_scope = Scope(self.current_scope)
        # تعریف متغیر حلقه
        var_sym = Symbol(node.var_name, Type('int'), node.line, node.col, initialized=True)
        try:
            self.current_scope.define(node.var_name, var_sym)
        except Exception as e:
            self.error(f"Loop variable '{node.var_name}' already defined", node)

        start_type = self.visit(node.start)
        end_type = self.visit(node.end)
        if start_type.name != 'int':
            self.error(f"For start must be int, got '{start_type.name}'", node.start)
        if end_type.name != 'int':
            self.error(f"For end must be int, got '{end_type.name}'", node.end)

        for stmt in node.body:
            self.visit(stmt)

        self.current_scope = self.current_scope.parent

    def visit_ReturnStmt(self, node: ReturnStmt):
        if not self.current_function:
            self.error("Return statement outside function", node)
            return
        self.current_function_has_return = True
        expected = self.current_function.return_type
        if expected.name == 'void':
            if node.value is not None:
                self.error("Void function cannot return a value", node)
        else:
            if node.value is None:
                self.error(f"Function expected to return '{expected.name}' but no value provided", node)
            else:
                ret_type = self.visit(node.value)
                if not self.is_compatible(expected, ret_type):
                    self.error(f"Return type mismatch: expected '{expected.name}', got '{ret_type.name}'", node.value)

    def visit_ExprStmt(self, node: ExprStmt):
        if node.expr:
            self.visit(node.expr)

    def visit_Block(self, node: Block):
        self.current_scope = Scope(self.current_scope)
        for stmt in node.statements:
            self.visit(stmt)
        self.current_scope = self.current_scope.parent

    # ------------------------------------------------------------------
    # عبارات
    # ------------------------------------------------------------------
    def visit_Literal(self, node: Literal):
        mapping = {'number': 'int', 'string': 'str', 'bool': 'bool', 'null': 'null'}
        return Type(mapping[node.type_name])

    def visit_Variable(self, node: Variable):
        sym = self.current_scope.lookup(node.name)
        if not sym:
            self.error(f"Variable '{node.name}' is not defined", node)
            return Type('error')
        if not sym.initialized:
            self.error(f"Variable '{node.name}' is used before being assigned", node)
        return sym.type

    def visit_BinaryOp(self, node: BinaryOp):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        op = node.operator
        if op in ['+', '-', '*', '/', '%']:
            if left_type.name == 'int' and right_type.name == 'int':
                return Type('int')
            else:
                self.error(f"Arithmetic '{op}' requires int, got '{left_type.name}' and '{right_type.name}'", node)
                return Type('error')
        elif op in ['==', '!=', '<', '>', '<=', '>=']:
            if left_type.name == right_type.name:
                return Type('bool')
            else:
                self.error(f"Cannot compare '{left_type.name}' and '{right_type.name}' with '{op}'", node)
                return Type('error')
        elif op == '&&' or op == '||':
            if left_type.name == 'bool' and right_type.name == 'bool':
                return Type('bool')
            else:
                self.error(f"Logical '{op}' requires bool operands", node)
                return Type('error')
        else:
            self.error(f"Unknown binary operator '{op}'", node)
            return Type('error')

    def visit_UnaryOp(self, node: UnaryOp):
        operand_type = self.visit(node.operand)
        op = node.operator
        if op == '!':
            if operand_type.name == 'bool':
                return Type('bool')
            else:
                self.error(f"Logical not '!' requires bool, got '{operand_type.name}'", node)
                return Type('error')
        elif op == '+' or op == '-':
            if operand_type.name == 'int':
                return Type('int')
            else:
                self.error(f"Unary '{op}' requires int, got '{operand_type.name}'", node)
                return Type('error')
        else:
            self.error(f"Unknown unary operator '{op}'", node)
            return Type('error')

    def visit_Call(self, node: Call):
        builtins = {
            'print': {'args': [None], 'ret': Type('void'), 'accepts_any': True},   # هر نوعی را می‌پذیرد
            'scan': {'args': [], 'ret': Type('int')},
            'list': {'args': [Type('int')], 'ret': Type('vector')},
            'length': {'args': [Type('vector')], 'ret': Type('int')},
            'exit': {'args': [Type('int')], 'ret': Type('void')},
        }
        if node.func_name in builtins:
            spec = builtins[node.func_name]
            if len(node.arguments) != len(spec['args']):
                self.error(f"Function '{node.func_name}' expects {len(spec['args'])} arguments, got {len(node.arguments)}", node)
                return spec['ret']
            for i, arg in enumerate(node.arguments):
                arg_type = self.visit(arg)
                if not spec.get('accepts_any'):
                    expected = spec['args'][i]
                    if not self.is_compatible(expected, arg_type):
                        self.error(f"Argument {i+1} of '{node.func_name}' expected '{expected.name}', got '{arg_type.name}'", arg)
            return spec['ret']
        else:
            # تابع کاربر
            if node.func_name not in self.functions:
                self.error(f"Function '{node.func_name}' is not defined", node)
                return Type('error')
            ret_type, params = self.functions[node.func_name]
            if len(node.arguments) != len(params):
                self.error(f"Function '{node.func_name}' expects {len(params)} arguments, got {len(node.arguments)}", node)
                return ret_type
            for i, (arg, param) in enumerate(zip(node.arguments, params)):
                arg_type = self.visit(arg)
                if not self.is_compatible(param.type, arg_type):
                    self.error(f"Argument {i+1} of '{node.func_name}' expected '{param.type.name}', got '{arg_type.name}'", arg)
            return ret_type

    def visit_ArrayAccess(self, node: ArrayAccess):
        array_type = self.visit(node.array)
        if array_type.name != 'vector':
            self.error(f"Expected vector, got '{array_type.name}'", node.array)
        index_type = self.visit(node.index)
        if index_type.name != 'int':
            self.error(f"Array index must be int, got '{index_type.name}'", node.index)
        return Type('int')

    def visit_ArrayLiteral(self, node: ArrayLiteral):
        # همه عناصر باید int باشند (طبق مشخصات TesLang)
        for elem in node.elements:
            elem_type = self.visit(elem)
            if elem_type.name != 'int':
                self.error(f"Array literal elements must be int, got '{elem_type.name}'", elem)
        return Type('vector')

    def visit_TernaryOp(self, node: TernaryOp):
        cond_type = self.visit(node.cond)
        if cond_type.name != 'bool':
            self.error(f"Ternary condition must be bool, got '{cond_type.name}'", node.cond)
        then_type = self.visit(node.then_expr)
        else_type = self.visit(node.else_expr)
        if not self.is_compatible(then_type, else_type):
            self.error(f"Ternary branches have incompatible types: '{then_type.name}' and '{else_type.name}'", node)
        return then_type

    # ------------------------------------------------------------------
    # توابع کمکی
    # ------------------------------------------------------------------
    def is_compatible(self, expected: Type, actual: Type) -> bool:
        if expected.name == 'error' or actual.name == 'error':
            return True
        return expected.name == actual.name