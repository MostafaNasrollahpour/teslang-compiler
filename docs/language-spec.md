# TesLang Language Specification

## 1. Overview

TesLang is a small statically checked programming language designed around functions, explicit type declarations, structured control flow, expressions, vectors, and a small set of built-in operations.

This document describes the language surface recognized and validated by the TesLang compiler frontend.

Backend support is intentionally narrower than frontend support. The backend support status is documented separately in [Compiler Architecture](compiler-architecture.md).

## 2. Lexical Structure

### 2.1 Whitespace

Spaces, tabs, carriage returns, and newline characters are ignored outside literals.

Whitespace is used only to separate tokens and does not define program structure.

### 2.2 Identifiers

Identifiers begin with a letter or underscore.

Subsequent characters may contain letters, digits, or underscores.

Examples:

```text
x
result
_sum
value2
my_variable
```

Keywords cannot be used as ordinary identifiers.

### 2.3 Keywords

The compiler recognizes the following keywords and built-ins:

```text
funk
int
vector
str
mstr
bool
null
as
return
if
else
endif
while
endwhile
do
for
to
begin
end
endfor
scan
print
list
length
exit
true
false
```

### 2.4 Numeric Literals

Numeric tokens begin with one or more decimal digits.

Examples:

```text
0
10
356
```

The lexer can also recognize a decimal point inside a numeric token:

```text
10.5
```

However, TesLang currently defines only the `int` numeric type. Numeric literals containing a decimal point are therefore rejected during semantic analysis.

### 2.5 String Literals

Quoted string literals may use either single or double quotes:

```text
"hello"
'hello'
```

The lexer recognizes the escape sequences:

```text
\n
\t
```

Other escaped characters are inserted as the escaped character itself.

Examples:

```text
"hello\nworld"
"column1\tcolumn2"
```

### 2.6 Multiline Strings

A multiline string uses three double quotes:

```text
"""
This is a
multiline string.
"""
```

Multiline string literals have type `mstr`.

### 2.7 Boolean Literals

Boolean literals are:

```text
true
false
```

Their type is `bool`.

### 2.8 Null Literal

The null literal is:

```text
null
```

`null` is also used in function declarations to represent a function with no return value.

### 2.9 Comments

TesLang comments begin with:

```text
</
```

and end with:

```text
/>
```

Example:

```text
</ this is a comment />
```

Comments may span multiple lines.

Nested comments are supported:

```text
</
    outer comment

    </ nested comment />

    outer comment continues
/>
```

An unclosed comment is reported as a syntax error.

## 3. Type System

TesLang recognizes the following declared types:

```text
int
bool
str
mstr
vector
null
```

Internally, `null` is mapped to the compiler's `void` type when used as a function return type.

### 3.1 `int`

Represents integer values.

Example:

```text
x :: int = 10;
```

### 3.2 `bool`

Represents boolean values.

Example:

```text
flag :: bool = true;
```

### 3.3 `str`

Represents a quoted string value.

Example:

```text
message :: str = "hello";
```

### 3.4 `mstr`

Represents a multiline string value.

Example:

```text
message :: mstr = """
hello
world
""";
```

`str` and `mstr` are considered compatible by the semantic analyzer.

### 3.5 `vector`

Represents a vector containing integer elements.

Example:

```text
values :: vector = [1, 2, 3];
```

### 3.6 `null`

`null` represents the absence of a value.

For function declarations, a `null` return type represents a function that does not return a value:

```text
funk <null> main() {
}
```

## 4. Variables

### 4.1 Declaration

Variables are declared using `::`:

```text
name :: type;
```

Example:

```text
x :: int;
```

### 4.2 Initialization

A declaration may include an initializer:

```text
x :: int = 10;
flag :: bool = true;
```

The initializer must be compatible with the declared type.

### 4.3 Assignment

Variables are assigned using `=`:

```text
x = 20;
```

The assigned value must be compatible with the variable's declared type.

### 4.4 Definite Assignment

Reading a variable before it has been initialized or assigned is a semantic error.

Example:

```text
x :: int;
print(x);
```

The semantic analyzer reports that `x` is used before being assigned.

### 4.5 Duplicate Declarations

A variable cannot be declared more than once in the same lexical scope.

A nested scope may declare a different symbol with the same name.

## 5. Functions

### 5.1 Standard Function Declaration

Functions are declared with `funk`.

Syntax:

```text
funk <return-type> function-name(parameters) {
    statements
}
```

Example:

```text
funk <int> sum(a as int, b as int) {
    return a + b;
}
```

### 5.2 Parameters

Parameters use the syntax:

```text
name as type
```

Multiple parameters are separated by commas:

```text
funk <int> add(a as int, b as int) {
    return a + b;
}
```

Function arguments are checked against parameter types during semantic analysis.

### 5.3 Void Functions

A function with no return value uses `null` as its declared return type:

```text
funk <null> show() {
    print(10);
}
```

Internally, the compiler represents this return type as `void`.

### 5.4 Expression-Body Functions

TesLang also supports a compact function form:

```text
funk <int> add(a as int, b as int) => return a + b;
```

The body of this form consists of one return expression.

### 5.5 Nested Function Declarations

The parser accepts function declarations inside function bodies.

Semantic handling for nested function declarations is incomplete in the current implementation, and nested functions are not part of the supported end-to-end subset.

### 5.6 Function Calls

Functions are called using parentheses:

```text
sum(10, 20)
```

The semantic analyzer checks:

- that the function exists,
- that the number of arguments is correct,
- that argument types are compatible with parameter types.

### 5.7 Entry Point

A valid TesLang program must define a function named `main`.

Its required signature is:

```text
funk <null> main()
```

`main` must not accept parameters.

## 6. Return Statements

A return statement has one of the following forms:

```text
return;
```

or:

```text
return expression;
```

A function with a non-void return type must return a compatible value.

Example:

```text
funk <int> value() {
    return 10;
}
```

A void function cannot return a value.

For non-void functions, the semantic analyzer performs return-path validation.

## 7. Expressions

### 7.1 Arithmetic Operators

TesLang supports:

```text
+
-
*
/
%
```

For integers:

```text
10 + 20
a - b
x * y
value / 2
value % 2
```

`-`, `*`, `/`, and `%` require integer operands.

`+` supports either:

- two integer operands, producing `int`, or
- two string-like operands (`str` or `mstr`), producing a string value.

Integer and string operands cannot be mixed.

### 7.2 Comparison Operators

Supported comparison operators are:

```text
<
>
<=
>=
==
!=
```

Comparison results have type `bool`.

Operands must have compatible types.

`str` and `mstr` are considered mutually compatible for comparison.

### 7.3 Logical Operators

Logical operators are:

```text
&&
||
!
```

`&&` and `||` require boolean operands.

`!` requires one boolean operand.

### 7.4 Unary Operators

Unary arithmetic operators are:

```text
+
-
```

They require an integer operand.

Example:

```text
-x
+value
```

### 7.5 Assignment Expressions

Assignment is an expression:

```text
x = value
```

Assignment is right-associative.

Example:

```text
a = b = 10;
```

The semantic analyzer restricts assignment targets to variables and indexed vector elements.

### 7.6 Ternary Expressions

TesLang supports conditional expressions:

```text
condition ? value1 : value2
```

The condition must have type `bool`.

The two result expressions must have compatible types.

Example:

```text
max = a > b ? a : b;
```

## 8. Operator Precedence

From highest precedence to lowest:

| Level | Operators | Associativity |
|---|---|---|
| 1 | array indexing `[]` | left |
| 2 | unary `+`, `-`, `!` | right |
| 3 | `*`, `/`, `%` | left |
| 4 | `+`, `-` | left |
| 5 | `<`, `>`, `<=`, `>=` | left |
| 6 | `==`, `!=` | left |
| 7 | `&&` | left |
| 8 | `||` | left |
| 9 | `?:` | right |
| 10 | `=` | right |

Parentheses may be used to explicitly control evaluation order:

```text
(a + b) * c
```

## 9. Conditional Statements

### 9.1 `if`

Conditions are enclosed in double square brackets:

```text
if [[ condition ]] begin
    statements
endif
```

The condition must have type `bool`.

### 9.2 `if / else`

```text
if [[ condition ]] begin
    statements
else begin
    statements
endif
```

The `if` and `else` branches introduce nested semantic scopes.

## 10. Loops

### 10.1 `while`

```text
while [[ condition ]] begin
    statements
endwhile
```

The condition must have type `bool`.

### 10.2 `do-while`

```text
do begin
    statements
while [[ condition ]] endwhile
```

The body executes before the condition is evaluated.

The condition must have type `bool`.

### 10.3 `for`

```text
for(i = start to end) begin
    statements
endfor
```

Example:

```text
for(i = 0 to 10) begin
    print(i);
endfor
```

The loop variable is created as an initialized integer inside the loop scope.

Both the start and end expressions must have type `int`.

## 11. Blocks and Scopes

Functions introduce lexical scopes.

The bodies of:

- functions,
- conditional branches,
- loops,
- explicit brace-delimited blocks,

also participate in scope handling.

A brace-delimited block has the form:

```text
{
    statements
}
```

Name lookup begins in the current scope and continues through parent scopes.

Symbols may shadow symbols from outer scopes, but duplicate declarations inside the same scope are rejected.

## 12. Vectors

### 12.1 Vector Literals

A vector literal uses square brackets:

```text
[1, 2, 3]
```

All elements must have type `int`.

The resulting expression has type `vector`.

### 12.2 Vector Variables

```text
values :: vector = [1, 2, 3];
```

### 12.3 Indexing

Vector elements are accessed with an integer index:

```text
values[0]
```

The indexed expression must have type `vector`.

The index must have type `int`.

Vector access produces an `int`.

### 12.4 Indexed Assignment

An indexed vector element may appear on the left-hand side of an assignment:

```text
values[0] = 10;
```

The assigned value must have type `int`.

## 13. Built-in Functions

### 13.1 `print`

Frontend signature:

```text
print(value)
```

`print` accepts exactly one argument.

The semantic analyzer accepts any frontend type.

The currently verified backend supports integer output.

### 13.2 `scan`

Signature:

```text
scan()
```

Return type:

```text
int
```

### 13.3 `list`

Signature:

```text
list(size)
```

`size` must have type `int`.

Return type:

```text
vector
```

Backend lowering for `list` is not currently part of the verified backend subset.

### 13.4 `length`

Signature:

```text
length(vector)
```

The argument must have type `vector`.

Return type:

```text
int
```

Backend lowering for `length` is not currently part of the verified backend subset.

### 13.5 `exit`

Signature:

```text
exit(code)
```

`code` must have type `int`.

Return type:

```text
void
```

Backend lowering for `exit` is not currently part of the verified backend subset.

## 14. Semantic Rules

### 14.1 Name Resolution

Variables and functions must be defined before they can be resolved through the active scope hierarchy.

Top-level functions are registered before their bodies are analyzed, allowing functions to reference other top-level functions.

Nested function symbols are also pre-registered before the surrounding function body is analyzed, but nested-function semantic context handling is incomplete.

### 14.2 Type Compatibility

Types must normally match exactly.

Additional compatibility rules are:

- `str` and `mstr` are mutually compatible.
- an internal `void` value is compatible with `null` where applicable.
- semantic `error` types are treated as compatible to avoid cascading diagnostics.

### 14.3 Variable Initialization

A variable declaration without an initializer creates an uninitialized symbol.

An assignment marks that variable as initialized.

Reading an uninitialized variable reports a semantic error.

### 14.4 Function Calls

A function call must match:

- the declared function name,
- the required argument count,
- the declared parameter types.

### 14.5 Return Validation

Void functions cannot return values.

Non-void functions must return values compatible with their declared return type.

The semantic analyzer also checks that non-void functions return on all recognized terminal paths.

### 14.6 Conditions

The conditions of:

- `if`,
- `while`,
- `do-while`,
- ternary expressions,

must have type `bool`.

### 14.7 Entry Point

Every program must provide exactly the required entry-point form:

```text
funk <null> main()
```

## 15. Grammar Summary

The following grammar is an informal EBNF-style summary of the syntax accepted by the frontend.

```text
program
    = function-declaration* EOF
    ;

function-declaration
    = "funk" "<" type ">" IDENTIFIER
      "(" parameter-list? ")"
      ( function-block | expression-function-body )
    ;

expression-function-body
    = "=>" "return" expression ";"
    ;

function-block
    = "{" statement* "}"
    ;

parameter-list
    = parameter ("," parameter)*
    ;

parameter
    = IDENTIFIER "as" type
    ;

type
    = "int"
    | "vector"
    | "str"
    | "mstr"
    | "bool"
    | "null"
    ;

statement
    = variable-declaration
    | function-declaration
    | if-statement
    | while-statement
    | do-while-statement
    | for-statement
    | return-statement
    | brace-block
    | expression-statement
    | ";"
    ;

brace-block
    = "{" statement* "}"
    ;

variable-declaration
    = IDENTIFIER "::" type ("=" expression)? ";"
    ;

if-statement
    = "if" "[[" expression "]]" "begin"
      statement*
      ("else" "begin" statement*)?
      "endif"
    ;

while-statement
    = "while" "[[" expression "]]" "begin"
      statement*
      "endwhile"
    ;

do-while-statement
    = "do" "begin"
      statement*
      "while" "[[" expression "]]"
      "endwhile"
    ;

for-statement
    = "for" "(" IDENTIFIER "=" expression "to" expression ")"
      "begin"
      statement*
      "endfor"
    ;

return-statement
    = "return" expression? ";"
    ;

expression-statement
    = expression ";"
    ;

expression
    = assignment
    ;

assignment
    = ternary ("=" assignment)?
    ;

ternary
    = logical-or ("?" expression ":" ternary)?
    ;

logical-or
    = logical-and ("||" logical-and)*
    ;

logical-and
    = equality ("&&" equality)*
    ;

equality
    = comparison (("==" | "!=") comparison)*
    ;

comparison
    = addition (("<" | ">" | "<=" | ">=") addition)*
    ;

addition
    = multiplication (("+" | "-") multiplication)*
    ;

multiplication
    = unary (("*" | "/" | "%") unary)*
    ;

unary
    = ("+" | "-" | "!") unary
    | primary
    ;

primary
    = atom ("[" expression "]")*
    ;

atom
    = NUMBER
    | STRING
    | MULTILINE_STRING
    | "true"
    | "false"
    | "null"
    | array-literal
    | call
    | IDENTIFIER
    | "(" expression ")"
    ;

call
    = callable-name "(" argument-list? ")"
    ;

callable-name
    = IDENTIFIER
    | "print"
    | "scan"
    | "list"
    | "length"
    | "exit"
    ;

argument-list
    = expression ("," expression)*
    ;

array-literal
    = "[" (expression ("," expression)*)? "]"
    ;
```

## 16. Complete Example

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

The verified backend compiles this program into TSVM intermediate representation and produces:

```text
436
```

when executed.

## 17. Implementation Note

This document describes the language recognized and checked by the compiler frontend.

Not every frontend construct currently has complete TSVM lowering.

For implementation-level details and the backend support matrix, see [Compiler Architecture](compiler-architecture.md).
