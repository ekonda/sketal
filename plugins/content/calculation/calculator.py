def pr_iterator(array):
    pr = None

    for i in array:
        yield i, pr
        pr = i


def ex(ex):
    raise ex


import math


class Calculator():
    __slots__ = ("operations", "special")

    default_operations = {
        ",": (1, lambda x, y: (x, y)),
        "+": (3, lambda x, y: x + y),
        "-": (3, lambda x, y: x - y),
        "unary +": (3, lambda x: x),
        "unary -": (3, lambda x: -x),
        "*": (6, lambda x, y: x * y),
        "/": (6, lambda x, y: x / y if y != 0 else float("inf")),
        "^": (9, lambda x, y: x ** y),
        "unary sqrt": (9, lambda x: x ** 0.5 if x >= 0 else ex(ValueError("Square root of a negative number."))),

        "unary pow": (9, lambda x: x[0]**x[1]),
        "unary fact": (9, math.factorial),
        "unary log": (9, lambda x: (math.log(x) if x > 0 else ex(ValueError("Value x can't be zero for log!")))
                                    if len(x) == 1 or isinstance(x, (int, float))
                                    else math.log(x[0], x[1]) if x[0] > 0 and x[1] > 0 and x[1] != 1 else
                                    ex(ValueError("Values for can't be zero (and one for base) for log!"))),
    }

    default_variables = {"pi": 3.14159265359, "e": 2.71828182846}

    def __init__(self, operations=None):

        if operations is None:
            operations = self.default_operations

        if None in operations:
            operations.update(self.default_operations)

        self.operations = operations
        self.special = ["(", ")", ","]

    def unary_place(self, pr_token):
        return pr_token is None or pr_token == "(" or pr_token in self.operations

    @staticmethod
    def isfloat(v):
        try:
            float(str(v))
            return True
        except ValueError:
            return False

    def tokenized(self, expr, **variables):
        return list(self.tokenize(expr, **variables))

    def tokenize(self, expr, **variables):
        token = ""
        token_pr = None

        for s in expr:
            if s in (" ", "\n"):
                if token:
                    yield token
                    token_pr = token
                    token = ""

                continue

            if token and self.isfloat(token) and not self.isfloat(token + s):
                yield token
                token_pr = token
                token = ""

            token += s

            if token in self.operations or token in self.special or token in variables \
                    or (self.unary_place(token_pr) and f"unary {token}" in self.operations):
                yield token
                token_pr = token
                token = ""

        if token:
            yield token

    def infix_to_postfixed(self, expr, **variables):
        return list(self.infix_to_postfix(expr, **variables))

    def infix_to_postfix(self, expr, **variables):
        if isinstance(expr, (str, )):
            expr =  self.tokenize(expr, **variables)

        p = lambda x: self.operations.get(x, (0, 0))[0]

        stack = []

        top = lambda: stack[-1]

        for token, pr_token in pr_iterator(expr):
            if token == ")":
                while stack:
                    current_top = stack.pop(-1)

                    if current_top == "(": break

                    yield current_top

                else:
                    raise ValueError("Unbalanced brackets")

                continue

            if token == "(":
                stack.append(token)
                continue

            if self.unary_place(pr_token) and f"unary {token}" in self.operations:
                token = f"unary {token}"

            elif token not in self.operations:
                yield token
                continue

            while stack and p(top()) >= p(token):
                yield stack.pop(-1)

            stack.append(token)

        while stack:
            yield stack.pop(-1)

    def calculate_safe(self, expr, **variables):
        try:
            return True, self.calculate(expr, **variables)
        except ValueError:
            return False, 0

    @staticmethod
    def prepare_token(token):
        # You can just return `token` it will turn calculator to small programming language

        if isinstance(token, (int, float)):
            return token

        if isinstance(token, str):
            return float(token)

        if isinstance(token, (list, tuple)):
            return token

        return float(str(token))


    def calculate(self, expr, **variables):
        postfix = self.infix_to_postfix(expr, **variables)

        stack = []

        for token in postfix:
            if token not in self.operations:
                if token in variables:
                    if callable(variables[token]):
                        stack.append(variables[token]())
                    else:
                        stack.append(variables[token])
                else:
                    stack.append(token)

                continue

            if token.startswith("unary"):
                a = self.prepare_token(stack.pop(-1))

                stack.append(self.operations[token][1](a))

            else:
                a = self.prepare_token(stack.pop(-1))
                b = self.prepare_token(stack.pop(-1))

                stack.append(self.operations[token][1](b, a))

        if len(stack) > 1:
            raise ValueError("Unbalanced expression")

        return stack.pop(0)
