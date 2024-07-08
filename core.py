# Standard
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from inspect import FullArgSpec, getfullargspec
from typing import Annotated, Any, Callable, Dict, Type, get_origin

class ErrorType(Enum):
    ArgCount = 'Unexpected argument count'
    ArgMap = 'Argument map failed'
    ArgMiss = 'Argument missing'
    ArgVal = 'Argument validation failed'
    BadMetadata = 'Invalid annotation metadata - only Validator instances are allowed'

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

class Validator(ABC):
    """
    Base class for argument validators.
    """
    @abstractmethod
    def __call__(self, 
            arg_name: str,
            arg_type: Type,
            source_map: Dict[str, Any],
            target_map: Dict[str, Any]):
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

class Attr(str):
    def __call__(self, o):
        return getattr(o, self.name)
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f'Attr({repr(self.name)})'

class Map(Validator):
    """
    Map arguments from a source function spec according to the defined nodes.
    """
    def __call__(self, 
            arg_name: str,
            arg_type: Type, 
            source_map: Dict[str, Any],
            target_map: Dict[str, Any]):
        try:
            res = source_map
            for node in self.nodes:
                res = node(res) if callable(node) else res[node]
            target_map[arg_name] = res
        except Exception as e:
            if arg_name not in target_map:
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

def map_defaults(spec: FullArgSpec):
    d: Dict[str, Any] = {}
    if spec.defaults is not None:
        d.update(zip(spec.args[-len(spec.defaults):], spec.defaults))
    return d

def map_kwdefaults(spec: FullArgSpec):
    return spec.kwonlydefaults or {}

def get_arg_map(spec: FullArgSpec, args: tuple, kwargs: Dict[str, Any]):
    arg_map = {}
    # populate positional arguments
    spec_defaults = map_defaults(spec)
    for i, arg_name in enumerate(spec.args):
        if i < len(args):
            arg_map[arg_name] = args[i]
        elif arg_name in spec_defaults:
            arg_map[arg_name] = spec_defaults[arg_name]
        else:
            raise ValidecorError(ErrorType.ArgMiss, arg_name = arg_name)
    # check for *args
    if spec.varargs is not None:
        arg_map[spec.varargs] = args[min(len(args), len(spec.args)):]
    elif len(args) > len(spec.args):
        raise ValidecorError(ErrorType.ArgCount, message = 'Too many args')
    # populate keyword arguments
    spec_kwdefaults = map_kwdefaults(spec)
    for arg_name in spec.kwonlyargs:
        if arg_name in kwargs:
            arg_map[arg_name] = kwargs[arg_name]
        elif arg_name in spec_kwdefaults:
            arg_map[arg_name] = spec_kwdefaults[arg_name]
        else:
            raise ValidecorError(ErrorType.ArgMiss, arg_name = arg_name)
    # check for **kwargs
    if spec.varkw is not None:
        arg_map[spec.varkw] = { k: v for k, v in kwargs if k not in spec.kwonlyargs }
    elif len(kwargs) > len(spec.kwonlyargs):
        raise ValidecorError(ErrorType.ArgCount, message = 'Too many kwargs')
    return arg_map

def get_arg_def(spec: FullArgSpec):
    return map_defaults(spec) | map_kwdefaults(spec)

def validecor(source_spec: FullArgSpec = None):
    def decorator(fun):
        target_spec = getfullargspec(fun)
        @wraps(fun)
        def wrapper(*args, **kwargs):
            source_map = get_arg_map(target_spec if source_spec is None else source_spec, args, kwargs)
            target_map = source_map if source_spec is None else get_arg_def(target_spec)
            if target_spec.varargs is not None:
                target_map[target_spec.varargs] = tuple()
            if target_spec.varkw is not None:
                target_map[target_spec.varkw] = {}
            for arg_name, annotation in target_spec.annotations.items():
                if get_origin(annotation) is Annotated:
                    arg_type = annotation.__origin__
                    for metadata in annotation.__metadata__:
                        if isinstance(metadata, Validator):
                            metadata(arg_name, arg_type, source_map, target_map)
                        else:
                            raise ValidecorError(ErrorType.BadMetadata,
                                arg_name = arg_name,
                                metadata = metadata)
            if source_spec is not None:
                args = [ target_map[arg_name] for arg_name in target_spec.args ]
                if target_spec.varargs is not None:
                    args.extend(target_map[target_spec.varargs])
                kwargs = { arg_name: target_map[arg_name] for arg_name in target_spec.kwonlyargs }
                if target_spec.varkw is not None:
                    kwargs.update(target_map[target_spec.varkw])
            return fun(*args, **kwargs)
        return wrapper
    return decorator
