# Standard
from typing import Any, Callable, Dict, Type
# Internal
from core import ErrorType, ValidecorError, Validator

class IsType(Validator):
    """
    Ensure the argument type matches the defined (or override) type.
    """
    def __init__(self, type_override: Type = None):
        self.type_override = type_override
    def __call__(self, arg_name: str, arg_type: Type, arg, arg_map: dict):
        actual_type = type(arg)
        if self.type_override is not None:
            arg_type = self.type_override
        if actual_type is not arg_type:
            raise ValidecorError(ErrorType.ArgVal,
                arg_name = arg_name,
                arg_type = arg_type,
                validator = self)
    def __repr__(self):
        name = type(self).__name__
        details = '' if self.type_override is None else self.type_override.__name__
        return f'{name}({details})'

class Between(Validator):
    """
    Check that the argument is between lo and hi (inclusive).
    """
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi
    def __call__(self, arg_name: str, arg_type: Type, arg, *_):
        try:
            if arg < self.lo or self.hi < arg:
                raise ValidecorError(ErrorType.ArgVal,
                    arg_name = arg_name,
                    arg_type = arg_type,
                    validator = self)
        except ValidecorError as e:
            raise e
        except Exception as e:
            raise ValidecorError(ErrorType.ArgVal,
                arg_name = arg_name,
                arg_type = arg_type,
                validator = self,
                sub_error = e)
    def __repr__(self):
        name = type(self).__name__
        details = f'{repr(self.lo)},{repr(self.hi)}'
        return f'{name}({details})'

class Custom(Validator):
    """
    Execute a simple custom validator.
    """
    def __init__(self, validator: Callable[[Any], None]):
        self.validator = validator
    def __call__(self, arg_name: str, arg_type: Type, arg, *_):
        try:
            self.validator(arg)
        except Exception as e:
            raise ValidecorError(ErrorType.ArgVal,
                arg_name = arg_name,
                arg_type = arg_type,
                validator = self,
                sub_error = e)
    def __repr__(self):
        name = type(self).__name__
        details = f'{repr(self.validator)}'
        return f'{name}({details})'

class CustomX(Validator):
    """
    Execute a fully custom validator.
    """
    def __init__(self, validator: Callable[[str, Type, Any, Dict[str, Any]], None]):
        self.validator = validator
    def __call__(self, arg_name: str, arg_type: Type, arg, arg_map: Dict[str, Any]):
        self.validator(arg_name, arg_type, arg, arg_map)
    def __repr__(self):
        name = type(self).__name__
        details = f'{repr(self.validator)}'
        return f'{name}({details})'
