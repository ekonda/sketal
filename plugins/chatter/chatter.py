from handler.base_plugin import BasePlugin
from plugins.calculation.calculator import Calculator

from enum import Enum
import itertools
import random
import os
import re


class Type(Enum):
    Non = -1
    Eoe = 0
    Text = 1
    Inst = 2
    Name = 3


class Node:
    __slots__ = ("type", "subtype", "value")

    def __init__(self, t=Type.Non, v=""):
        self.type = t
        self.value = v


class ChatterPlugin(BasePlugin):
    __slots__ = ("subplugins", "instructions", "prefixes", "calculator")

    def __init__(self, prefixes=(""), instructions=None):
        """Answers with a specified in config file values.
        Requires: CalculatorPlugin"""

        super().__init__()

        self.calculator = Calculator()
        self.prefixes = prefixes

        self.instructions = {}
        self.setup_instructions()
        if instructions:
            self.instructions.update(instructions)

    def initiate(self):
        self.subplugins = []

        self.bot.logger.info("Loading scripts for ChatterPlugin...")

        for root, dirs, files in os.walk(self.get_path("scripts")):
            for f in files:
                result = self.read_plugin(root + os.sep + f)

                if result[0]:
                    self.bot.logger.info(f"Loading script `{f}` for ChatterPlugin... Successfull!")

                else:
                    self.bot.logger.error(f"Loading script `{f}` for ChatterPlugin... Error: \"{result[1]}\"")

    async def check_message(self, msg):
        return not msg.is_out

    async def process_message(self, msg):
        skiptoeoe = False
        stmscheck = True
        skiptoerr = False

        result = False

        for subplugin in self.subplugins:
            i = 0

            while i < len(subplugin):
                node = subplugin[i]
                node_pr = subplugin[i - 1] if i > 0 else None

                if skiptoeoe and node.type != Type.Eoe:
                    pass

                elif node.type == Type.Inst and node.value == "->":
                    stmscheck = False

                elif node.type == Type.Eoe:
                    stmscheck = True
                    skiptoeoe = False
                    skiptoerr = False

                elif node_pr and node_pr.type == Type.Inst and (not skiptoerr or node_pr.value == "f"):
                    try:
                        if not await self.instructions[node_pr.value](msg, node.value, msg.text):
                            if not stmscheck:
                                result = True

                            skiptoeoe = True
                    except ValueError:
                        skiptoerr = True

                i += 1

        return result

    def setup_instructions(self):
        def gen_regexp(s):
            return r"(^|\?|!|\.|,|:|;|-|\s|\n)" + re.escape(s) +  r"($|\?|!|\.|,|:|;|-|\s|\n)"

        def get_variables(msg):
            variables = {"text": msg.text, "arg0": msg.text}
            for i, arg in enumerate(msg.text.split()):
                variables[f"arg{i + 1}"] = arg
                variables[f"a{i + 1}"] = arg

            return variables

        def process_value(msg, value):
            variables = get_variables(msg)

            result = ""
            token = ""
            ch_pr = None

            i = 0
            while i < len(value):
                if value[i] == "{":
                    if value[i + 1] == "{":
                        result += "{"
                        i += 1

                    else:
                        token += "("

                elif value[i] == "}":
                    if i + 1 < len(value) and value[i + 1] == "}":
                        result += "}"
                        i += 1

                    else:
                        result += str(self.calculator.calculate(token + ")", **variables))
                        token = ""

                elif token:
                    token += value[i]

                else:
                    result += value[i]

                i += 1

            return result

        # read
        async def cw(msg, value, text):
            value = value.lower()

            return re.search(gen_regexp(value), text.lower()) is not None

        async def CW(msg, value, text):
            return re.search(gen_regexp(value), text) is not None

        async def pw(msg, value, text):
            value = value.lower()

            return any(re.search(gen_regexp(f"{p}{value}"), text.lower()) is not None for p in self.prefixes)

        async def PW(msg, value, text):
            return any(re.search(gen_regexp(f"{p}{value}"), text) is not None for p in self.prefixes)

        async def e(msg, value, text):
            return value.lower() == text.lower()

        async def E(msg, value, text):
            return value == text

        self.instructions["cw"] = cw
        self.instructions["CW"] = CW
        self.instructions["pw"] = pw
        self.instructions["PW"] = PW
        self.instructions["e"] = e
        self.instructions["E"] = E

        # write
        async def a(msg, value, text):
            await msg.answer(process_value(msg, value))

            return False

        async def r(msg, value, text):
            if random.random() < .5:
                await msg.answer(process_value(msg, value))

                return False

            return True

        async def sr(msg, value, text):
            if random.random() < .25:
                await msg.answer(process_value(msg, value))

                return False

            return True

        async def br(msg, value, text):
            if random.random() < .75:
                await msg.answer(process_value(msg, value))

                return False

            return True

        async def f(msg, value, text):
            await msg.answer(value)

            return False

        async def do_nothing(msg, value, text):
            return True

        self.instructions["a"] = a
        self.instructions["r"] = r
        self.instructions["sr"] = sr
        self.instructions["br"] = br
        self.instructions["f"] = f
        self.instructions["->"] = do_nothing

    def print_plugins(self):
        newname = True

        for subplugin in self.subplugins:
            for n in subplugin:
                if newname:
                    print("-" * len(str(n.type) + ": " + str(n.value)))
                    newname = False

                print(str(n.type) + ": " + str(n.value))

    def read_plugin(self, path):
        plugin = [Node(Type.Name, path.split(os.sep)[-1]), Node()]
        token = ""
        inside = False
        comment = False

        def add_node(type=Type.Non):
            plugin.append(Node(type))

        with open(path) as cont:
            for no, li in enumerate(cont):
                pr_ch = None
                for cno, ch in enumerate(li):
                    node = plugin[-1]

                    if comment:
                        if ch == "#":
                            comment = False

                        continue

                    else:
                        if ch == "#" and not inside:
                            comment = True
                            continue

                    if ch == ";" and not inside:
                        node.type = Type.Eoe
                        add_node()

                    elif ch == '"' and pr_ch != '\\':
                        add_node()
                        inside = not inside

                    elif inside:
                        node.value += ch
                        node.type = Type.Text

                    elif node.value == "->":
                        add_node()

                    elif ch not in (" ", "\n", ","):
                        node.value += ch
                        node.type = Type.Inst

                    pr_ch = ch

        if plugin[-1].type == Type.Non and not inside and not comment:
            plugin[-1].type = Type.Eoe

        else:
            return False, f"Unexpected end of file"

        i = 0
        while i < len(plugin):
            node = plugin[i]

            if node.type == Type.Inst and node.value not in self.instructions:
                return False, f"Unknown instruction: {node.value}"

            if i > 0:
                node_pr = plugin[i - 1]
            else:
                node_pr = None

            if node_pr is not None:
                if node_pr.type == node.type == Type.Eoe:
                    plugin.pop(i)
                    continue

                if node.type == Type.Text and node_pr.type != Type.Inst:
                    return False, f"Wrong order, missing instruction for text: {node.value}"

            i += 1

        self.subplugins.append(plugin)

        return True, "OK"
