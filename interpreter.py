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
        print(rec_print(expr, 0))
        results.append(linearize(evaluate(expr)))
        
    return " ;; ".join(str(x) for x in results)

# convert concrete syntax to CST
parser = Lark(open("grammar.lark").read(), parser='lalr')

def rec_print(tree, depth):
    tabs = depth * '  '
    tabbed = False
    for item in tree:
        if isinstance(item, tuple):
            print()
            rec_print(item, depth + 1)
        else:
            if not tabbed:
                print(f"{tabs}{item}", end=' ')
                tabbed = True
            else:
                print(f"{item}", end=' ')

# convert CST to AST
class LambdaCalculusTransformer(Transformer):
    def start(self, args):
        return args  # This will return the list of statements directly
        
    def statement(self, args):
        expr, = args
        return ('statement', expr)
        
    def lam(self, args):
        name, body = args
        print(f"LAM-----------------\n\t{name}\n\t{body}\n\t{args}")
        print("-----------------")
        return ('lam', str(name), body)

    def app(self, args):
        print(f"APP-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('app', *args)

    def var(self, args):
        token, = args
        print(f"VAR-----------------\n\t{token}")
        print("-----------------")
        return ('var', str(token))

    def NAME(self, token):
        print(f"NAME-----------------\n\t{token}")
        print("-----------------")
        return str(token)

    def number(self, args):
        token, = args
        print(f"NUMBER-----------------\n\t{token}")
        print("-----------------")
        return float(token)
    
    def plus(self, args):
        print(f"PLUS-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('plus', ('number', args[0]), ('number', args[1]))

    def minus(self, args):
        print(f"MINUS-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('minus', ('number', args[0]), ('number', args[1]))
    
    def mul(self, args):
        print(f"MUL-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('mul', ('number', args[0]), ('number', args[1]))

    def neg(self, args):
        print(f"NEG-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('neg', ('number', args[0]))

    def if_(self, args):
        print(f"IF-----------------\n\t{args[0]}\n\t{args[1]}\n\t{args[2]}")
        print("-----------------")
        return ('if', ('number', args[0]), ('number', args[1]), ('number', args[2]))

    def leq(self, args):
        # Handles: exp <= exp
        print(f"LEQ-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('leq', ('number', args[0]), ('number', args[1]))
    
    def eq(self, args):
        # Handles: exp == exp
        print(f"EQ-----------------\n\t{args[0]}\n\t{args[1]}")
        print("-----------------")
        return ('eq', ('number', args[0]), ('number', args[1]))

    def let(self, args):
        # Handles: let NAME = exp in exp
        name, expr1, expr2 = args
        print(f"LET-----------------\n\t{name}\n\t{expr1}\n\t{expr2}")
        print("-----------------")
        return ('let', (str(name)), (expr1), (expr2))

    def fix(self, args):
        expr, = args
        print(f"FIX-----------------\n\t{expr}")
        print("-----------------")
        return ('fix', expr)
    
    def rec(self, args):
        name, expr1, expr2 = args
        print(f"REC-----------------\n\t{name}\n\t{expr1}\n\t{expr2}")
        print("-----------------")
        return ('let', (str(name)), ('fix',expr1), (expr2))

    def statement(self, args):
        expr, = args
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

# reduce AST to normal form
def evaluate(tree):
    print(f"TOP OF EVAL", tree)
    if isinstance(tree, (int, float, str)):
        result = tree
    elif tree[0] == 'app':
        if tree[1][0] == 'fix':
            _tree = ('fix', tree[2], tree[1][1])
            result = evaluate(_tree)
        else:
            e1 = evaluate(tree[1])

            if e1[0] == 'lam':
                body = e1[2]
                name = e1[1]
                arg = tree[2]
                rhs = substitute(body, name, arg)
                result = evaluate(rhs)
                pass
            elif e1[0] == 'var':
                print("FOUND VARRRR")
                result = evaluate(tree[2])
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
        _then = evaluate(tree[2])
        _else = evaluate(tree[3])

        if _if == 0.0:  # False
            print(f"\tFALSE: {_else} for {tree[3]}")
            result = ('var', _else)
        else:  # true
            result = ('var', _then)

    elif tree[0] == 'eq':
        print("\t" + str(tree))
        result = (float)(tree[1][1] == tree[2][1])

    elif tree[0] == 'leq':
        result = (float)(tree[1][1] <= tree[2][1])

    elif tree[0] == 'let':
        result = evaluate(substitute(tree[3], tree[1], (tree[2])))
    elif tree[0] == 'fix':
        print("FIXED")
        print(tree)
        _if = evaluate(substitute(tree[2][2], 'n', tree[1]))
        print("IF" + str(_if))
        _tree = substitute(tree[2], 'n', ('number', tree[1]))
        print(f"TREE: {_tree}")
        print(tree[1][2])
        print(tree[1][2][1])
        cond = tree[1][2][1]
        result = tree
        
        # if tree[2][0] == 'fix':
        #     result = letrec_evaluate(tree[1], tree[2], tree[3][2])
        # else:
        #     ...

    # elif tree[0] == 'rec':
    #     result = evaluate(substitute(tree[3], tree[1], (tree[2])))

    # elif tree[0] == 'fix':
    #     func_tree = tree[1]
    #     # Direct substitution of the 'fix' back into the function's body
    #     substituted_func = substitute(func_tree, func_tree[1], tree)
    #     return evaluate(substituted_func)

    elif tree[0] == 'hd':
        list_val = evaluate(tree[1])
        if list_val[0] == 'cons':
            result = evaluate(list_val[1])

    elif tree[0] == 'tl':
        list_val = evaluate(tree[1])
        if list_val[0] == 'cons':
            result = evaluate(list_val[2])

    elif tree[0] == 'cons':
        head = evaluate(tree[1])
        tail = evaluate(tree[2])
        result = ('cons', head, tail)

    elif tree[0] == 'nil':
        result = tree

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
    print("REPLACING " + str(name) + " WITH " + str(replacement) + " IN "+ str(tree))
    print(tree)
    # tree [replacement/name] = tree with all instances of 'name' replaced by 'replacement'
    if(isinstance(tree, float)):
        result = tree
    elif tree[0] == 'var':
        if tree[1] == name:
            print("GTTEM")
            result = replacement # n [r/n] --> r
        else:
            result = tree # x [r/n] --> x
    elif tree[0] == 'lam':
        if tree[1] == name:
            result = tree # \n.e [r/n] --> \n.e
        else:
            fresh_name = name_generator.generate()
            result = ('lam', fresh_name, substitute(substitute(tree[2], tree[1], ('var', fresh_name)), name, replacement))
            # \x.e [r/n] --> (\fresh.(e[fresh/x])) [r/n]
    elif tree[0] == 'app':
        result = ('app', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'plus':
        result = ('plus', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    elif tree[0] == 'minus':
        result = ('minus', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    elif tree[0] == 'mul':
        result = ('mul', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'number':
        if isinstance(tree[1], (float, int)):
            result = ('number', tree[1])
        else:
            result = ('number', substitute(tree[1], name, replacement))
    elif tree[0] == 'neg':
        result = tree


    elif tree[0] == 'if':
        print(substitute(tree[1], name, replacement))
        result = ('if', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement), substitute(tree[3], name, replacement))

    elif tree[0] == 'eq':
        result = ('eq', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'leq':
        result = ('leq', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))

    elif tree[0] == 'let':
        print('\t' + str(tree))

        if(name == tree[1]):
            tree = evaluate(tree)
        
        if isinstance(tree, (int, float)):
            result = ('number',tree)
        else:
            result = ('let', tree[1], substitute(tree[2], name, replacement), substitute(tree[3], name, replacement))
    elif tree[0] == 'rec':
        print('\t' + str(tree))

        if(name == tree[1]):
            tree = evaluate(tree)
        
        if isinstance(tree, (int, float)):
            result = ('number',tree)
        else:
            result = ('rec', tree[1], substitute(tree[2], name, replacement), substitute(tree[3], name, replacement))
    elif tree[0] == 'fix':
        result = ('fix', substitute(tree[1],name,replacement))

    elif tree[0] == 'cons':
        result = ('cons', substitute(tree[1], name, replacement), substitute(tree[2], name, replacement))
    elif tree[0] == 'hd':
        result = ('hd', substitute(tree[1], name, replacement))
    elif tree[0] == 'tl':
        result = ('tl', substitute(tree[1], name, replacement))
    elif tree[0] == 'nil':
        result = tree

    else:
        raise Exception('Unknown tree', tree)
    
    print(f"SUB RES: {result}")
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
