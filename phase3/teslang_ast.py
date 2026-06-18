# teslang_ast.py
from typing import List, Optional, Any

class ASTNode:
    def __init__(self, line: int = 0, col: int = 0):
        self.line = line
        self.col = col

class Type(ASTNode):
    def __init__(self, name: str, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.name = name   # 'int', 'vector', 'str', 'mstr', 'bool', 'void'

    def __repr__(self):
        return self.name

class Program(ASTNode):
    def __init__(self, functions: List['FunctionDecl'], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.functions = functions

    def __repr__(self):
        return f"Program({self.functions})"

class Param(ASTNode):
    def __init__(self, name: str, type: Type, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.name = name
        self.type = type

    def __repr__(self):
        return f"Param({self.name}: {self.type})"

# Statement must be defined before FunctionDecl
class Statement(ASTNode):
    pass

class FunctionDecl(Statement):   # Now Statement is defined
    def __init__(self, name: str, return_type: Type, params: List[Param], body: List[Statement], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.name = name
        self.return_type = return_type
        self.params = params
        self.body = body

    def __repr__(self):
        return f"FunctionDecl({self.name}, {self.return_type}, {self.params}, {self.body})"

class Block(Statement):
    def __init__(self, statements: List[Statement], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.statements = statements

    def __repr__(self):
        return f"Block({self.statements})"

class VarDecl(Statement):
    def __init__(self, name: str, var_type: Type, initializer: Optional['Expression'], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.name = name
        self.var_type = var_type
        self.initializer = initializer

    def __repr__(self):
        return f"VarDecl({self.name}: {self.var_type} = {self.initializer})"

class IfStmt(Statement):
    def __init__(self, condition: 'Expression', then_body: List[Statement], else_body: Optional[List[Statement]], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

    def __repr__(self):
        return f"IfStmt({self.condition}, {self.then_body}, {self.else_body})"

class WhileStmt(Statement):
    def __init__(self, condition: 'Expression', body: List[Statement], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f"WhileStmt({self.condition}, {self.body})"

class DoWhileStmt(Statement):
    def __init__(self, body: List[Statement], condition: 'Expression', line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.body = body
        self.condition = condition

    def __repr__(self):
        return f"DoWhileStmt({self.body}, {self.condition})"

class ForStmt(Statement):
    def __init__(self, var_name: str, start: 'Expression', end: 'Expression', body: List[Statement], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.var_name = var_name
        self.start = start
        self.end = end
        self.body = body

    def __repr__(self):
        return f"ForStmt({self.var_name} from {self.start} to {self.end}, {self.body})"

class ReturnStmt(Statement):
    def __init__(self, value: Optional['Expression'], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.value = value

    def __repr__(self):
        return f"ReturnStmt({self.value})"

class ExprStmt(Statement):
    def __init__(self, expr: Optional['Expression'], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.expr = expr

    def __repr__(self):
        return f"ExprStmt({self.expr})"

class Expression(ASTNode):
    pass

class Literal(Expression):
    def __init__(self, value: Any, type_name: str, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.value = value
        self.type_name = type_name   # 'number', 'string', 'bool', 'null'

    def __repr__(self):
        return f"Literal({self.value})"

class Variable(Expression):
    def __init__(self, name: str, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.name = name

    def __repr__(self):
        return f"Var({self.name})"

class BinaryOp(Expression):
    def __init__(self, left: Expression, operator: str, right: Expression, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left} {self.operator} {self.right})"

class UnaryOp(Expression):
    def __init__(self, operator: str, operand: Expression, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.operator} {self.operand})"

class Assign(Expression):
    def __init__(self, target: Expression, value: Expression, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.target = target
        self.value = value

    def __repr__(self):
        return f"Assign({self.target} = {self.value})"

class Call(Expression):
    def __init__(self, func_name: str, arguments: List[Expression], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.func_name = func_name
        self.arguments = arguments

    def __repr__(self):
        return f"Call({self.func_name}({self.arguments}))"

class ArrayAccess(Expression):
    def __init__(self, array: Expression, index: Expression, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.array = array
        self.index = index

    def __repr__(self):
        return f"ArrayAccess({self.array}[{self.index}])"

class TernaryOp(Expression):
    def __init__(self, cond: Expression, then_expr: Expression, else_expr: Expression, line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr

    def __repr__(self):
        return f"TernaryOp({self.cond} ? {self.then_expr} : {self.else_expr})"

class ArrayLiteral(Expression):
    def __init__(self, elements: List[Expression], line: int = 0, col: int = 0):
        super().__init__(line, col)
        self.elements = elements

    def __repr__(self):
        return f"ArrayLiteral({self.elements})"