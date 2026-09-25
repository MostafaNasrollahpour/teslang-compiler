# code_generator.py
from teslang_ast import *
from typing import List, Dict, Optional

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.label_counter = 0
        self.current_function = None
        self.var_reg = {}
        self.next_reg = 3
        self.temp_pool = ['r2', 'r12', 'r13', 'r14', 'r15']
        self.free_temps = self.temp_pool.copy()
        self.used_temps = []

    def new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, ins: str):
        self.code.append(ins)

    def get_code(self) -> str:
        return "\n".join(self.code)

    def alloc_var_reg(self, name: str) -> str:
        if name not in self.var_reg:
            if self.next_reg > 15:
                raise RuntimeError("No register for variable")
            reg = f"r{self.next_reg}"
            self.next_reg += 1
            self.var_reg[name] = reg
        return self.var_reg[name]

    def alloc_temp(self) -> str:
        if not self.free_temps:
            raise RuntimeError("No temp register available")
        reg = self.free_temps.pop(0)
        self.used_temps.append(reg)
        return reg

    def free_temp(self, reg: str):
        if reg in self.used_temps:
            self.used_temps.remove(reg)
            self.free_temps.append(reg)

    def reset_temps(self):
        for reg in self.used_temps:
            self.free_temps.append(reg)
        self.used_temps = []
        self.free_temps = sorted(self.free_temps, reverse=True)

    def visit(self, node: ASTNode):
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            raise NotImplementedError(f"visit_{type(node).__name__}")
        return method(node)

    def visit_Program(self, node: Program):
        for f in node.functions:
            self.visit(f)

    def visit_FunctionDecl(self, node: FunctionDecl):
        self.current_function = node
        self.var_reg = {}
        self.next_reg = 3
        self.reset_temps()
        self.emit(f"proc {node.name}")
        for i, p in enumerate(node.params, start=1):
            reg = self.alloc_var_reg(p.name)
            self.emit(f"mov {reg}, r{i}")
        for stmt in node.body:
            self.visit(stmt)
        # Emit a single return at the end of the function
        self.emit("ret")
        self.emit("")
        self.current_function = None

    def visit_VarDecl(self, node: VarDecl):
        reg = self.alloc_var_reg(node.name)
        if node.initializer:
            val_reg = self.visit(node.initializer)
            self.emit(f"mov {reg}, {val_reg}")
            self.free_temp(val_reg)

    def visit_Assign(self, node: Assign):
        if isinstance(node.target, Variable):
            reg_left = self.var_reg.get(node.target.name)
            if not reg_left:
                raise RuntimeError(f"Unknown var {node.target.name}")
            reg_right = self.visit(node.value)
            self.emit(f"mov {reg_left}, {reg_right}")
            self.free_temp(reg_right)
            return reg_right
        elif isinstance(node.target, ArrayAccess):
            val_reg = self.visit(node.value)
            base_reg = self.visit(node.target.array)
            index_reg = self.visit(node.target.index)
            addr_reg = self.alloc_temp()
            self.emit(f"mul {addr_reg}, {index_reg}, 4")
            self.emit(f"add {addr_reg}, {base_reg}, {addr_reg}")
            self.emit(f"store {val_reg}, {addr_reg}")
            self.free_temp(val_reg)
            self.free_temp(base_reg)
            self.free_temp(index_reg)
            self.free_temp(addr_reg)
            return val_reg
        return None

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        res = self.alloc_temp()
        op = node.operator
        if op in ('+', '-', '*', '/', '%'):
            m = {'+':'add','-':'sub','*':'mul','/':'div','%':'mod'}
            self.emit(f"{m[op]} {res}, {left}, {right}")
        elif op in ('<', '>', '<=', '>=', '==', '!='):
            self.emit(f"cmp {left}, {right}")
            l_true = self.new_label()
            l_end = self.new_label()
            self.emit(f"mov {res}, 0")
            cond_map = {'<':'jlt','>':'jgt','<=':'jle','>=':'jge','==':'je','!=':'jne'}
            self.emit(f"{cond_map[op]} {l_true}")
            self.emit(f"jmp {l_end}")
            self.emit(f"{l_true}:")
            self.emit(f"mov {res}, 1")
            self.emit(f"{l_end}:")
        else:
            raise NotImplementedError(f"Binary op {op}")
        self.free_temp(left)
        self.free_temp(right)
        return res

    def visit_Literal(self, node: Literal) -> str:
        reg = self.alloc_temp()
        if node.type_name == 'number':
            self.emit(f"mov {reg}, {node.value}")
        elif node.type_name == 'bool':
            self.emit(f"mov {reg}, {1 if node.value else 0}")
        else:
            self.emit(f"mov {reg}, 0")
        return reg

    def visit_Variable(self, node: Variable) -> str:
        reg = self.var_reg.get(node.name)
        if not reg:
            raise RuntimeError(f"Undefined var {node.name}")
        temp = self.alloc_temp()
        self.emit(f"mov {temp}, {reg}")
        return temp

    def visit_ArrayAccess(self, node: ArrayAccess) -> str:
        base_reg = self.visit(node.array)
        index_reg = self.visit(node.index)
        addr_reg = self.alloc_temp()
        self.emit(f"mul {addr_reg}, {index_reg}, 4")
        self.emit(f"add {addr_reg}, {base_reg}, {addr_reg}")
        val_reg = self.alloc_temp()
        self.emit(f"load {val_reg}, {addr_reg}")
        self.free_temp(base_reg)
        self.free_temp(index_reg)
        self.free_temp(addr_reg)
        return val_reg

    def visit_ArrayLiteral(self, node: ArrayLiteral) -> str:
        raise NotImplementedError("Array literal not supported")

    def visit_Call(self, node: Call) -> str:
        if node.func_name == 'print':
            # Integer output only; string output is not supported
            arg = self.visit(node.arguments[0])
            self.emit(f"call iput, {arg}")
            self.free_temp(arg)
            dummy = self.alloc_temp()
            self.emit(f"mov {dummy}, 0")
            return dummy
        elif node.func_name == 'scan':
            reg = self.alloc_temp()
            self.emit(f"call iget, {reg}")
            return reg
        elif node.func_name == 'list':
            size_reg = self.visit(node.arguments[0])
            base_reg = self.alloc_temp()
            self.emit(f"mov {base_reg}, 1000")  # placeholder
            self.free_temp(size_reg)
            return base_reg
        elif node.func_name == 'length':
            arr_reg = self.visit(node.arguments[0])
            len_reg = self.alloc_temp()
            self.emit(f"mov {len_reg}, 0")  # placeholder
            self.free_temp(arr_reg)
            return len_reg
        elif node.func_name == 'exit':
            arg = self.visit(node.arguments[0])
            self.emit(f"exit {arg}")  # placeholder
            self.free_temp(arg)
            dummy = self.alloc_temp()
            self.emit(f"mov {dummy}, 0")
            return dummy
        else:
            # User-defined function call
            dest = self.alloc_temp()
            arg_regs = [self.visit(a) for a in node.arguments]
            args_str = ", ".join([dest] + arg_regs)
            self.emit(f"call {node.func_name}, {args_str}")
            for r in arg_regs:
                self.free_temp(r)
            return dest

    def visit_IfStmt(self, node: IfStmt):
        cond = self.visit(node.condition)
        self.emit(f"cmp {cond}, 0")
        l_else = self.new_label()
        l_end = self.new_label()
        self.emit(f"jz {l_else}")
        for s in node.then_body:
            self.visit(s)
        self.emit(f"jmp {l_end}")
        self.emit(f"{l_else}:")
        if node.else_body:
            for s in node.else_body:
                self.visit(s)
        self.emit(f"{l_end}:")
        self.free_temp(cond)

    def visit_WhileStmt(self, node: WhileStmt):
        l_start = self.new_label()
        l_end = self.new_label()
        self.emit(f"{l_start}:")
        cond = self.visit(node.condition)
        self.emit(f"cmp {cond}, 0")
        self.emit(f"jz {l_end}")
        self.free_temp(cond)
        for s in node.body:
            self.visit(s)
        self.emit(f"jmp {l_start}")
        self.emit(f"{l_end}:")

    def visit_ForStmt(self, node: ForStmt):
        reg_var = self.alloc_var_reg(node.var_name)
        start_reg = self.visit(node.start)
        self.emit(f"mov {reg_var}, {start_reg}")
        self.free_temp(start_reg)
        l_start = self.new_label()
        l_end = self.new_label()
        self.emit(f"{l_start}:")
        end_reg = self.visit(node.end)
        self.emit(f"cmp {reg_var}, {end_reg}")
        self.emit(f"jgt {l_end}")
        self.free_temp(end_reg)
        for s in node.body:
            self.visit(s)
        self.emit(f"add {reg_var}, {reg_var}, 1")
        self.emit(f"jmp {l_start}")
        self.emit(f"{l_end}:")

    def visit_ReturnStmt(self, node: ReturnStmt):
        if node.value:
            val = self.visit(node.value)
            self.emit(f"mov r0, {val}")
            self.free_temp(val)
        # Return is emitted at the end of the function

    def visit_ExprStmt(self, node: ExprStmt):
        if node.expr:
            res = self.visit(node.expr)
            if res:
                self.free_temp(res)

    def visit_Block(self, node: Block):
        for s in node.statements:
            self.visit(s)