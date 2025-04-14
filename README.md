Python implementation of interoppy. 

The basic usage of interoppy is to start it as a subprocess from some other programming language, and then send json objects representing function calls and interpret the results which are also json objects:

```
{"my.module.my-function": ["argument 1", "argument 2", Three]}
```

Please note that linebreak characters are not allowed in the json source, so don't use a pretty printer when sending json to interoppy.

Or, if you have named arguments, you can pass the unnamed arguments under the key `_`:


```
{"my.module.my-function": {"_": ["argument 1", "argument 2"], "named_arg1": true, "named_arg2": 2.15}
```

The arguments of your function must either be simple datatypes (numbers, bools, string or dicts). If you need anything more complex, you have to write an additional wrapper function (on the python side) that can take those simple datatypes and create python class instances from them for example.

The output of `my-function` must either be a simple datatype that `json.dumps` can serialize, or you must provide an encoder. Typically you would do that by means of some init function:

```
# contents of `my.module`

from interoppy import register_encoder

def encoding_function(my_object):
  # dict's are what json.dumps can turn into json objects
  return {"property_name", my_object.json_serializeable_property}

def init_interoppy():
  register_encoder(encoding_function)
```

For more complex setup you might also create an encoder class that conforms to what can be passed to the `cls` argument of `json.dumps` (`json.dumps(my_object, cls=MyEncoderClass`). Which you then register within your init function:

```
def init_interoppy():
  register_encoder(MyEncoderClass)
```

And then on the client side, you need to tell interoppy to call that init function by sending the following json object to its input stream:

```
{"my.module.init_interoppy":[]}
```

Interoppy only consists of less than 300 lines of code. For anything else (such as using the Handler directly) simply consult the source code.



To test what interoppy will do, you can also start interoppy manually and then manually send json objects to it:

```
python -m interoppy
{"succes":"started interoppy server"}
{"my.module.my_function":[]}
"whatever my_function returned"
```