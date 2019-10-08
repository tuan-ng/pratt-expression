# PARSING EXPRESSIONS FOLLOWING PRATT

In this post we discuss parsing simple arithmetic expressions following Pratt's
approach. By simple arithmetic expressions we mean those that involve
additions, subtractions, multiplications, divisions, powers, factorials, and
inversion of positive and negative numbers; they may also include parentheses.

Please note that what we call parsing below actually includes evaluating as
well. By the end of this post we will have written a function `parse` such that

```python
parse("2")
2
parse("-1 - 2")
-3
parse("-1 * 2**2 - 3! + 4")
-6
parse("~2")
0.5
parse("(2 * (3 + -4))")
-2
```

and so on. This post learns from the excellent post by Fredrik Lundh, adding
some explanation of the basic ideas behind the method.

## TOKENIZING

First we will get tokenizing out of the way. To tokenize means to split an
input string into tokens, which in the current case are either numbers or
operators. Each token will be a class, and for convenience we'll add a token
that represents the end of the input string also. Assuming that we're dealing
only with additions and multiplications, we'll have the following classes

```python
class literal_token:
    def __init__(self, value):
        self.value = int(value)

class operator_add_token:
    pass

class operator_mul_token:
    pass

class end_token:
    pass
```

Now, each token may be preceded by whitespaces, but are otherwise either
numbers or operators, and so the pattern is

```python
import re

token_pat = re.compile(r"\s*(?:(\d+)|(.))")
```

Note how we discarded the outer group in the regular expression, e.g.

```python
token_pat.findall("1 + 2 + 3")
[('1', ''), ('', '+'), ('2', ''), ('', '+'), ('3', '')]
```

To continue with tokenizing:

```python
def tokenize(program):
    for number, operator in token_pat.findall(program):
        if number:
            yield literal_token(number)
        elif operator == "+":
            yield operator_add_token()
        elif operator == "*":
            yield operator_mul_token()
        else:
            raise SyntaxError("unknown operator")
    yield end_token()
```

Thus calling `tokenize` on a string now will give us a generator object.

## THE IDEAS

The code that we will show below are based on several ideas.

#### L (or left)

To start, parsing an expression can be understood as contracting the expression
to a single value. Below, to parse a given expression, we update a variable
named `L` repeatedly and return it at the end.

Examples: Just a single number, `1`,

```
1
-
L
```

where we return `L=1`. Next, the expression `1+2+3`,

```
1 + 2 + 3
-
L
-----
  L
  -------
     L
```

where we return `L=6`.

#### ORDERED PLANES

It's important to update `L`, the left value, correctly. We've seen the example
`1+2+3`:

```
1 + 2 + 3
-
L
-----
  L
  -------
     L
```

But if we look at the expression `1+2*3`, the updating of `L` must proceed
differently,

```
1 + 2 * 3
-
L
    -   -
    -----
------
  L
```

because multiplication takes precedence over addition. To aid our thinking, we
will imagine that expressions involving **different kinds** of operators live
on different ordered planes, and that the contraction to a single value happens
thoroughly on a higher plane, at which point that value is combined with the
value at the lower plane to give the final result. Example: We'll look at the
expression `1+2*3` again:

```
    2 * 3
1 +
-
L


    2 * 3
    -
    L
1 +
-
L


    2 * 3
    -----
    L
1 +
-------
  L


    6
    -
    L
1 +
-----
  L


7
-
L
```

This procedure, i.e. contracting to a single value on a higher plane and
combining it with the value in a lower plane, can be applied to deal with
operators having different precedences.

Example: We'll look at the expression `0+1+2*3*4**5`, where `**` is
the power operator.

```
                4 ** 5
        2 * 3 *
0 + 1 +
-
L


                4 ** 5
        2 * 3 *
0 + 1 +
-----
  L


            4 ** 5
    2 * 3 *
1 +
-
L


            4 ** 5
    2 * 3 *
    -
    L
1 +
-
L


            4 ** 5
    2 * 3 *
    -----
      L
1 +
-
L


        4 ** 5
    6 *
    -
    L
1 +
-
L

        4 ** 5
        -
        L
    6 *
    -
    L
1 +
-
L


        4 ** 5
        ------
          L
    6 *
    -
    L
1 +
-
L


        1024
        ----
         L
    6 *
    -
    L
1 +
-
L

        1024
    6 *
    -------
      L
1 +
-
L


    6144
    ----
     L
1 +
-
L

    6144
1 +
--------
  L


6145
----
 L
```

The procedure works for postfix operators as well.

Example: We'll check out the expression `1+2+3!`:

```
        3 !
1 + 2 +
-
L


        3 !
1 + 2 +
-----
  L


    3 !
3 +
-
L

    3 !
    -
    L
3 +
-
L

    3 !
    ---
    L
3 +
-
L

    6
    -
    L
3 +
-
L

9
-
L
```

The procedure works for prefix operators as well.

Example: We'll check out the example `~2+3`, where `~2 = 1/2`:

```
~ 2
-
L
    + 3


~ 2
---
L
    + 3


0.5
---
L
    + 3


0.5
---
L
    + 3
-------
  L



3.5
---
 L
```

#### e (or expression)

In the actual code that will be shown below, the process of contracting on a
given plane is carried out by a function `e`. `e` will be called at different
times by different operators, and each time `e` is called, it will be given an
argument to indicate at which plane it is operating. `e` will be called
initially with argument `0`, the lowest possible plane, to start the parsing
process. Due to the contracting property of `e`, the entire expression will
then be parsed and reduced to a single left value which will be returned by
this initial call of `e`.

Example: We will work through the evaluation of `1+2*3*4+5`. Please remember
that the end of the expression is represented by `end_token`. We will give `*`
value `10`, meaning expressions involving multiplications are on planes
associated with the number `10`, and `*` value `20`. Finally, we will denote by
`tokens` the sequence of tokens to be parsed, it's seen by all calls to `e`.
The variable `token`, which indicates the next token just obtained, is also
available globally to all calls to `e`, so that different calls to `e` always
starts at the correct position.

```
. call e(0)
A parsing happening in e(0) - tokens: "1+2*3*4+5"
  get the first token and put it to L
  L: 1
  token: +
         10 > 0 so + makes a call to e, e(10)
  pending operation A: 1 + e(10)

B parsing happening in e(10) - tokens: "2*3*4+5"
  get the first token and put it to L
  L: 2
  token: *
         20 > 10 so * makes a call to e, e(20)
  pending operation B: 2 * e(20)

C parsing happening in e(20) - tokens: "3*4+5"
  get the first token and put it to L
  L: 3
  token: *
         20 = 20 so L is returned immediately

-> pending operation B is resolved: 2 * 3 = 6
   parsing comes back to step B. L in B is now 6

B parsing happening in e(10) - tokens: "4+5"
  L: 6
  token: *
         20 > 10 so * makes a call to e, e(20)
  pending operation B: 6 * e(20)

D parsing happening in e(20) - tokens: "4+5"
  get the first token and put it to L
  L: 4
  token: +
         10 < 20 so L is returned immediately

-> pending operation B is resolved: 6 * 4 = 24
   parsing comes back to step B. L in B is now 24

B parsing happening in e(10) - tokens: "5"
  L: 24
  token: +
         10 = 10 so L is returned immediately

-> pending operation A is resolved: 1 + 24 = 25
   parsing comes back to step A. L in A is now 25

A parsing happening in e(0) - tokens: "5"
  L: 25
  token: +
         10 > 0 so + makes a call to e, e(10)
  pending operation A: 25 + e(10)

E parsing happening in e(10) - tokens: "5"
  get the first token and put it to L
  L: 5
  token: end_token
         L is returned immediately

-> pending operation A is resolved: 25 + 5 = 30
   parsing comes back to step A. L in A is now 30

A parsing happening in e(0) - tokens: ""
  L: 30
  token: end_token
             L is returned immediately
```

#### nud, lbp and led

Before showing the actual code for `e` (or `expression`) discussed above, we
will augment the operators with a method named `led` so that they can make
calls to `e` and demand pending operations. Each operator is associated to an
ordered plane and we call it `lbp`. Moreover, we will augment numbers with a
method named `nud` so as to be able to get their values. We'll list what the
names stand for at the end of the note.

```python
class literal_token:

    def __init__(self, value):
        self.value = int(value)

    def nud(self):
        return self.value


class operator_add_token:
    lbp = 10

    def led(self, left):
        return left + expression(10)


class operator_mul_token:
    lbp = 20

    def led(self, left):
        return left * expression(20)


class end_token:
    lbp = 0
```

## EVALUATING ADDITIONS AND MULTIPLICATIONS

At this point, we can show `expression` and `parse`. `parse` makes the first
call to `expression` to start parsing at plane `0`. What `rbp` stands for will
be listed at the end of the note.

```python
def expression(rbp=0):
    global token
    t = token
    token = next(tokens)
    left = t.nud()
    while rbp < token.lbp:
        t = token
        token = next(tokens)
        left = t.led(left)
    return left


def parse(program):
    global token, tokens
    tokens = tokenize(program)
    token = next(tokens)
    return expression()
```

Note the loop inside `expression`, it helps with the contraction work that
will go on on a plane. Note also the value `lbp=0` given to `end_token`, it
makes the program more uniform.

The crucial fact that makes `expression` work is that whenever `expression` is
called to operate on an expression, the first token it expects must always be a
number, and the next token must always be an operator.

The code,
[basic.py](https://github.com/tuan-ng/pratt-expression/blob/master/pratt/basic.py),
is now able to evaluate expressions that involve additions and multiplications
of numbers.

## ALL OTHER OPERATORS

The structure that has been set up can easily be extended to include other
infix operators such as `-` and `/`. We will now discuss how to add other
operators.

#### PREFIX OPERATORS

We'll add the inversion operator `~` to the code. `~` is a prefix operator. In
a sense, a prefix operator is strange, because the strategy of contracting
repeatedly to the left expects always an expression that has a number at the
begining followed by an operator. For example, in `1+2*3*4+5` each time
`expression` is called it encounters a number first followed by an operator.
In `~2+3` we don't have that form.

Because we actually call `nud` of a number to get its value

```python
class literal_token:

    def __init__(self, value):
        self.value = int(value)

    def nud(self):
        return self.value
```

we'll need to have `nud` inside a prefix operator as well, so that the
`expression` does not break:

```python
class operator_inv_token:

    def nud(self):
        // ...
```

To continue with the example `~2+3`, at the time of calling `nud` of `~`,
`~` is already consumed. We should use `expression` to parse the rest of the
expression for us. But since `~` should take precedences over `+` (and `*`),
and since we know the behavior of `expression` thoroughly, we should call
`expression` with a right argument so that it gets the correct right side
of `~` and then modifies the latter accordingly. Thus:

```python
class operator_inv_token:

    def nud(self):
        return 1 / expression(100)
```

We'll now make `-` and `+` work as prefix operators also. All we need to do is
to add a `nud` method to each token class:

```python
class operator_add_token:
    lbp = 10

    def nud(self):
        return expression(100)

    def led(self, left):
        return left + expression(10)


class operator_sub_token:
    lbp = 10

    def nud(self):
        return -expression(100)

    def led(self, left):
        return left - expression(10)
```

It might seem magic that an operator has two methods and that the methods will
be called exactly when they are needed by the general procedure in
`expression`. But in a correct expression, the position of an operator decides
whether it will be a prefix or an infix, and `expression` already takes into
account that fact. So it works!

#### POSTFIX OPERATORS

We'll now add `!`. This is almost like an infix operator, except that it does
not to call `expression` to get its right value. We want to give it a value
higher than other operators so that for example `2*5!` will give `240`.

```python
class operator_fac_token:
    lbp = 150

    def led(self, left):
        return math.factorial(left)
```

#### POWERS AND RIGHT ASSOCIATION

Now we add `**`. We start with tokenizing:

```python
token_pat = re.compile(r"\s*(?:(\d+)|(\*\*|.))")
```

Then we can proceed as usual. We want power to take precedence over most
other operators:

```python
class operator_pow_token:
    lbp = 30

    def led(self, left):
        return left ** expression(30)
```

If we evaluate `2**3**4` now, we'll have `4096`. This is consistent with the
general process of repeatedly contracting to the left (so the evaluation of
`2**3`first, then the evaluation of `8**4`). If we want right association, i.e.
to evaluate `3**4` first (`81`) and then `2**81`, we only need to make sure
that when a `**` is calling `expression`, the argument is a bit lower, so that
if another `**` is seen right after, the latter, whose `lbp` is `30`, takes
over precedence.

```python
class operator_pow_token:
    lbp = 30

    def led(self, left):
        return left ** expression(30-1)
```

Now if we evaluate `2**3**4` we will have right association.

## PARENTHESES

We have seen that when `expression` is called with a argument it will keep
parsing until it sees an operator having a plane value lower than the argument.
Inside a pair of parentheses parsing should starts right after the left
parenthesis at the lowest level, until a matching right parenthesis is seen. We
can take advantage of the fact that a left parenthesis can be seen as a prefix
operator, and a right one a postfix (except that it does not use its left value
and we just disard it). Thus

```python
def match(tok=None):
    global token
    if tok and tok != type(token):
        raise SyntaxError('Expected %s' % tok)
    token = next(tokens)

class operator_lparen_token:
    lbp = 0

    def nud(self):
        expr = expression()
        match(operator_rparen_token)
        return expr

class operator_rparen_token:
    lbp = 0
```

The code for the full parser is in
[full.py](https://github.com/tuan-ng/pratt-expression/blob/master/pratt/full.py).

## THE NAMES

`nud` stands for **null denotation**, and is used for prefix operators. `led`
stands for **left denotation** and is used for infix or postfix operators, i.e.
those that use left values and are waiting for right values. `lbp` stands for
**left binding power**, and `rbp` stands for **right binding power**.
