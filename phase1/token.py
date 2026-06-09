from enum import Enum, auto

class TokenType(Enum):
    # Keywords & built‑ins
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
    # Built‑in functions (from the spec)
    SCAN = auto()
    PRINT = auto()
    LIST = auto()
    LEN = auto()          # "length" is shown as LEN in sample output
    EXIT = auto()

    # Operators & punctuation (names match the sample output)
    LESS_THAN = auto()    # <
    GREATER_THAN = auto() # >
    LESS_EQUAL = auto()   # <=
    GREATER_EQUAL = auto()# >=
    EQUAL = auto()        # ==
    NOT_EQUAL = auto()    # !=
    EQ = auto()           # =   (assignment)
    PLUS = auto()         # +
    MINUS = auto()        # -
    MULTIPLY = auto()     # *
    DIVIDE = auto()       # /
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACE = auto()       # {   -> PDF uses LCURLYEBR (we keep LBRACE)
    RBRACE = auto()       # }   -> RCURLYEBR
    LSQUARE = auto()      # [   -> PDF uses LSQUAREBR
    RSQUARE = auto()      # ]   -> RSQUAREBR
    SEMICOLON = auto()    # ;
    COLON = auto()        # :
    DBL_COLON = auto()    # ::
    COMMA = auto()        # ,
    QUESTION = auto()     # ?
    AND = auto()          # &&
    OR = auto()           # ||
    NOT = auto()          # !
    ARROW = auto()   # =>
    MOD = auto()   # %

    # Literals & identifiers
    ID = auto()           # identifier (instead of IDENTIFIER)
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