import re
import math


class literal_token:

    def __init__(self, value):
        self.value = int(value)

    def nud(self):
        return self.value


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


class operator_mul_token:
    lbp = 20

    def led(self, left):
        return left * expression(20)


class operator_div_token:
    lbp = 20

    def led(self, left):
        return left / expression(20)


class operator_inv_token:

    def nud(self):
        return 1 / expression(100)


class operator_fac_token:
    lbp = 150

    def led(self, left):
        return math.factorial(left)


class operator_pow_token:
    lbp = 30

    def led(self, left):
        return left ** expression(30-1)


class operator_lparen_token:
    lbp = 0

    def nud(self):
        expr = expression()
        match(operator_rparen_token)
        return expr


class operator_rparen_token:
    lbp = 0


class end_token:
    lbp = 0


token_pat = re.compile(r"\s*(?:(\d+)|(\*\*|.))")


def tokenize(program):
    for number, operator in token_pat.findall(program):
        if number:
            yield literal_token(number)
        elif operator == "+":
            yield operator_add_token()
        elif operator == "-":
            yield operator_sub_token()
        elif operator == "*":
            yield operator_mul_token()
        elif operator == "/":
            yield operator_div_token()
        elif operator == "~":
            yield operator_inv_token()
        elif operator == "!":
            yield operator_fac_token()
        elif operator == "**":
            yield operator_pow_token()
        elif operator == "(":
            yield operator_lparen_token()
        elif operator == ")":
            yield operator_rparen_token()
        else:
            raise SyntaxError("unknown operator")
    yield end_token()


def match(tok=None):
    global token
    if tok and tok != type(token):
        raise SyntaxError('Expected %s' % tok)
    token = next(tokens)


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
