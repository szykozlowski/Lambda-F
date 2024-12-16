# Lambda Calculus Interpreter in Python

This repositor contains a functioning interpreter for lambda calculus written in python.  grammar.lark contains the rules for the grammar/helps create the ast, and interpreter.py is where the ast is evaluated.

## Capabilities

- Basic Arithmetic (+ - *)
- Lambda Calculus Expressions
- Conditionals (if then else)
- Equalities (== <=)
- Operations on Lists (head, tail, conc)
- Fixed-Point Recursion
- Assignment (let x = 1)
- Delimiting (;\;)

## How to Run

> python interpreter.py test.lc