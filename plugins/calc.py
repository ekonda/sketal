import hues
import math

from plugin_system import Plugin

plugin = Plugin("Калькулятор",
                usage=["посчитать [выражение] - посчитать результат с помощью калькулятора",
                       "посчитать помощь - показать доступные операторы"])


class Function:
    __slots__ = ["sign", "function", "priority", "arguments", "description"]

    def __init__(self, sign, function, description, arguments, priority):
        self.sign = sign
        self.function = function
        self.arguments = arguments
        self.priority = priority
        self.description = description

    async def __call__(self, *args):
        return self.function(*args)

    def __repr__(self):
        return self.sign


def fix_error(x):
    err = 2e-16

    if - err < x < err:
        return 0

    if math.pi - err < x < math.pi + err:
        return math.pi

    if 0.5 - err < x < 0.5 + err:
        return 0.5

    if 1 - err < x < 1 + err:
        return 1

    return x


async def process(Q, W):
    action = W.pop()

    if not action.function:
        return True

    try:

        if action.arguments == 1:
            a = Q.pop()

            Q.append(await action(a))

        elif action.arguments == 2:
            b = Q.pop()
            a = Q.pop()

            Q.append(await action(a, b))

        return True

    except (TypeError, ValueError):
        return None


async def is_float(x):
    try:
        float(x)
    except ValueError:
        return False

    if "+" in x or "-" in x:
        return False

    return True


async def do_bracket(Q, W):
    while W and W[-1] != "(":
        if await process(Q, W) is None:
            return False

    return True


@plugin.on_command('посчитай', 'посчитать')
async def calc(msg, args):
    if not args:
        return await msg.answer("Нечего считать! Пожалуйста, укажите выражение!")

    if args[0].lower() == "помощь":
        result = ""

        for k, v in FUNCTIONS.items():
            temp = "🔷 \"" + v.sign + "\" - " + v.description + "\n\n"

            if len(result) + len(temp) >= 550:
                await msg.answer(result)
                result = ""

            result += temp

        return await msg.answer(result)

    exp = "(" + " ".join(args) + ")"

    Q = []  # Operands
    W = []  # Operators

    current_exp = ""
    prev_type = ""
    close_bracket = 0

    for i in range(len(exp)):
        if exp[i] == " ":
            continue

        if current_exp == "pi":
            Q.append(math.pi)

            prev_type = "numb"
            current_exp = ""

        elif await is_float(current_exp) and not await is_float(exp[i]) and not exp[i] == ".":
            Q.append(float(current_exp))

            prev_type = "numb"
            current_exp = ""

        if prev_type == "numb":
            while close_bracket:
                if not await do_bracket(Q, W):
                    return await msg.answer("Ошибка в разборе выражения!")

                close_bracket -= 1

        current_exp += exp[i]

        if current_exp in FUNCTIONS:
            if prev_type is not "numb" and prev_type not in ")":
                W.append(FUNCTIONS["("])
                close_bracket += 1

                if current_exp in "-+":
                    Q.append(0)

            if current_exp == ")":
                if not await do_bracket(Q, W):
                    return await msg.answer("Ошибка в разборе выражения!")

            else:
                while W and 0 <= W[-1].priority <= FUNCTIONS[current_exp].priority:
                    if await process(Q, W) is None:
                        return await msg.answer("Ошибка в разборе выражения!")

                W.append(FUNCTIONS[current_exp])

            prev_type = current_exp
            current_exp = ""


    if len(Q) != 1:
        return await msg.answer("Ошибка в разборе выражения!")

    else:
        return await msg.answer(f"Ответ: {Q.pop()}")

FUNCTIONS = []

# Functions(2 operands):
FUNCTIONS.append(Function(sign="+",
                          function=lambda x, y: x + y,
                          description="Сложение (x + y, 5 + 2 = 7)",
                          arguments=2,
                          priority=3))

FUNCTIONS.append(Function(sign="-",
                          function=lambda x, y: x - y,
                          description="Вычитание (x - y, 5 - 2 = 3)",
                          arguments=2,
                          priority=3))

FUNCTIONS.append(Function(sign="*",
                          function=lambda x, y: x * y,
                          description="Умножение (x * y, 5 * 2 = 10)",
                          arguments=2,
                          priority=2))

FUNCTIONS.append(Function(sign="/",
                          function=lambda x, y: x / y,
                          description="Деление (x * y, 5 / 2 = 2.5)",
                          arguments=2,
                          priority=2))

FUNCTIONS.append(Function(sign="mod",
                          function=lambda x, y: x % y,
                          description="Остаток деления (x mod y, 5 mod 2 = 1)",
                          arguments=2,
                          priority=2))

FUNCTIONS.append(Function(sign="div",
                          function=lambda x, y: x // y,
                          description="Целочисленное деление (x div y, 5 div 2 = 2)",
                          arguments=2,
                          priority=2))

FUNCTIONS.append(Function(sign="^",
                          function=lambda x, y: x ** y,
                          description="Возведение выражения x в степень y(x ^ y, 3 ^ 2 = 9)",
                          arguments=2,
                          priority=1))

#
# Functions 1 operand
FUNCTIONS.append(Function(sign="sin",
                          function=lambda x: fix_error(math.sin(x)),
                          description="Синус угла в радианах (sin x, sin (pi / 6) = 0.5)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="cos",
                          function=lambda x: fix_error(math.cos(x)),
                          description="Косинус угла в радианах (cos x, cos (pi / 3) = 0.5)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="tg",
                          function=lambda x: fix_error(math.tan(x)),
                          description="Тангенс угла в радианах (tg x, tg (pi / 4) = 1)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="ctg",
                          function=lambda x: fix_error(1 / math.tan(x)),
                          description="Косинус угла в радианах (ctg x, ctg (pi / 4) = 1)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="arcsin",
                          function=lambda x: fix_error(math.asin(x)),
                          description="Арксинус в радианах (arcsin x, arcsin 0.5 = 0.52...)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="arccos",
                          function=lambda x: fix_error(math.acos(x)),
                          description="Арккосинус в радианах (arccos x, arccos 0.5 = 1.04...)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="arctg",
                          function=lambda x: fix_error(math.atan(x)),
                          description="Тангенс угла в радианах (arctg x, arctg 0.5 = 0.46...)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="arcctg",
                          function=lambda x: fix_error(math.pi / 2 - math.atan(x)),
                          description="Косинус угла в радианах (arcctg x, arcctg 0.5 = 1.10...)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="sqrt",
                          function=lambda x: math.sqrt(x),
                          description="Корень из выражения (sqrt x, sqrt 9 = 3)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function(sign="abs",
                          function=lambda x: math.fabs(x),
                          description="Модуль выражения (abs x, abs -9 = 9)",
                          arguments=1,
                          priority=1))

FUNCTIONS.append(Function("(", None, "Скобочка для приоритета", 0, -1))
FUNCTIONS.append(Function(")", None, "Скобочка для приоритета", 0, 50))

FUNCTIONS = {func.sign: func for func in FUNCTIONS}