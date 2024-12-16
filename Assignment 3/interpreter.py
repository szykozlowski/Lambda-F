import sys
from lark import Lark, Transformer, Tree
import lark
import os

print(f"Python version: {sys.version}")
print(f"Lark version: {lark.__version__}")

#  run/execute/interpret source code
def interpret(source_code):
    cst = parser.parse(source_code)
    ast = LambdaCalculusTransformer().transform(cst)
    result_ast = evaluate(ast)
    result = linearize(result_ast)
    return result

# convert concrete syntax to CST
parser = Lark(open("grammar.lark").read(), parser='lalr')

# convert CST to AST
class LambdaCalculusTransformer(Transformer):
    def lam(self, args):
        name, body = args
        return ('lam', str(name), body)

    def app(self, args):
        new_args = [(arg.data, arg.children[0]) if isinstance(arg, Tree) and arg.data == 'int' else arg for arg in args]
        return ('app', *new_args)

    def var(self, args):
        token, = args
        return ('var', str(token))

    def NAME(self, token):
        return str(token)

# reduce AST to normal form
def evaluate(tree, depth = 0, source="initial"):
    # print(f"{depth * '\t'}[ EVALUATION ] -> {source}\n{(depth + 1) * '\t'}LTree: {linearize(tree)}\n{(depth + 1) * '\t'}Tree: {tree}")
    if tree[0] == 'app':
        e1 = evaluate(tree[1], depth + 1, "E1")
        if e1[0] == 'lam':
            body = e1[2]
            name = e1[1]
            argument = evaluate(tree[2], depth + 1, "ARG")
            rhs = substitute(body, name, argument, depth)
            result = evaluate(rhs, depth + 1, "RESULT") 
        else:
            result = ('app', e1, tree[2])
    elif tree[0] == 'lam':
        body = evaluate(tree[2], depth + 1, "ELIF LAM")
        result = ('lam', tree[1], body)
    else:
        result = tree
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

# beta reduction (apply a function to an argument)
def substitute(tree, name, replacement, depth = 0):
    # print(f"{'\t' * depth}[ SUBSTITUTION ]\n{(depth + 1) * '\t'}Tree: {linearize(tree)}\n{(depth + 1) * '\t'}Name: {name}\n{(depth + 1) * '\t'}Replacement: {linearize(replacement)}")
    # tree [replacement/name] = tree with all instances of 'name' replaced by 'replacement'
    if tree[0] == 'var':
        if tree[1] == name:
            return replacement
        else:
            return tree
    elif tree[0] == 'lam':
        # ( \ tree[1] . tree[2] ) [replacement/name]
        if tree[1] == name:
            return tree
        else:
            new_name = name_generator.generate()
            return ('lam', new_name, substitute(substitute(tree[2], tree[1], ('var', new_name), depth + 1), name, replacement, depth + 1))
    elif tree[0] == 'app':
        return ('app', substitute(tree[1], name, replacement, depth + 1), substitute(tree[2], name, replacement, depth + 1))
    else:
        raise Exception('Unknown tree', tree)

def linearize(ast):
    if ast[0] == 'var':
        return ast[1]
    elif ast[0] == 'lam':
        return "(" + "\\" + ast[1] + "." + linearize(ast[2]) + ")"
    elif ast[0] == 'app':
        return "(" + linearize(ast[1]) + " " + linearize(ast[2]) + ")"
    else:
        raise Exception('Unknown AST', ast)

def main():
    import sys
    if len(sys.argv) != 2:
        #print("Usage: python interpreter.py <filename or expression>", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]

    if os.path.isfile(input_arg):
        # If the input is a valid file path, read from the file
        with open(input_arg, 'r') as file:
            expression = file.read()
    else:
        # Otherwise, treat the input as a direct expression
        expression = input_arg

    result = interpret(expression)
    print(f"\033[95m{result}\033[0m")

if __name__ == "__main__":
    main()