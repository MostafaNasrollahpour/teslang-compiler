from enum import Enum, auto

class TokenType(Enum):
    # Keywords & built-ins
    FUNK = auto()
    INT = auto()
    VECTOR = auto()
    STR = auto()
    MSTR = auto()
    BOOL = auto()
    NULL = auto()
    AS = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    ENDIF = auto()
    WHILE = auto()
    ENDWHILE = auto()
    DO = auto()
    FOR = auto()
    TO = auto()
    BEGIN = auto()
    ENDFOR = auto()
    SCAN = auto()
    PRINT = auto()
    LIST = auto()
    LEN = auto()
    EXIT = auto()

    # Operators & punctuation
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    EQ = auto()
    ARROW = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MOD = auto()
    LPAREN = auto()
    RPAREN = auto()
    LCURLYEBR = auto()
    RCURLYEBR = auto()
    LSQUAREBR = auto()
    RSQUAREBR = auto()
    SEMI_COLON = auto()
    COLON = auto()
    DBL_COLON = auto()
    COMMA = auto()
    QUESTION = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Literals & identifiers
    ID = auto()
    NUMBER = auto()
    STRING = auto()
    MULTILINE_STRING = auto()
    EOF = auto()

class Token:
    def __init__(self, type: TokenType, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"{self.line} {self.column} {self.type.name} {self.value}"