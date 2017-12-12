from handler.base_plugin import BasePlugin
from plugins.calculation.calculator import Calculator

from enum import Enum
import itertools
import random
import copy
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
                if f.startswith("_"):
                    continue

                result = self.read_plugin(root + os.sep + f)

                if result[0]:
                    self.bot.logger.info(f"Loading script `{f}` for ChatterPlugin... Successfull!")

                else:
                    self.bot.logger.error(f"Loading script `{f}` for ChatterPlugin... Error: \"{result[1]}\"")

    async def check_message(self, msg):
        return not msg.is_out and not msg.is_forwarded

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
                        if not await self.instructions[node_pr.value](msg, node.value, msg.full_text):
                            if not stmscheck:
                                result = True

                            skiptoeoe = True
                    except ValueError:
                        skiptoerr = True

                i += 1

        return result

    def setup_instructions(self):
        memory = [""] * 16

        def gen_regexp(s):
            return r"(^|\?|!|\.|,|:|;|-|\s|\n)" + re.escape(s) +  r"($|\?|!|\.|,|:|;|-|\s|\n)"

        def get_variables(msg):
            variables = {"text": msg.text, "arg0": msg.text}

            for i, arg in enumerate(msg.text.split()):
                variables[f"arg{i + 1}"] = arg
                variables[f"a{i + 1}"] = arg

            for i in range(len(memory)):
                def wrapper(i):
                    d = copy.copy(i)

                    def g():
                        return memory[d]

                    return g

                variables[f"v{i + 1}"] = wrapper(i)

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
            value = process_value(msg, value).lower()

            return re.search(gen_regexp(value), text.lower()) is not None

        async def CW(msg, value, text):
            value =  process_value(msg, value)

            return re.search(gen_regexp(value), text) is not None

        async def pw(msg, value, text):
            value =  process_value(msg, value).lower()

            return any(re.search(gen_regexp(f"{p}{value}"), text.lower()) is not None for p in self.prefixes)

        async def PW(msg, value, text):
            value =  process_value(msg, value)

            return any(re.search(gen_regexp(f"{p}{value}"), text) is not None for p in self.prefixes)

        async def e(msg, value, text):
            value =  process_value(msg, value)

            return value.lower() == text.lower()

        async def E(msg, value, text):
            value =  process_value(msg, value)

            return value == text

        self.instructions["cw"] = cw
        self.instructions["CW"] = CW
        self.instructions["pw"] = pw
        self.instructions["PW"] = PW
        self.instructions["e"] = e
        self.instructions["E"] = E

        for k, v in list(self.instructions.items()):
            async def temp(*args, **kwargs):
                return not (await v(*args, **kwargs))

            self.instructions[f"n{k}"] = temp

        # variables
        def wrapper(num):
            d = copy.copy(num)

            async def v(msg, value, text):
                memory[d] = process_value(msg, value)

                return True

            return v

        for i in range(len(memory)):
            self.instructions[f"v{i + 1}"] = wrapper(i)

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
        escaped = False

        def add_node(type=Type.Non):
            plugin.append(Node(type))

        with open(path) as cont:
            for no, li in enumerate(cont):
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

                    if inside:
                        if escaped or ch not in ("\\", '"'):
                            node.value += ch
                            node.type = Type.Text
                            escaped = False

                        elif ch == '"':
                            add_node()
                            inside = False

                        elif ch == '\\':
                            escaped = True

                    elif ch == ";":
                        node.type = Type.Eoe
                        add_node()

                    elif ch == '"':
                        add_node()
                        inside = True

                    elif node.value == "->":
                        add_node()

                    elif ch not in (" ", "\n", ","):
                        node.value += ch
                        node.type = Type.Inst

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
