# symbol_table.py
from teslang_ast import Type,Param
from typing import List, Optional

class Symbol:
    def __init__(self, name: str, sym_type: Type, line: int, col: int, 
                 initialized: bool = False,
                 is_function: bool = False,
                 params: Optional[List['Param']] = None):
        self.name = name
        self.type = sym_type          # برای متغیر: نوع داده، برای تابع: نوع بازگشتی
        self.line = line
        self.col = col
        self.initialized = initialized
        self.is_function = is_function
        self.params = params if params is not None else []

    def __repr__(self):
        if self.is_function:
            return f"FuncSymbol({self.name}: {self.type} params={self.params})"
        return f"Symbol({self.name}: {self.type}, initialized={self.initialized})"

class Scope:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name: str, symbol: Symbol):
        if name in self.symbols:
            raise Exception(f"Symbol '{name}' already defined in this scope")
        self.symbols[name] = symbol

    def lookup(self, name: str):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str):
        return self.symbols.get(name)