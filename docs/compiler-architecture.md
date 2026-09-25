# TesLang Compiler Architecture

## 1. Overview

TesLang Compiler is implemented as a traditional multi-stage compiler pipeline.

The major stages are:

```text
Source Code
    ↓
Lexer
    ↓
Token Stream
    ↓
Recursive-Descent Parser
    ↓
Abstract Syntax Tree
    ↓
Semantic Analyzer
    ↓
Code Generator
    ↓
TSVM Intermediate Representation
```

The frontend recognizes and validates a larger language surface than the currently verified backend subset.

This separation is intentional in the current repository state: frontend implementation and semantic rules remain visible even where backend lowering has not yet been completed.

## 2. Repository Components

The compiler implementation is divided into the following modules:

| File | Responsibility |
|---|---|
| `main.py` | Compiler entry point and pipeline orchestration |
| `lexer.py` | Source text tokenization |
| `tokens.py` | Token type and token definitions |
| `parser.py` | Recursive-descent parser |
| `teslang_ast.py` | Abstract syntax tree node definitions |
| `symbol_table.py` | Symbols and lexical scopes |
| `semantic_analyzer.py` | Name resolution, type checking, and semantic validation |
| `code_generator.py` | TSVM-targeted IR generation |

## 3. Compiler Entry Point

The compiler is started through:

```text
compiler/main.py
```

The entry point reads TesLang source code from standard input:

```text
stdin
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Semantic Analyzer
  ↓
Code Generator
  ↓
output.tsl
```

If parsing fails, a syntax error is written to standard error and the compiler exits with a non-zero status.

If semantic errors are found, all collected semantic diagnostics are printed to standard error and code generation is skipped.

When compilation succeeds, generated TSVM IR is written to:

```text
output.tsl
```

## 4. Lexer

The lexer is implemented in:

```text
compiler/lexer.py
```

It maintains:

- the current source position,
- line number,
- column number,
- total input length.

Each emitted token stores its original line and column.

### 4.1 Token Categories

The lexer recognizes:

- identifiers
- keywords
- numeric literals
- string literals
- multiline strings
- boolean literals
- operators
- punctuation
- comments

### 4.2 Source Position Tracking

Every call to the lexer advancement routine updates line and column information.

Newline characters increment the line number and reset the column.

This information is carried into tokens and later used for diagnostics.

### 4.3 Nested Comments

Comments use:

```text
</
```

and:

```text
/>
```

The lexer maintains a comment nesting depth.

A nested opening marker increments the depth, and a closing marker decrements it.

Tokenization resumes when the nesting depth reaches zero.

### 4.4 String Handling

Single-line strings support both single and double quote delimiters.

Multiline strings use triple double quotes.

The lexer recognizes `\n` and `\t` escape sequences.

## 5. Token Model

Token definitions live in:

```text
compiler/tokens.py
```

Each token contains:

```text
type
value
line
column
```

`TokenType` is represented as a Python enumeration.

The token set contains separate entries for:

- language keywords,
- built-ins,
- operators,
- punctuation,
- literals,
- identifiers,
- end-of-file.

## 6. Parser

The parser is implemented in:

```text
compiler/parser.py
```

It is a handwritten recursive-descent parser.

No parser generator is used.

The parser keeps two lexer tokens available:

```text
current_token
next_token
```

The additional lookahead is used, among other things, to distinguish variable declarations from ordinary expressions.

For example:

```text
x :: int = 10;
```

is recognized because an identifier followed by `::` starts a variable declaration.

## 7. Recursive-Descent Structure

Major parser methods correspond directly to language constructs.

Examples include:

```text
parse_program
parse_function_decl
parse_statement
parse_var_decl
parse_if_stmt
parse_while_stmt
parse_dowhile_stmt
parse_for_stmt
parse_return_stmt
```

Expression parsing is divided into precedence levels rather than being handled by one monolithic routine.

## 8. Expression Precedence

Expression parsing proceeds through the following levels:

```text
assignment
    ↓
ternary
    ↓
logical OR
    ↓
logical AND
    ↓
equality
    ↓
comparison
    ↓
addition
    ↓
multiplication
    ↓
unary
    ↓
primary
    ↓
atom
```

Assignment and ternary expressions are right-associative.

Arithmetic and logical binary levels are parsed left-associatively.

Array indexing is applied as a postfix operation after primary expressions.

## 9. Abstract Syntax Tree

AST definitions live in:

```text
compiler/teslang_ast.py
```

All AST objects derive from:

```text
ASTNode
```

AST nodes preserve source line and column information where available.

### 9.1 Program-Level Nodes

```text
Program
FunctionDecl
Param
```

### 9.2 Statement Nodes

```text
Statement
Block
VarDecl
IfStmt
WhileStmt
DoWhileStmt
ForStmt
ReturnStmt
ExprStmt
```

### 9.3 Expression Nodes

```text
Expression
Literal
Variable
BinaryOp
UnaryOp
Assign
Call
ArrayAccess
TernaryOp
ArrayLiteral
```

The AST acts as the boundary between parsing and later compiler passes.

The semantic analyzer and code generator both operate on AST nodes rather than raw tokens.

## 10. Symbol Table and Scope Model

Symbol management is implemented in:

```text
compiler/symbol_table.py
```

A symbol records:

- name
- type
- declaration position
- initialization status
- whether it represents a function
- function parameters

A scope contains:

```text
symbols
parent
```

Name resolution first searches the current scope.

If a name is not found, lookup recursively continues through parent scopes.

## 11. Semantic Analysis

Semantic analysis is implemented in:

```text
compiler/semantic_analyzer.py
```

The analyzer uses a visitor-style dispatch model:

```text
visit_<NodeType>
```

### 11.1 Global Function Registration

Before function bodies are analyzed, top-level function symbols are registered in the global scope.

This permits one function to reference another function declared later in the source file.

### 11.2 Function Scope

Entering a function creates a new scope.

Function parameters are inserted into that scope as initialized symbols.

Nested function symbols are pre-registered before the containing function body is analyzed.

The current analyzer does not fully preserve function context across nested function visits, so nested functions are classified as incomplete rather than fully supported.

### 11.3 Variable Validation

For variable declarations, the analyzer checks:

- duplicate declarations,
- initializer type compatibility.

For variable use, it checks:

- whether the variable exists,
- whether the symbol is actually a variable rather than a function,
- whether the variable has been initialized.

### 11.4 Assignment Validation

Assignments are validated against their target type.

Valid semantic assignment targets are:

- variables,
- vector elements.

Assignment to a function symbol is rejected.

### 11.5 Type Checking

Arithmetic operators validate integer operands.

String-like addition is also recognized by the frontend.

Comparison expressions produce boolean results.

Logical operations require boolean operands.

Unary arithmetic requires integers.

Logical negation requires a boolean operand.

### 11.6 Function Calls

Built-in and user-defined calls are checked for:

- argument count,
- argument types,
- target function existence.

User-defined function return types are propagated as the type of the call expression.

### 11.7 Return Validation

The analyzer checks:

- return statements outside functions,
- values returned from void functions,
- missing values from non-void functions,
- incompatible return types.

For non-void functions, the analyzer performs a simple terminal-path return analysis.

A direct `return` is considered terminating.

A block terminates when its statement list terminates.

An `if` statement terminates only when both branches terminate.

Loops are not assumed to guarantee a return.

### 11.8 Program Entry Point

The analyzer requires a `main` function with the signature:

```text
funk <null> main()
```

Internally, its return type is represented as `void`.

## 12. Semantic Diagnostics

Semantic errors are collected rather than immediately aborting at the first error.

Diagnostics include source line and column information:

```text
[Line X, Col Y] message
```

After semantic analysis, code generation begins only if no semantic errors have been collected.

## 13. Code Generator

The backend is implemented in:

```text
compiler/code_generator.py
```

Like the semantic analyzer, it dispatches on AST node type:

```text
visit_<NodeType>
```

Generated instructions are collected in memory and written to `output.tsl` after traversal.

## 14. Register Model

Each generated function receives a fresh local register-allocation state.

Variables are assigned virtual registers beginning at:

```text
r3
```

Temporary expressions use a small temporary-register pool:

```text
r2
r12
r13
r14
r15
```

Temporary registers are allocated during expression evaluation and returned to the pool after use.

The current implementation is intentionally simple and does not perform spilling or advanced register allocation.

## 15. Function Lowering

A generated function starts with:

```text
proc function_name
```

Function parameters are copied from incoming TSVM registers into locally allocated variable registers.

The compiler reserves the TSVM return register convention around `r0`.

For the verified straight-line subset, return values are moved into `r0` before the final `ret`.

Example:

```text
proc sum
mov r3, r1
mov r4, r2
...
mov r0, r14
ret
```

## 16. TSVM Calling Convention

TSVM procedures use private virtual-register sets.

A `call` instruction copies call operands into the callee's registers.

The return value is read from `r0` and may be written into the destination operand of the call.

The compiler uses this behavior to generate user-defined calls such as:

```text
call sum, r2, r15, r14
```

where the destination register also participates in TSVM's call convention.

## 17. External Runtime

TSVM is not implemented inside this repository.

The upstream runtime is available at:

```text
https://github.com/aligrudi/tsvm
```

The repository intentionally ignores a local `tsvm/` directory so the runtime can be cloned and built next to the compiler without mixing external source code into the compiler repository.

## 18. TSVM Instruction Set

The TSVM runtime supports instructions including:

```text
mov
add
sub
mul
div
mod
cmp<
cmp>
cmp==
cmp<=
cmp>=
ld
st
ret
call
jmp
jz
jnz
```

It also provides runtime procedures including:

```text
iget
iput
mem
rel
```

## 19. Backend Support Matrix

The compiler frontend is currently more complete than its backend.

| Language Construct | Lexer / Parser | Semantic Analysis | Code Generation | End-to-End Status |
|---|---|---|---|---|
| Integer literals | Yes | Yes | Yes | Verified |
| Integer variables | Yes | Yes | Yes | Verified |
| Variable declarations | Yes | Yes | Yes | Verified |
| Variable assignment | Yes | Yes | Yes | Verified |
| Integer arithmetic | Yes | Yes | Yes | Implemented |
| Straight-line function calls | Yes | Yes | Yes | Verified |
| Terminal return values | Yes | Yes | Yes | Verified |
| Integer `print` | Yes | Yes | Yes | Verified |
| `scan()` | Yes | Yes | Implemented | Not covered by smoke test |
| Boolean literals | Yes | Yes | Basic lowering | Limited |
| Comparisons | Yes | Yes | Partial | Not verified |
| `if` | Yes | Yes | Partial | Not verified |
| `while` | Yes | Yes | Partial | Not verified |
| `for` | Yes | Yes | Partial | Not verified |
| `do-while` | Yes | Yes | No visitor | Not supported by backend |
| Unary expressions | Yes | Yes | No visitor | Not supported by backend |
| Logical `&&` / `||` | Yes | Yes | Not lowered | Not supported by backend |
| Ternary expressions | Yes | Yes | No visitor | Not supported by backend |
| Strings | Yes | Yes | No string representation | Not supported by backend |
| Multiline strings | Yes | Yes | No string representation | Not supported by backend |
| Vector literals | Yes | Yes | Not implemented | Not supported by backend |
| Vector indexing | Yes | Yes | Partial | Not verified |
| `list` | Yes | Yes | Placeholder | Not verified |
| `length` | Yes | Yes | Placeholder | Not verified |
| `exit` | Yes | Yes | Placeholder | Not verified |
| Nested functions | Yes | Incomplete | Partial / unverified | Not supported end-to-end |

## 20. Current Backend Boundaries

Several code-generation paths remain intentionally visible even though they are not part of the verified backend subset.

Examples include control-flow lowering, vector memory operations, and some built-ins.

Some of these paths currently contain placeholder logic or instruction forms that do not directly correspond to the final TSVM instruction set.

For this reason, the repository distinguishes between:

```text
frontend-supported
```

and:

```text
verified end-to-end
```

instead of presenting all parsed constructs as fully executable.

## 21. Verified End-to-End Path

The included sample program exercises the stable path:

```text
TesLang source
    ↓
lexical analysis
    ↓
recursive-descent parsing
    ↓
AST construction
    ↓
semantic analysis
    ↓
integer/function code generation
    ↓
TSVM IR
    ↓
TSVM execution
```

The source:

```text
funk <int> sum(a as int, b as int) {
    return a + b;
}

funk <null> main() {
    x :: int = 5;
    y :: int = 31;
    print(356 + 44 + sum(x, y));
}
```

produces:

```text
436
```

when executed on TSVM.

## 22. Verification Strategy

The repository includes:

```text
scripts/smoke-test.sh
```

The smoke test verifies:

1. Python source compilation,
2. TesLang sample compilation,
3. generated IR against the checked-in reference IR,
4. TSVM execution when the runtime is available.

GitHub Actions repeats this verification on repository pushes and pull requests.

## 23. Implementation Evolution

The Git history preserves the compiler's incremental development.

Major milestones are marked with repository tags:

```text
lexer-complete
frontend-complete
compiler-complete
```

The current `main` branch contains repository cleanup, documentation, and presentation work while keeping the original implementation history available.

## 24. Design Focus

The implementation favors explicit compiler stages over abstraction-heavy frameworks.

The primary goals were to make the following mechanisms visible in code:

- tokenization,
- source-location tracking,
- recursive-descent parsing,
- operator precedence,
- AST construction,
- visitor-based compiler passes,
- lexical scopes,
- symbol resolution,
- semantic type rules,
- definite assignment,
- return-path validation,
- virtual-register allocation,
- procedure calls,
- target IR generation.

This makes the repository useful both as a functioning compiler for its verified subset and as a concrete exploration of compiler internals.
