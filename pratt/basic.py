import re


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


token_pat = re.compile(r"\s*(?:(\d+)|(.))")


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
