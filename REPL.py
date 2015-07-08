# A read-eval-print-loop for MCEdit.

# Created to allow programmers to quickly experiment with code without worrying
# about destroying their world thanks to MCEdit supplying the ability to quickly
# view and undo changes.

# If there are any issues or enhancement requests please submit a bug report at:
# https://github.com/qqii/mcedit-filters
import __future__
import sys
import traceback
import pymclevel

# coedop.py

_features = [getattr(__future__, fname)
             for fname in __future__.all_feature_names]

PyCF_DONT_IMPLY_DEDENT = 0x200

def _maybe_compile(compiler, source, filename, symbol):
    for line in source.split("\n"):
        line = line.strip()
        if line and line[0] != '#':
            break
    else:
        if symbol != "eval":
            source = "pass"

    err = err1 = err2 = None
    code = code1 = code2 = None

    try:
        code = compiler(source, filename, symbol)
    except SyntaxError, err:
        pass

    try:
        code1 = compiler(source + "\n", filename, symbol)
    except SyntaxError, err1:
        pass

    try:
        code2 = compiler(source + "\n\n", filename, symbol)
    except SyntaxError, err2:
        pass

    if code:
        return code
    if not code1 and repr(err1) == repr(err2):
        raise SyntaxError, err1

def _compile(source, filename, symbol):
    return compile(source, filename, symbol, PyCF_DONT_IMPLY_DEDENT)

def compile_command(source, filename="<input>", symbol="single"):
    return _maybe_compile(_compile, source, filename, symbol)

class Compile:
    def __init__(self):
        self.flags = PyCF_DONT_IMPLY_DEDENT

    def __call__(self, source, filename, symbol):
        codeob = compile(source, filename, symbol, self.flags, 1)
        for feature in _features:
            if codeob.co_flags & feature.compiler_flag:
                self.flags |= feature.compiler_flag
        return codeob

class CommandCompiler:
    def __init__(self,):
        self.compiler = Compile()

    def __call__(self, source, filename="<input>", symbol="single"):
        return _maybe_compile(self.compiler, source, filename, symbol)

# code.py

def softspace(file, newvalue):
    oldvalue = 0
    try:
        oldvalue = file.softspace
    except AttributeError:
        pass
    try:
        file.softspace = newvalue
    except (AttributeError, TypeError):
        pass
    return oldvalue

class InteractiveInterpreter:

    def __init__(self, locals=None):
        if locals is None:
            locals = {"__name__": "__console__", "__doc__": None}
        self.locals = locals
        self.compile = CommandCompiler()

    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False

        if code is None:
            return True

        self.runcode(code)
        return False

    def runcode(self, code):
        try:
            exec code in self.locals
        except SystemExit:
            raise
        except:
            self.showtraceback()
        else:
            if softspace(sys.stdout, 0):
                print

    def showsyntaxerror(self, filename=None):
        type, value, sys.last_traceback = sys.exc_info()
        sys.last_type = type
        sys.last_value = value
        if filename and type is SyntaxError:
            try:
                msg, (dummy_filename, lineno, offset, line) = value
            except:
                pass
            else:
                value = SyntaxError(msg, (filename, lineno, offset, line))
                sys.last_value = value
        list = traceback.format_exception_only(type, value)
        map(self.write, list)

    def showtraceback(self):
        try:
            type, value, tb = sys.exc_info()
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            tblist = traceback.extract_tb(tb)
            del tblist[:1]
            list = traceback.format_list(tblist)
            if list:
                list.insert(0, "Traceback (most recent call last):\n")
            list[len(list):] = traceback.format_exception_only(type, value)
        finally:
            tblist = tb = None
        map(self.write, list)

    def write(self, data):
        sys.stderr.write(data)

class InteractiveConsole(InteractiveInterpreter):

    def __init__(self, locals=None, filename="<console>"):
        InteractiveInterpreter.__init__(self, locals)
        self.filename = filename
        self.resetbuffer()

    def resetbuffer(self):
        self.buffer = []

    def interact(self, banner=None):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write("%s\n" % str(banner))
        more = 0
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                try:
                    line = self.raw_input(prompt)
                    encoding = getattr(sys.stdin, "encoding", None)
                    if encoding and not isinstance(line, unicode):
                        line = line.decode(encoding)
                    if line.lower().startswith("exit"):
                        self.write("Exiting...\n")
                        break
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0

    def push(self, line):
        self.buffer.append(line)
        source = "\n".join(self.buffer)
        more = self.runsource(source, self.filename)
        if not more:
            self.resetbuffer()
        return more

    def raw_input(self, prompt=""):
        return raw_input(prompt)


def interact(banner=None, readfunc=None, local=None):
    console = InteractiveConsole(local)
    if readfunc is not None:
        console.raw_input = readfunc
    else:
        try:
            import readline
        except ImportError:
            pass
    console.interact(banner)

# REPL.py

displayName = 'Read Evaluate Print Loop'

inputs = (
    ('Include Globals', False),
)

def perform(level, box, options):
    vars = {"pymclevel": pymclevel}
    vars.update(locals())
    if options["Include Globals"]:
        vars.update(globals())

    shell = InteractiveConsole(vars)
    banner = (
        "\n"
        "This is a read-eval-print-loop for MCEdit. Type \"exit\" to exit.\n\n"
        "The variables you have access to are:\n"
        "box - the bounding box of your selection.\n"
        "level - the world you have currently loaded in mcedit\n"
        "pymclevel - the pymclevel module for editing minecraft worlds and data\n\n"
        "Please note that it is normal for the mcedit gui window to become unresponsive, "
        "it will return to normal once you exit repl mode."
        )
    shell.interact(banner=banner)
