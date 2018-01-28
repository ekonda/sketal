import unittest

try:
    import calculator
except ModuleNotFoundError:
    import plugins.content.calculation.calculator as calculator

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = calculator.Calculator()

    def test_tokenize(self):
        self.assertEqual(self.calculator.tokenized("1 + 1"), ["1", "+", "1"])
        self.assertEqual(self.calculator.tokenized("1 - (-1) + 1"), ["1", "-", "(", "-", "1", ")", "+", "1"])
        self.assertEqual(self.calculator.tokenized("123"), ["123"])
        self.assertEqual(self.calculator.tokenized("sqrt(8)"), ["sqrt", "(", "8", ")"])
        self.assertEqual(self.calculator.tokenized("12 * ( 3)"), ["12", "*", "(", "3", ")"])
        self.assertEqual(self.calculator.tokenized("12 * (-3)"), ["12", "*", "(", "-", "3", ")"])
        self.assertEqual(self.calculator.tokenized("1\n2"), ["1", "2"])
        self.assertEqual(self.calculator.tokenized("1\n 23 2"), ["1", "23", "2"])
        self.assertEqual(self.calculator.tokenized("1\n2 + 10 * 3"), ["1", "2", "+", "10", "*", "3"])
        self.assertEqual(self.calculator.tokenized("+ 10 * 3"), ["+", "10", "*", "3"])

    def test_infix_to_postfix(self):
        self.assertEqual(self.calculator.infix_to_postfixed("1 + 1"), ["1", "1", "+"])
        self.assertEqual(self.calculator.infix_to_postfixed("1 - 5 * 2"), ["1", "5", "2", "*", "-"])
        self.assertEqual(self.calculator.infix_to_postfixed("(1 - 5) * 2"), ["1", "5", "-", "2", "*"])
        self.assertEqual(self.calculator.infix_to_postfixed("12 * ( -3)"), ["12", "3", "unary -", "*"])
        self.assertEqual(self.calculator.infix_to_postfixed("1\n2"), ["1", "2"])
        self.assertEqual(self.calculator.infix_to_postfixed("sqrt (5-4)"), ["5", "4", "-", "unary sqrt"])
        self.assertEqual(self.calculator.infix_to_postfixed(["+", "10", "*", "3"]), ["10", "3", "*", "unary +"])

    def test_init(self):
        self.assertEqual(self.calculator.calculate("1 + 1"), 2)

    def test_unary(self):
        self.assertEqual(self.calculator.calculate("- 1 + 1"), 0)
        self.assertEqual(self.calculator.calculate("- 1 - 1 + (- 2)"), -4)
        self.assertEqual(self.calculator.calculate("+ 1"), 1)
        self.assertEqual(self.calculator.calculate("- 2 - 2"), -4)
        self.assertEqual(self.calculator.calculate("(- 2) - 2"), -4)
        self.assertEqual(self.calculator.calculate("sqrt (4) - 2"), 0)
        self.assertEqual(self.calculator.calculate("fact 4"), 2*3*4)

    def test_functions(self):
        self.assertEqual(self.calculator.calculate("pow(- 5 * 4, 1)"), -20)
        self.assertEqual(self.calculator.calculate("pow(2, 2)"), 4)
        self.assertEqual(self.calculator.calculate("log(8, 2)"), 3)
        self.assertEqual(self.calculator.calculate("log(64, 8)"), 2)
        self.assertEqual(self.calculator.calculate("(1, 2)"), (1, 2))

    def test_text(self):
        self.assertEqual(self.calculator.calculate("hey"), "hey")

    def test_variables_const(self):
        self.assertEqual(self.calculator.calculate("a", a=2), 2)
        self.assertEqual(self.calculator.calculate("a + b", a=2, b=3), 5)
        self.assertEqual(self.calculator.calculate("a + b - c", **{"a": 2, "c": 5, "b": 0}), -3)
        self.assertEqual(self.calculator.calculate("a / c", **{"a": 2, "c": 0, "b": 0}), float("inf"))
        self.assertEqual(self.calculator.calculate("5 + a", a=5), 10)

    def test_variables_callable(self):
        self.assertEqual(self.calculator.calculate("5 + a", a=lambda: 10), 15)

        class Test():
            def __init__(self, v=5):
                self.v = v

            def __str__(self):
                return str(self.v)

            def __call__(self):
                return self.v * 2

        self.assertEqual(self.calculator.calculate("-a", a=Test), -5)
        self.assertEqual(self.calculator.calculate("a", a=Test(4)), 8)

        test = Test(2)
        self.assertEqual(self.calculator.calculate("a", a=test), 4)
        test.v = 16
        self.assertEqual(self.calculator.calculate("a", a=test), 32)

    def test_operations(self):
        self.assertEqual(self.calculator.calculate("1 + 1"), 2)
        self.assertEqual(self.calculator.calculate("1 + 2"), 3)
        self.assertEqual(self.calculator.calculate("1 - 2"), -1)
        self.assertEqual(self.calculator.calculate("1 - 1"), 0)
        self.assertEqual(self.calculator.calculate("1 * 1"), 1)
        self.assertEqual(self.calculator.calculate("1 * 0"), 0)
        self.assertEqual(self.calculator.calculate("1 / 1"), 1)
        self.assertEqual(self.calculator.calculate("1 / 0"), float("inf"))
        self.assertEqual(self.calculator.calculate("0 / 1"), 0)

    def test_order(self):
        self.assertEqual(self.calculator.calculate("1 + 2 * 3"), 7)
        self.assertEqual(self.calculator.calculate("1 + 2 * (3 - 2)"), 3)
        self.assertEqual(self.calculator.calculate("2 ^ 2 * (3 - 1) / 2"), 4)
        self.assertEqual(self.calculator.calculate("1 + 2 * 3 - 4"), 3)
        self.assertEqual(self.calculator.calculate("(1 + 2) * (3 - (4 + 2 * 1))"), -9)

if __name__ == '__main__':
    unittest.main()
