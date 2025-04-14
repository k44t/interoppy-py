import importlib
import json
import sys
from dataclasses import dataclass
import inspect

"""
{my_function: [1, "zwei"]}
{my.module.my_function: [1, "zwei"]}

-->

{error: "the message"}
{success: {the: "result"}}
"""



class CallSyntaxError(Exception):
    def __str__(self):
        return """CallSyntaxError: a function call must be a json object that matches the following pattern {module.function = ["one", True, 3]} or {module.function = {_: ["unnamed", "args"], arg1: "value", arg2: True, arg3: 3} }"""

class FunctionError(Exception):
    def __init__(self, module, function):
        self.module = module
        self.function = function


class FunctionDoesNotExistError(FunctionError): #pylint: disable=missing-class-docstring
    def __init__(self, module, function):
        super().__init__(module, function)

    def __str__(self):
        return f"FunctionDoesNotExistError: module {self.module} has no function {self.function}"

class NotAFunctionError(FunctionError): #pylint: disable=missing-class-docstring
    def __init__(self, module, function):
        super().__init__(module, function)

    def __str__(self):
        return f"NotAFunctionError: {self.function} in module {self.module} is not callable"



def find_handler():
    for frame_info in inspect.stack():
        frame = frame_info.frame
        # Check each local variable in the frame
        for obj in frame.f_locals.values():
            if isinstance(obj, Handler):
                return obj
    raise ValueError("find_handler must be called from within the listen function of a Handler")




def register_encoder(enc):
    """when called from within a Handler it will register the given encoder with the handler"""
    find_handler().encoder = enc


def stop():
    """when called from within a Handler it will stop the handler's listen loop"""
    find_handler().running = False



@dataclass
class Handler:

    encoder = None
    running = True

    def handle(self, o):
        if not isinstance(o, dict):
            raise CallSyntaxError()
        if not len(o) == 1:
            raise CallSyntaxError()
        fqdn = next(iter(o.keys()))
        try:
            modulen, fnn = fqdn.rsplit('.', 1)
        except:
            raise ValueError(f"no module given from which to execute function: {fqdn}")
        mod = importlib.import_module(modulen)
        try:
            fn = getattr(mod, fnn)
        except AttributeError as ex:
            raise FunctionDoesNotExistError(modulen, fnn) from ex
        if not callable(fn):
            raise NotAFunctionError(modulen, fnn)
        args = o[fqdn]
        if isinstance(args, list):
            return fn(*args)
        elif isinstance(args, dict):
            unnamed = args.pop("_", [])
            return fn(*unnamed, **args)
        else:
            raise CallSyntaxError()





    def listen(self, ins, outs):
        # buffer = ""
        decoder = json.JSONDecoder()
        self.running = True
        while self.running:
            chunk = ins.readline()
            if not chunk:
                break    # End of stream

            try:
                # Try to decode a JSON object from the buffer
                obj, index = decoder.raw_decode(chunk)
                try:
                    r = self.handle(obj)
                    if self.encoder is not None:
                        if callable(self.encoder):
                            r = json.dumps(self.encoder(r))
                        elif inspect.isclass(self.encoder):
                            r = json.dumps(r, cls=self.encoder)
                        else:
                            raise ValueError("encoder is neither callable nor a class that can be used by the json module")
                    else:
                        r = json.dumps(r)
                    outs.write(f'{{"success":{r}}}')
                    outs.write("\n")
                except BaseException as ex:
                    outs.write(json.dumps({'"error"': f"{ex}"}))
                    outs.write("\n")
                # buffer = buffer[index:].lstrip()    # Remove the parsed object from the buffer
            except json.JSONDecodeError as ex:
                # Check if the error is due to incomplete data                    
                # if "Expecting value" in str(ex) or "Unterminated string" in str(ex):
                outs.write(json.dumps({'"error"': f"{ex}"}))
                outs.write("\n")


def main():
    # print('''{"success":"started interoppy server"}''')
    Handler().listen(sys.stdin, sys.stdout)

if __name__ == "__main__":
    main()
