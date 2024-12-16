### Question 2

In lambda calculus, expressions are evaluated by applying functions to arguments.  For this to happen, functions and arguments need to be grouped in pairs.  This is why "a b c d" reduces to "(((a b) c) d)", as it allows for the application of a onto b, c on to the result of that application, and finally d on to the result of the previous applications.  "(a)" reduces to "a" since there are no applications happening.  Since there is no grouping required, the parentheses are dropped.

### Question 3

Capture-avoiding substitution is a method used to replace a variable in a mathematical expression without changing its meaning. Imagine you have a formula with placeholders, and you want to swap one placeholder for another value. If you aren’t careful, some parts of the formula might accidentally change meaning because the new value might clash with an existing one. To avoid this, the substitution is done carefully, sometimes renaming other parts, so everything stays clear and correct.

### Question 4

No, you do not always get the expected result in lambda calculus. Not all computations reduce to normal form; some, like the omega combinator, can result in infinite loops and never simplify. While many expressions do reduce to a final form, some expressions will continue expanding indefinitely.


### Question 5

The smallest lambda expression that does not reduce to normal form is called the omega combinator. It looks like this: `(λx. x x) (λx. x x)`. When you try to reduce it, it infinitely applies itself, leading to an endless loop of expansion. As a result, this expression never reaches a final, simplified form, which is why it does not have a normal form.

### Question 7

((\m.\n. m n) (\f.\x. f (f x))) (\f.\x. f (f (f x)))

((\Var1. (\f.\x. f (f x)) Var1) ) (\f.\x. f (f (f x)))

((\Var2.(\Var4.(Var2 (Var2 Var4)))) (\f.(\x.(f (f (f x))))))

(\Var5.((\f.(\x.(f (f (f x))))) ((\f.(\x.(f (f (f x))))) Var5)))

### Question 8

<img width="900" alt="Screen Shot 2024-11-03 at 4 52 53 PM" src="https://github.com/user-attachments/assets/dbb79bef-8638-4a7f-a05d-6e9c4f7f5e3c">
<img width="1129" alt="Screen Shot 2024-11-03 at 4 53 08 PM" src="https://github.com/user-attachments/assets/3fe48be5-6bf8-4b62-ace1-2b172145bc30">
