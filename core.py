# Standard
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from inspect import FullArgSpec, getfullargspec
from typing import Annotated, Any, Callable, Dict, Type, get_origin

class ErrorType(Enum):
    ArgMap = 'Argument map failed'
    ArgVal = 'Argument validation failed'
    BadAnnotation = 'Invalid annotation metadata'
    CustomSpec = 'Custom spec does not match actual arguments'

class ValidecorError(Exception):
    def __init__(self, err_type: ErrorType, **kwargs):
        super().__init__(err_type.value)
        self.type = err_type
        self.kwargs = kwargs
    def __repr__(self):
        return f'{self.type.value} (type: {self.type.name}' \
            + ''.join(f', {k}: {repr(v)}' for k, v in self.kwargs.items()) \
            + ')'
    def __str__(self):
        return repr(self)

class Attr(str):
    def __call__(self, o):
        return getattr(o, self.name)
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f'Attr({repr(self.name)})'

class Map:
    """
    Map arguments from a source function spec according to the defined nodes.
    """
    def __call__(self, 
            arg_name: str,
            arg_type: Type, 
            arg_map: Dict[str, Any],
            arg_def: Dict[str, Any]):
        try:
            res = arg_map
            for node in self.nodes:
                res = node(res) if callable(node) else res[node]
            return res
        except Exception as e:
            if arg_name in arg_def:
                return arg_def[arg_name]
            raise ValidecorError(ErrorType.ArgMap, 
                arg_name = arg_name,
                arg_type = arg_type,
                arg_map = self,
                last_node = node,
                sub_error = e)
    def __init__(self, *nodes: int | str | Callable):
        self.nodes = nodes
    def __repr__(self):
        return f'Map({ ",".join(repr(node) for node in self.nodes) })'

class Validator(ABC):
    """
    Base class for argument validators.
    """
    @abstractmethod
    def __call__(self, arg_name: str, arg_type: Type, arg, arg_map: Dict[str, Any]):
        """
        Run-time validation of function arguments.
        
        Raise an appropriate exception on invalid input.
        
        @arg_name: Defined argument name.
        @arg_type: Defined argument type.
        @arg: The actual run-time argument.
        @arg_map: Argument map according to declared source spec.
        """
        pass
    @abstractmethod
    def __repr__(self):
        pass

def get_arg_map(spec: FullArgSpec, args: tuple, kwargs: Dict[str, Any]):
    arg_map = kwargs.copy()
    for arg_name, arg_value in zip(spec.args, args):
        arg_map[arg_name] = arg_value
    defaults = get_arg_def(spec)
    for arg_name, arg_default in defaults.items():
        if arg_name not in arg_map:
            arg_map[arg_name] = arg_default
    return arg_map

def get_arg_def(spec: FullArgSpec):
    arg_def: Dict[str, Any] = {}
    if spec.kwonlydefaults is not None:
        arg_def.update(spec.kwonlydefaults)
    if spec.defaults is not None:
        arg_def.update(zip(spec.args[-len(spec.defaults):], spec.defaults))
    return arg_def

def validecor(source_spec: FullArgSpec = None):
    def decorator(fun):
        target_spec = getfullargspec(fun)
        @wraps(fun)
        def wrapper(*args, **kwargs):
            arg_map = get_arg_map(source_spec or target_spec, args, kwargs)
            arg_def = get_arg_def(target_spec)
            for arg_name, annotation in target_spec.annotations.items():
                if get_origin(annotation) is Annotated:
                    arg_type = annotation.__origin__
                    arg_value: Any
                    arg_orig = True
                    for metadata in annotation.__metadata__:
                        if isinstance(metadata, Map):
                            arg_value = metadata(arg_name, arg_type, arg_map, arg_def)
                            arg_orig = False
                        elif isinstance(metadata, Validator):
                            if arg_orig:
                                arg_value = arg_map[arg_name]
                            metadata(arg_name, arg_type, arg_value, arg_map)
                        else:
                            raise ValidecorError(ErrorType.BadAnnotation, metadata = metadata)
            return fun(*args, **kwargs)
        return wrapper
    return decorator
