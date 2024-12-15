import sys
from lark import Lark, Transformer, Tree
import lark
import os

#print(f"Python version: {sys.version}")
#print(f"Lark version: {lark.__version__}")

#  run/execute/interpret source code
def interpret(source_code):
    # print("Thinking... Give me a moment...")
    cst = parser.parse(source_code)
    
    ast = LambdaCalculusTransformer().transform(cst)
    # print(ast)
    statements = ast if isinstance(ast, list) else [ast]
    
    results = []
    for stmt in statements:
        expr = stmt[1] if stmt[0] == 'statement' else stmt
        results.append(linearize(evaluate(expr)))
    # print(results)   
    return " ;; ".join(str(x) for x in results)

# convert concrete syntax to CST
parser = Lark(open("grammar.lark").read(), parser='lalr')

# convert CST to AST
class LambdaCalculusTransformer(Transformer):
    def start(self, args):
        # print(args)
        return args  # This will return the list of statements directly
        
    def lam(self, args):
        name, body = args
        return ('lam', str(name), body)

    def app(self, args):
        return ('app', *args)

    def var(self, args):
        token, = args
        return ('var', str(token))

    def NAME(self, token):
        return str(token)

    def number(self, args):
        token, = args
        return float(token)
    
    def plus(self, args):
        return ('plus', ('number', args[0]), ('number', args[1]))

    def minus(self, args):
        return ('minus', ('number', args[0]), ('number', args[1]))
    
    def mul(self, args):
        return ('mul', ('number', args[0]), ('number', args[1]))

    def neg(self, args):
        return ('neg', ('number', args[0]))

    def if_(self, args):
        return ('if', ('number', args[0]), ('number', args[1]), ('number', args[2]))

    def leq(self, args):
        # Handles: exp <= exp
        return ('leq', ('number', args[0]), ('number', args[1]))
    
    def eq(self, args):
        # Handles: exp == exp
        return ('eq', ('number', args[0]), ('number', args[1]))

    def let(self, args):
        # Handles: let NAME = exp in exp
        name, expr1, expr2 = args
        return ('let', (str(name)), (expr1), (expr2))

    def fix(self, args):
        expr, = args
        return ('fix', expr)
    
    def rec(self, args):
        name, expr1, expr2 = args
        return ('let', str(name), 
                ('fix', ('lam', str(name), expr1)), 
                expr2)

    def statement(self, args):
        expr, = args
        # print(args)
        return ('statement', expr)


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

    def multi_statement(self, args):
        expr, rest = args
        return [('statement', expr)] + (rest if isinstance(rest, list) else [('statement', rest)])

    def single_statement(self, args):
        expr, = args
        return ('statement', expr)

    def make_app(self, args):
        if len(args) == 1:
            return args[0]
        result = args[0]
        for arg in args[1:]:
            result = ('app', result, arg)
        return result

# reduce AST to normal form
def evaluate(tree):
    # print(tree)
    if isinstance(tree, (int, float, str)):
        result = tree
    elif tree[0] == 'app':
        # print("TREE " + str(tree))
        e1 = evaluate(tree[1])

        if e1[0] == 'lam':
            body = e1[2]
            name = e1[1]
            arg = tree[2]
            rhs = substitute(body, name, arg)
            result = evaluate(rhs)
            pass
        else:
            result = ('app', e1, tree[2])
            pass
    elif tree[0] == 'plus':
        result = evaluate(tree[1]) + evaluate(tree[2])
    elif tree[0] == 'minus':
        result = evaluate(tree[1]) - evaluate(tree[2])
    elif tree[0] == 'mul':
        result = evaluate(tree[1]) * evaluate(tree[2])

    elif tree[0] == 'number':
        result = evaluate(tree[1])
    elif tree[0] == 'neg':
        result = -evaluate(tree[1])


    elif tree[0] == 'if':
        _if = evaluate(tree[1])
        _then = tree[2]  # Don't evaluate yet
        _else = tree[3]  # Don't evaluate yet

        if _if == 0.0:  # False
            result = evaluate(_else)  # Evaluate the chosen branch
        else:  # true
            result = evaluate(_then)  # Evaluate the chosen branch

    elif tree[0] == 'eq':
        # print("\t" + str(tree))
        result = (float)(evaluate(tree[1][1]) == evaluate(tree[2][1]))

    elif tree[0] == 'leq':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return float(left <= right)
        return ('leq', left, right)

    elif tree[0] == 'let':
        result = evaluate(substitute(tree[3], tree[1], (tree[2])))

    elif tree[0] == 'hd':
        list_val = evaluate(tree[1])
        if list_val[0] == 'cons':
            result = evaluate(list_val[1])
        else:
            result = tree

    elif tree[0] == 'tl':
        list_val = evaluate(tree[1])
        if list_val[0] == 'cons':
            result = evaluate(list_val[2])
        else:
            result = tree

    elif tree[0] == 'cons':
        head = evaluate(tree[1])
        tail = evaluate(tree[2])
        result = ('cons', head, tail)

    elif tree[0] == 'nil':
        result = tree

    elif tree[0] == 'fix':
        func = evaluate(tree[1])
        if func[0] == 'lam':
            result = evaluate(('app', func, tree))
        else:
            result = ('fix', func)

    else:
        result = tree
        pass
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
def substitute(tree, name, replacement):
    # print("REPLACING " + str(name) + " WITH " + str(replacement) + " IN "+ str(tree))
    # print(tree)
    # tree [replacement/name] = tree with all instances of 'name' replaced by 'replacement'
    if(isinstance(tree, float)):
        return tree
    elif tree[0] == 'var':
        if tree[1] == name:
            # print("GTTEM")
            return replacement # n [r/n] --> r
        else:
            return tree # x [r/n] --> x
    elif tree[0] == 'lam':
        if tree[1] == name:
            return tree # \n.e [r/n] --> \n.e
        else:
            fresh_name = name_generator.generate()
            return ('lam', fresh_name, substitute(substitute(tree[2], tree[1], ('var', fresh_name)), name, replacement))
            # \x.e [r/n] --> (\fresh.(e[fresh/x])) [r/n]
    elif tree[0] == 'app':
        return ('app', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'plus':
        return ('plus', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    elif tree[0] == 'minus':
        return ('minus', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    elif tree[0] == 'mul':
        return ('mul', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'number':
        if isinstance(tree[1], (float, int)):
            return ('number', tree[1])
        else:
            return ('number', substitute(tree[1], name, replacement))
    elif tree[0] == 'neg':
        return tree


    elif tree[0] == 'if':
        # print(substitute(tree[1], name, replacement))
        return ('if', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement), substitute(tree[3], name, replacement))

    elif tree[0] == 'eq':
        return ('eq', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'leq':
        return ('leq', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'let':
        # print('\t' + str(tree))

        if(name == tree[1]):
            tree = evaluate(tree)
        
        if isinstance(tree, (int, float)):
            return ('number',tree)
        return ('let', tree[1], substitute(tree[2], name, replacement), substitute(tree[3], name, replacement))
    elif tree[0] == 'rec':
        # print('\t' + str(tree))

        if(name == tree[1]):
            tree = evaluate(tree)
        
        if isinstance(tree, (int, float)):
            return ('number',tree)
        return ('rec', tree[1], substitute(tree[2], name, replacement), substitute(tree[3], name, replacement))
    elif tree[0] == 'fix':
        return ('fix', substitute(tree[1],name,replacement))

    elif tree[0] == 'cons':
        return ('cons', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    elif tree[0] == 'hd':
        return ('hd', substitute(tree[1], name, replacement))
    elif tree[0] == 'tl':
        return ('tl', substitute(tree[1], name, replacement))
    elif tree[0] == 'nil':
        return tree

    else:
        raise Exception('Unknown tree', tree)
    

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