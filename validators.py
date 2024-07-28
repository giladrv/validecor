# Standard
import json
import re
from re import RegexFlag, Pattern
from typing import Any, Callable, Type
# Internal
from .core import Map, SimpleValidator, Validator, repx

class Between(SimpleValidator):
    """
    Check that the argument is between lo and hi (inclusive).
    """
    def __call__(self, arg):
        try:
            if arg < self.lo or self.hi < arg:
                raise ValueError(f'Invalid value: {arg}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        return f'Argument must be between {repx(self.lo)} and {repx(self.hi)} (inclusive)'
    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi
    def __repr__(self):
        name = type(self).__name__
        details = f'{repx(self.lo)},{repx(self.hi)}'
        return f'{name}({details})'

class Custom(SimpleValidator):
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

class IsJsonStr(SimpleValidator):
    """
    Ensure the argument is a valid json string.
    """
    def __call__(self, arg):
        try:
            json.loads(arg, default = self.default or str)
        except Exception as e:
            raise TypeError(f'Not a valid json string: {repx(arg)}', e)
    def __desc__(self):
        return 'Argument must be a valid json string'
    def __init__(self, default = None):
        self.default = default
    def __repr__(self):
        desc = type(self).__name__
        if self.default is not None:
            desc += f'({repx(self.default)})'
        return desc

class IsType(SimpleValidator):
    """
    Ensure the argument type matches the target type.
    """
    def __call__(self, arg):
        if self.allow_none and arg is None:
            return
        arg_type = type(arg)
        if arg_type not in self.target_types:
            raise TypeError(f'Invalid type: {arg_type.__name__}')
    def __desc__(self):
        return f'Argument must be of type: {self.format_types()}'
    def __init__(self, *target_types: tuple[Type], allow_none: bool = False):
        self.target_types = target_types
        self.allow_none = allow_none
    def __repr__(self):
        return f'{type(self).__name__}({self.format_types()})'
    def format_types(self):
        return ','.join(tt.__name__ for tt in self.target_types)

class IsTypable(SimpleValidator):
    """
    Ensure the argument type can be converted to the target type.
    """
    def __call__(self, arg):
        try:
            self.target_type(arg)
        except Exception as e:
            raise TypeError(f'Incompatible type: {type(arg).__name__}', e)
    def __desc__(self):
        return f'Argument must be convertible to type: {self.target_type.__name__}'
    def __init__(self, target_type: Type):
        self.target_type = target_type
    def __repr__(self):
        name = type(self).__name__
        details = self.target_type.__name__
        return f'{name}({details})'

class LenBetween(SimpleValidator):
    """
    Check that the argument length is between lo and hi (inclusive).
    """
    def __call__(self, arg):
        try:
            arg_len = len(arg)
            if self.lo is not None and arg_len < self.lo:
                raise ValueError(f'Too short: {repx(arg)}')
            if self.hi is not None and arg_len > self.hi:
                raise ValueError(f'Too long: {repx(arg)}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        desc = f'Argument length must be'
        if self.lo is not None:
            desc += f' greater than {self.lo}'
        if self.hi is not None:
            desc += f' less than {self.hi}'
        desc += ' (inclusive)'
    def __init__(self, lo: int = None, hi: int = None):
        self.lo = lo
        self.hi = hi
    def __repr__(self):
        details = f'{repx(self.lo)},{repx(self.hi)}'
        return f'{type(self).__name__}({details})'

class LessThan(SimpleValidator):
    """
    Check that the argument is less than hi.
    """
    def __call__(self, arg):
        try:
            if arg >= self.hi:
                raise ValueError(f'Invalid value: {arg}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        return f'Argument must be less than {repx(self.hi)}'
    def __init__(self, hi):
        self.hi = hi
    def __repr__(self):
        return f'{type(self).__name__}({repx(self.hi)})'

class LessThanOrEqual(SimpleValidator):
    """
    Check that the argument is less than or equal to hi.
    """
    def __call__(self, arg):
        try:
            if arg > self.hi:
                raise ValueError(f'Invalid value: {arg}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        return f'Argument must be less than or equal to {repx(self.hi)}'
    def __init__(self, hi):
        self.hi = hi
    def __repr__(self):
        return f'{type(self).__name__}({repx(self.hi)})'

class GreaterThan(SimpleValidator):
    """
    Check that the argument is greater than lo.
    """
    def __call__(self, arg):
        try:
            if arg <= self.lo:
                raise ValueError(f'Invalid value: {arg}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        return f'Argument must be greater than {repx(self.lo)}'
    def __init__(self, lo):
        self.lo = lo
    def __repr__(self):
        return f'{type(self).__name__}({repx(self.lo)})'

class GreaterThanOrEqual(SimpleValidator):
    """
    Check that the argument is greater than or equal to hi.
    """
    def __call__(self, arg):
        try:
            if arg < self.lo:
                raise ValueError(f'Invalid value: {arg}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        return f'Argument must be greater than or equal to {repx(self.lo)}'
    def __init__(self, lo):
        self.lo = lo
    def __repr__(self):
        return f'{type(self).__name__}({repx(self.lo)})'

class Not(SimpleValidator):
    """
    Check that the argument is not valid according to the target validator.
    """
    def __call__(self, arg):
        try:
            self.validator(arg)
            raise ValueError(f'Valid: {repx(arg)}')
        except:
            pass
    def __desc__(self):
        return f'Argument must not be valid according to {repx(self.validator)}'
    def __init__(self, validator: Validator):
        self.validator = validator
    def __repr__(self):
        return f'{type(self).__name__}'

class NotBlank(SimpleValidator):
    """
    Check that the argument is not blank.
    """
    def __call__(self, arg):
        try:
            if (arg.strip() if self.auto_strip else arg) == "":
                raise ValueError(f'A blank string is invalid: {repx(arg)}')
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'Not a string: {arg}', e)
    def __desc__(self):
        return f'Argument must not be blank'
    def __init__(self, auto_strip: bool = True):
        self.auto_strip = auto_strip
    def __repr__(self):
        return f'{type(self).__name__}'

class NotNone(SimpleValidator):
    """
    Check that the argument is not None.
    """
    def __call__(self, arg):
        if arg is None:
            raise ValueError(f'None is invalid')
    def __desc__(self):
        return f'Argument must not be None'
    def __repr__(self):
        return f'{type(self).__name__}'

class OfEnum(SimpleValidator):
    """
    Ensure the argument is of the target Enum. The literal enum values are allowed.
    """
    def __init__(self, target_enum: Type):
        self.target_enum = target_enum
    def __call__(self, arg):
        try:
            self.target_enum(arg)
        except Exception as e:
            raise ValueError(f'Invalid value: {arg}', e)
    def __desc__(self):
        return f'Argument must be of the enum: {self.target_enum.__name__}'
    def __repr__(self):
        return f'{type(self).__name__}({self.target_enum.__name__})'

class OneOf(SimpleValidator):
    """
    Ensure the argument is one of the target values.
    """
    def __init__(self, *target_values: tuple[Any]):
        self.target_values = target_values
    def __call__(self, arg):
        if arg not in self.target_values:
            raise TypeError(f'Invalid value: {arg}')
    def __desc__(self):
        return f'Argument must be one of: {self.format_values()}'
    def __repr__(self):
        return f'{type(self).__name__}({self.format_values()})'
    def format_values(self):
        return ','.join(repx(tv) for tv in self.target_values)

class Regex(SimpleValidator):
    """
    Ensure the argument matches the regex pattern.
    """
    def __init__(self, pattern: str | Pattern[str], flags: int | RegexFlag = 0):
        self.pattern = pattern
        self.flags = flags
    def __call__(self, arg):
        try:
            if re.fullmatch(self.pattern, arg, self.flags) is None:
                raise ValueError(f'Invalid value: {arg}')
        except Exception as e:
            raise ValueError(f'Incompatible value: {arg}', e)
    def __desc__(self):
        return f'Argument must match the regex pattern: {self.target_enum.__name__}'
    def __repr__(self):
        details = repx(self.pattern)
        if self.flags != 0:
            details += ',' + repx(self.flags)
        return f'{type(self).__name__}({details})'

class MapApiGatewayBody(Map):
    def __init__(self, *nodes: int | str | Callable[..., Any]):
        super().__init__('event', 'body', json.loads, *nodes, hidden = 3)

class MapApiGatewayQuery(Map):
    def __init__(self, *nodes: int | str | Callable[..., Any]):
        super().__init__('event', 'queryStringParameters', *nodes, hidden = 2)
