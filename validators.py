# Standard
from typing import Any, Callable, Type
# Internal
from .core import Validator, repx

class Between(Validator):
    """
    Check that the argument is between lo and hi (inclusive).
    """
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi
    def __call__(self, arg):
        try:
            if arg < self.lo or self.hi < arg:
                raise ValueError(f'Invalid value: {arg}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Uncomparable value: {arg}', e)
    def __desc__(self):
        return f'Argument must be between {repr(self.lo)} and {repr(self.hi)} (inclusive)'
    def __repr__(self):
        name = type(self).__name__
        details = f'{repr(self.lo)},{repr(self.hi)}'
        return f'{name}({details})'

class Custom(Validator):
    """
    Execute a simple custom validator.

    `validator(arg):` raise an exception with the first argument
        being a message for the end-user, and optionally debugging message
        in the second argument.
    """
    def __call__(self, arg):
        self.validator(arg)
    def __desc__(self):
        desc = f'Argument must not fail `{self.validator.__name__}`'
        if self.validator.__doc__ is not None:
            desc += ':\n' + self.validator.__doc__
        return desc
    def __init__(self, validator: Callable[[Any], None]):
        self.validator = validator
    def __repr__(self):
        return f'{type(self).__name__}({repx(self.validator)})'

class IsType(Validator):
    """
    Ensure the argument type matches the target type.
    """
    def __init__(self, target_type: Type):
        self.target_type = target_type
    def __call__(self, arg):
        arg_type = type(arg)
        if arg_type is not self.target_type:
            raise TypeError(f'Invalid type: {arg_type.__name__}')
    def __desc__(self):
        return f'Argument must be of type: {self.target_type.__name__}'
    def __repr__(self):
        name = type(self).__name__
        details = self.target_type.__name__
        return f'{name}({details})'

class IsTypable(Validator):
    """
    Ensure the argument type can be converted to the target type.
    """
    def __call__(self, arg):
        try:
            self.target_type(arg)
        except Exception as e:
            raise TypeError(f'Incompatible type: {type(arg).__name__}', e)
    def __desc__(self):
        return f'Argument must be convertible to type `{self.target_type.__name__}`'
    def __init__(self, target_type: Type):
        self.target_type = target_type
    def __repr__(self):
        name = type(self).__name__
        details = self.target_type.__name__
        return f'{name}({details})'
