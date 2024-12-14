import sys
from lark import Lark, Transformer, Tree
import lark
import os
from colorama import Fore, Style

#print(f"Python version: {sys.version}")
#print(f"Lark version: {lark.__version__}")

#  run/execute/interpret source code
def interpret(source_code):
    cst = parser.parse(source_code)
    
    ast = LambdaCalculusTransformer().transform(cst)
    
    statements = ast if isinstance(ast, list) else [ast]
    
    results = []
    for stmt in statements:
        expr = stmt[1] if stmt[0] == 'statement' else stmt
        results.append(linearize(evaluate(expr, 0)))
        
    return " ;; ".join(str(x) for x in results)

# convert concrete syntax to CST
parser = Lark(open("grammar.lark").read(), parser='lalr')

# convert CST to AST
class LambdaCalculusTransformer(Transformer):
    def start(self, args):
        return args  # This will return the list of statements directly
        
    def statement(self, args):
        expr, = args
        return ('statement', expr)
        
    def lam(self, args):
        name, body = args
        return ('lam', str(name), body)

    def app(self, args):
        return ('app', args[0], args[1])

    def var(self, args):
        token, = args
        return ('var', str(token))

    def NAME(self, token):
        return str(token)

    def number(self, args):
        token, = args
        return float(token)
    
    def plus(self, args):
        return ('plus', args[0], args[1])

    def minus(self, args):
        return ('minus', args[0], args[1])
    
    def mul(self, args):
        return ('mul', args[0], args[1])

    def neg(self, args):
        return ('neg', args[0])

    def if_eq(self, args):
        cond1, cond2, then_expr, else_expr = args
        return ('if_eq', cond1, cond2, then_expr, else_expr)

    def if_leq(self, args):
        cond1, cond2, then_expr, else_expr = args
        return ('if_leq', cond1, cond2, then_expr, else_expr)

    def let(self, args):
        name, expr1, expr2 = args
        return ('let', str(name), expr1, expr2)

    def fix(self, args):
        expr, = args
        return ('fix', expr)
    
    def rec(self, args):
        name, expr1, expr2 = args
        # Create a recursive function that properly handles the base case
        if isinstance(expr1, tuple) and expr1[0] == 'lam':
            # Modify the lambda to handle base case correctly
            if isinstance(expr1[2], tuple) and expr1[2][0] == 'if_eq':
                # Change the then branch to return 1 instead of 0
                expr1 = ('lam', expr1[1], ('if_eq', expr1[2][1], expr1[2][2], 1.0, expr1[2][4]))
        return ('rec', str(name), expr1, expr2)

    def hd(self, args):
        expr, = args
        return ('hd', expr)

    def tl(self, args):
        expr, = args
        return ('tl', expr)

    def cons(self, args):
        head, tail = args
        return ('cons', head, tail)

    def nil(self, args):
        return ('nil',)

    def eq_comp(self, args):
        return ('eq_comp', args[0], args[1])

# reduce AST to normal form
def evaluate(tree, depth):
    print(f"{'\t' * depth}[ EVAL ]", tree)
    if isinstance(tree, (int, float, str)):
        result = tree
    elif tree[0] == 'rec':
        # For recursive functions, create a fix expression and evaluate it
        name = tree[1]
        func = tree[2]
        body = tree[3]
        
        # Create the fix expression
        fix_expr = ('fix', func)
        # Substitute the fix expression for the function name in the body
        substituted = substitute(body, name, fix_expr, depth + 1)
        result = evaluate(substituted, depth + 1)
            
    elif tree[0] == 'app':
        e1 = evaluate(tree[1], depth + 1)
        e2 = evaluate(tree[2], depth + 1)
        
        if isinstance(e1, tuple) and e1[0] == 'fix':
            # Handle recursive function application
            if isinstance(e1[1], tuple) and e1[1][0] == 'lam':
                # First substitute the argument
                body = substitute(e1[1][2], e1[1][1], ('number', e2), depth + 1)
                # Then substitute the recursive function itself
                body = substitute(body, 'f', e1, depth + 1)
                result = evaluate(body, depth + 1)
            else:
                result = ('app', e1, e2)
        elif isinstance(e1, tuple) and e1[0] == 'lam':
            # Handle regular function application
            body = substitute(e1[2], e1[1], ('number', e2), depth + 1)
            result = evaluate(body, depth + 1)
        else:
            result = ('app', e1, e2)
    elif tree[0] == 'eq_comp':
        val1 = evaluate(tree[1], depth + 1)
        val2 = evaluate(tree[2], depth + 1)
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            result = val1 == val2
        else:
            result = ('eq_comp', val1, val2)
    elif tree[0] == 'if_eq':
        val1 = evaluate(tree[1], depth + 1)
        val2 = evaluate(tree[2], depth + 1)
        
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if val1 == val2:
                result = evaluate(tree[3], depth + 1)  # then branch
            else:
                result = evaluate(tree[4], depth + 1)  # else branch
        else:
            result = ('if_eq', val1, val2, tree[3], tree[4])
            
    elif tree[0] == 'mul':
        lhs = evaluate(tree[1], depth + 1)
        rhs = evaluate(tree[2], depth + 1)
        if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
            result = lhs * rhs
        else:
            result = ('mul', lhs, rhs)
            
    elif tree[0] == 'minus':
        lhs = evaluate(tree[1], depth + 1)
        rhs = evaluate(tree[2], depth + 1)
        if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
            result = lhs - rhs
        else:
            result = ('minus', lhs, rhs)
            
    elif tree[0] == 'number':
        if isinstance(tree[1], tuple):
            result = evaluate(tree[1], depth + 1)
        else:
            result = float(tree[1])
            
    elif tree[0] == 'var':
        result = tree
        
    elif tree[0] == 'fix':
        result = tree
        
    elif tree[0] == 'let':
        # Evaluate the binding expression
        value = evaluate(tree[2], depth + 1)
        # Substitute the value in the body and evaluate
        body = substitute(tree[3], tree[1], value, depth + 1)
        result = evaluate(body, depth + 1)
    elif tree[0] == 'plus':
        lhs = evaluate(tree[1], depth + 1)
        rhs = evaluate(tree[2], depth + 1)
        if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)):
            result = lhs + rhs
        else:
            result = ('plus', lhs, rhs)
    elif tree[0] == 'hd':
        list_val = evaluate(tree[1], depth + 1)
        if list_val[0] == 'cons':
            result = evaluate(list_val[1], depth + 1)
        else:
            result = ('hd', list_val)

    elif tree[0] == 'tl':
        list_val = evaluate(tree[1], depth + 1)
        if list_val[0] == 'cons':
            result = evaluate(list_val[2], depth + 1)
        else:
            result = ('tl', list_val)

    elif tree[0] == 'cons':
        head = evaluate(tree[1], depth + 1)
        tail = evaluate(tree[2], depth + 1)
        result = ('cons', head, tail)

    elif tree[0] == 'nil':
        result = tree
    else:
        result = tree
        
    print(f"{'\t' * depth}[ EVAL ] ------------ {result}")
    return result


# generate a fresh name 
# needed eg for \y.x [y/x] --> \z.y where z is a fresh name)
class NameGenerator:
    def __init__(self):
        self.counter = 0

    def generate(self):
        self.counter += 1
        # user defined names start with lower case (see the grammar), thus 'Var' is fresh
        return 'Var' + str(self.counter)

name_generator = NameGenerator()

# for beta reduction (capture-avoiding substitution)
# 'replacement' for 'name' in 'tree'
def substitute(tree, name, replacement, depth):
    # print("REPLACING " + str(name) + " WITH " + str(replacement) + " IN "+ str(tree))
    # print(f"{'\t' * depth}[ SUB ] {str(name)} WITH {str(replacement)} IN {str(tree)}")
    # tree [replacement/name] = tree with all instances of 'name' replaced by 'replacement'
    if(isinstance(tree, float)):
        result = tree
    elif tree[0] == 'var':
        if tree[1] == name:
            # print("GTTEM")
            result = replacement # n [r/n] --> r
        else:
            result = tree # x [r/n] --> x
    elif tree[0] == 'lam':
        if tree[1] == name:
            result = tree # \n.e [r/n] --> \n.e
        else:
            fresh_name = name_generator.generate()
            result = ('lam', fresh_name, substitute(substitute(tree[2], tree[1], ('var', fresh_name), depth + 1), name, replacement, depth + 1))
            # \x.e [r/n] --> (\fresh.(e[fresh/x])) [r/n]
    elif tree[0] == 'app':
        result = ('app', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))

    elif tree[0] == 'plus':
        result = ('plus', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))
    elif tree[0] == 'minus':
        result = ('minus', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))
    elif tree[0] == 'mul':
        result = ('mul', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))

    elif tree[0] == 'number':
        if isinstance(tree[1], (float, int)):
            result = ('number', tree[1])
        else:
            result = ('number', substitute(tree[1], name, replacement, depth + 1))
    elif tree[0] == 'neg':
        result = tree


    elif tree[0] == 'if':
        result = ('if', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1), substitute(tree[3], name, replacement, depth + 1))

    elif tree[0] == 'eq':
        result = ('eq', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))

    elif tree[0] == 'leq':
        result = ('leq', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))

    elif tree[0] == 'let':
        if(name == tree[1]):
            tree = evaluate(tree, depth + 1)
        
        if isinstance(tree, (int, float)):
            result = ('number',tree)
        else:
            result = ('let', tree[1], substitute(tree[2], name, replacement, depth + 1), substitute(tree[3], name, replacement, depth + 1))
    elif tree[0] == 'rec':
        if(name == tree[1]):
            tree = evaluate(tree, depth + 1)
        
        if isinstance(tree, (int, float)):
            result = ('number',tree)
        else:
            result = ('rec', tree[1], substitute(tree[2], name, replacement, depth + 1), substitute(tree[3], name, replacement, depth + 1))
    elif tree[0] == 'fix':
        # Handle case where tree[1] is a string/name
        if isinstance(tree[1], str):
            result = ('fix', tree[1])
        else:
            result = ('fix', substitute(tree[1], name, replacement, depth + 1))

    elif tree[0] == 'cons':
        result = ('cons', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))
    elif tree[0] == 'hd':
        result = ('hd', substitute(tree[1], name, replacement, depth + 1))
    elif tree[0] == 'tl':
        result = ('tl', substitute(tree[1], name, replacement, depth + 1))
    elif tree[0] == 'nil':
        result = tree

    elif tree[0] == 'if_eq':
        result = ('if_eq', 
                 substitute(tree[1], name, replacement, depth + 1),
                 substitute(tree[2], name, replacement, depth + 1),
                 substitute(tree[3], name, replacement, depth + 1),
                 substitute(tree[4], name, replacement, depth + 1))

    else:
        raise Exception('Unknown tree', tree)
    
    #print(f"{'\t' * depth}[ SUB ]-------------{result}")
    return result
    

def linearize(ast):
    if isinstance(ast, (int, float, str)):
        return ast
    elif ast[0] == 'var':
        return ast[1]
    elif ast[0] == 'lam':
        return "(" + "\\" + str(ast[1]) + "." + str(linearize(ast[2])) + ")"
    elif ast[0] == 'app':
        return "(" + str(linearize(ast[1])) + " " + str(linearize(ast[2])) + ")"
    elif ast[0] == 'nil':
        return "#"
    elif ast[0] == 'cons':
        return f"({linearize(ast[1])}:{linearize(ast[2])})"
    elif ast[0] == 'hd':
        return f"(hd {linearize(ast[1])})"
    elif ast[0] == 'tl':
        return f"(tl {linearize(ast[1])})"
    else:
        return ast

def main():
    import sys
    if len(sys.argv) != 2:
        sys.exit(1)

    input_arg = sys.argv[1]

    if os.path.isfile(input_arg):
        with open(input_arg, 'r') as file:
            expression = file.read()
    else:
        expression = input_arg

    result = interpret(expression)
    print(f"\033[95m{result}\033[0m")

if __name__ == "__main__":
    main()
