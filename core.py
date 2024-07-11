# Standard
from abc import ABC, abstractmethod
from functools import wraps
from inspect import FullArgSpec, getfullargspec
from typing import Annotated, Any, Callable, Dict, Type, get_origin

class Validator(ABC):
    """
    Abstract Base Class for argument validators.
    """
    annotated_name: str
    annotated_type: Type
    cache: Dict[tuple, Any]
    @abstractmethod
    def __desc__(self) -> str:
        pass
    @abstractmethod
    def __repr__(self) -> str:
        pass
    @property
    def description(self) -> str:
        return self.__desc__()

class ExtendedValidator(Validator, ABC):
    @abstractmethod
    def __call__(self, 
            source_map: Dict[str, Any],
            target_map: Dict[str, Any]):
        """
        Extended run-time validation of function arguments.
        
        @source_map: Dictionary of source arg names to values.
        @target_map: Dictionary of target arg names to values.

        Raise an appropriate exception on invalid input.
        """
        pass

class SimpleValidator(Validator, ABC):
    @abstractmethod
    def __call__(self, arg):
        """
        Simple run-time validation of function arguments.
        
        @arg: The argument value to validate.

        Raise an appropriate exception on invalid input.
        """
        pass

class Attr(str):
    def __call__(self, o):
        return getattr(o, self.name)
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f'Attr({repx(self.name)})'

class Map(ExtendedValidator):
    """
    Map arguments from a source function spec according to the defined nodes.
    
    @hidden - 
    """
    def __call__(self, 
            source_map: Dict[str, Any],
            target_map: Dict[str, Any]):
        try:
            arg = source_map
            nodes = tuple()
            for i, node in enumerate(self.nodes):
                nodes += (node, )
                arg = self.cache.get(nodes, node(arg) if callable(node) else arg[node])
                self.cache[nodes] = arg
            target_map[self.annotated_name] = arg
        except Exception as e:
            if self.annotated_name not in target_map: # no default value
                raise Exception(f'Failed map node #{i}: {repx(node)}', e)
    def __desc__(self):
        return f'Argument must be mapped from: {self.format_nodes()}'
    def __init__(self, *nodes: int | str | Callable, hidden: int = 0):
        self.nodes = nodes
        self.hidden = hidden
    def __repr__(self):
        return f'Map({self.format_nodes()})'
    def format_nodes(self):
        return ",".join(repx(node) for i, node in enumerate(self.nodes) if i >= self.hidden)

CONTINUE = object()

def repx(obj):
    if callable(obj):
        return obj.__name__ if hasattr(obj, '__name__') else type(obj).__name__
    return repr(obj)

def default_log_hook(*__args__, **__kwargs__): return CONTINUE

def default_val_hook(__err__: Exception, __validecor__: Validator): raise

def default_err_hook(__err__: Exception, *__args__, **__kwargs__): raise

def default_map_hook(res): return res

def get_arg_map(spec: FullArgSpec, args: tuple, kwargs: Dict[str, Any]):
    arg_map = dict(zip(spec.args, args))
    if (i := len(args) - len(spec.args)) < 0:
        arg_map.update(zip(spec.args[i:], spec.defaults[i:]))
    if spec.varargs is not None:
        arg_map[spec.varargs] = args[len(spec.args):]
    arg_map.update((k, kwargs.get(k, spec.kwonlydefaults[k])) for k in spec.kwonlyargs)
    if spec.varkw is not None:
        arg_map[spec.varkw] = { k: kwargs[k] for k in kwargs if k not in arg_map }
    return arg_map

def get_arg_def(spec: FullArgSpec):
    arg_def = {}
    if spec.defaults is not None:
        arg_def.update(zip(spec.args[::-1], spec.defaults[::-1]))
    if spec.kwonlydefaults is not None:
        arg_def.update(spec.kwonlydefaults)
    if spec.varargs is not None:
        arg_def[spec.varargs] = tuple()
    if spec.varkw is not None:
        arg_def[spec.varkw] = {}
    return arg_def

def validecor(
        source_fun: Callable = None,
        pre_hook: Callable = default_log_hook,
        val_hook: Callable = default_val_hook,
        err_hook: Callable = default_err_hook,
        map_hook: Callable = default_map_hook):
    """
    ValiDecor is a decorator for annotating validations on function inputs.

    ValiDecor can also map input arguments from a source function and execute
    the target arguments on the decorated function.

    `source_fun(...):` This function will not be called but it is used to
        obtain the specification of the input arguments. The arguments are then
        mapped to the target function using the special validator Map.

    Use callback functions to intecept ValiDecor events.
    When a hook is called its return value will immediately be 
    returned to the user and no other code will be executed.
    The pre hook will only cause a return if it returns not None,
    otherwise the validation process continues.

    `pre_hook(*args, **kwargs):` Invoked with the source arguments 
        before any validations and intended for logging purposes.
        Default: no action.

    `val_hook(Exception, ValiDecor):` Invoked on validation errors.
        Includes the validation exception and the corresponding 
        ValiDecor class. The first argument of the Exception is 
        intended for the end-user, and the rest for debugging.
        Default: raise Exception.

    `err_hook(Exception, *args, **kwargs):` - Capture any exceptions
        while executing the main target function (includes the
        target arguments), and return a nice response.
        Default: raise Exception.

    `map_hook(response):` - Callback to perform any post processing 
        on the response and return a modified result.
        Default: return the response unmodified.
    """
    def decorator(target_fun):
        source_spec = getfullargspec(source_fun) if source_fun is not None else None
        target_spec = getfullargspec(target_fun)
        @wraps(target_fun)
        def wrapper(*source_args, **source_kwargs):
            if (res := pre_hook(*source_args, **source_kwargs)) is not CONTINUE:
                return res
            cache = {}
            source_map = get_arg_map(source_spec or target_spec, source_args, source_kwargs)
            target_map = get_arg_def(target_spec) if source_fun is not None else source_map
            for annotated_name, annotation in target_spec.annotations.items():
                if get_origin(annotation) is Annotated:
                    annotated_type = annotation.__origin__
                    for validator in annotation.__metadata__:
                        if not isinstance(validator, Validator):
                            raise Exception('Invalid annotation - only ValiDecor instances are allowed')
                        validator.annotated_name = annotated_name
                        validator.annotated_type = annotated_type
                        validator.cache = cache
                        try:
                            if isinstance(validator, SimpleValidator):
                                validator(target_map[annotated_name])
                            elif isinstance(validator, ExtendedValidator):
                                validator(source_map, target_map)
                            else:
                                pass
                        except Exception as e:
                            return val_hook(e, validator)
            if source_spec is None:
                target_args = source_args
                target_kwargs = source_kwargs
            else:
                target_args = [ target_map[arg_name] for arg_name in target_spec.args ]
                if target_spec.varargs is not None:
                    target_args.extend(target_map[target_spec.varargs])
                target_kwargs = { arg_name: target_map[arg_name] for arg_name in target_spec.kwonlyargs }
                if target_spec.varkw is not None:
                    target_kwargs.update(target_map[target_spec.varkw])
            try:
                res = target_fun(*target_args, **target_kwargs)
            except Exception as e:
                return err_hook(e, *target_args, **target_kwargs)
            else:
                return map_hook(res)
        return wrapper
    return decorator
