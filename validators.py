# Standard
from typing import Any, Callable, Dict, Type
# Internal
from core import ErrorType, ValidecorError, Validator

class Between(Validator):
    """
    Check that the argument is between lo and hi (inclusive).
    """
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi
    def __call__(self, 
            arg_name: str,
            arg_type: Type,
            _,
            target_map: Dict[str, Any]):
        try:
            arg = target_map[arg_name]
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
    def __call__(self, 
            arg_name: str,
            arg_type: Type,
            _,
            target_map: Dict[str, Any]):
        try:
            arg = target_map[arg_name]
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

class IsType(Validator):
    """
    Ensure the argument type matches the defined (or override) type.
    """
    def __init__(self, type_override: Type = None):
        self.type_override = type_override
    def __call__(self, 
            arg_name: str,
            arg_type: Type,
            _,
            target_map: Dict[str, Any]):
        arg = target_map[arg_name]
        actual_type = type(arg)
        if self.type_override is not None:
            arg_type = self.type_override
        if actual_type is not arg_type:
            raise ValidecorError(ErrorType.ArgVal,
                actual_type = actual_type,
                arg_name = arg_name,
                arg_type = arg_type,
                validator = self)
    def __repr__(self):
        name = type(self).__name__
        details = '' if self.type_override is None else self.type_override.__name__
        return f'{name}({details})'

class IsTypable(Validator):
    """
    Ensure the argument type matches the defined (or override) type.
    """
    def __init__(self, type_override: Type = None):
        self.type_override = type_override
    def __call__(self, 
            arg_name: str,
            arg_type: Type,
            _,
            target_map: Dict[str, Any]):
        try:
            arg = target_map[arg_name]
            if self.type_override is not None:
                arg_type = self.type_override
            target_map[arg_name] = arg_type(arg)
        except Exception as e:
            raise ValidecorError(ErrorType.ArgVal,
                arg_name = arg_name,
                arg_type = arg_type,
                validator = self,
                sub_error = e)
    def __repr__(self):
        name = type(self).__name__
        details = '' if self.type_override is None else self.type_override.__name__
        return f'{name}({details})'
