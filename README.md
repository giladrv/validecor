# ValiDecor

ValiDecor is a Python library designed to facilitate robust input validation using its core decorator `validecor`. It leverages Python's type annotation system to provide a seamless and intuitive interface for enforcing input constraints directly in function signatures using the special annotation type `typing.Annotated`.

Validecor was designed with special attention for its potential use on AWS Lambda functions. AWS Lambda handlers expect a fixed signature, i.e. `handler(event, context)`. This signature is uninformative and hinders code development.

## Installation (not implement yet)

Install ValiDecor via pip:

    pip install validecor

## Usage

### Basic Usage

To use ValiDecor, annotate function arguments with the desired validators wrapped inside `typing.Annotated`, and apply the `@validecor()` decorator to the function. Here is a basic example:

    from typing import Annotated
    from validecor import validecor
    from validecor.validators import IsType

    @validecor()
    def hello(msg: Annotated[str, IsType(str)]):
        print('Message:', msg)

### Advanced Usage (AWS Lambda)

The `validecor` decorator accepts several parameters to customized its usage. One can define the function signature expected by the caller, and automatically map the input to actually relevant arguments needed by the function. This is best explained with an example:

    from typing import Annotated
    from validecor import Attr, Map, validecor
    from validecor.validators import IsType

    # we define the source function signature
    def handler(event, context):
        pass
    
    # extend the Map class for better readability later
    class MapS3(Map):
        def __init__(self, *nodes: int | str | Callable[..., Any]):
            super().__init__('event', 'Records', 0, 's3', *nodes)

    # some function to be applied during the mapping
    def to_mb(size_in_bytes: float):
        return size_in_bytes / 1024 / 1024

    @validecor(handler)
    def s3_trigger(
        bucket: Annotated[str, MapS3('bucket', 'name')],
        key: Annotated[str, MapS3('object', 'key')],
        size: Annotated[float, MapS3('object', 'size', to_mb)],
        mem: Annotated[int, Map('context', Attr('memory_limit_in_mb'))]):
        ...

This way we only get the arguments relevant for the function operation, with helpful type hints, and don't need to bother with extracting them from the original `event` or `context` inputs within the function body.

Maps will be cached internally so as not to reapeat potentially expensive operations.

#### Callback Hooks

The `validecor` decorator supports the following hooks:

##### Initialization And Logging

    pre_hook: Callable[[*source_args, **source_kwargs], Any] = default_log_hook
    
This hook is called with the same arguments as the original function. Can be used for logging or halting the rest of the function execution by returning any `not None` value, which is then returned to the original caller. By default no action is performed.

##### Validation Handling

    val_hook: Callable[[Exception, Validator | ExtendedValidator], Any] = default_val_hook

This hook is called upon validation errors (or Map failures). Use this to return a custom error message to the user. By default the exception is re-raised unchanged.

##### Function Errors

    err_hook: Callable[[Exception, *target_args, **target_kwargs], Any] = default_err_hook

This hook is called when an exception is raised within the function body. The return value of the hook is the final value returned to the original caller. By default the exception is re-raised unchanged.

##### Post-Processing

    map_hook: Callable[[Any], Any] = default_map_hook

This hook is called with the results of the function to enable any post-processing. The return value of the hook is the final value returned to the original caller. By default passes along the same value returned by the function.

### Custom Validators

You can create custom validators in two ways: using the `validators.Custom` class which accepts any `Callable`, or by extending the `Validator` or `ExtendedValidator` classes from `validecor.core`. Here's how to create a custom validator that ensures a number is positive:

    from validecor.core import Validator

    class IsPositive(Validator):
        def __call__(self, arg):
            try:
                if arg <= 0:
                    raise ValueError(f"Invalid value: {arg}")
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f'Uncomparable value: {arg}', e)
        def __desc__(self):
            return "Argument must be a positive number."

    @validecor()
    def increment(number: Annotated[int, IsPositive()]):
        return number + 1

Typically we would want the description to be general for the validation class, and the error message to contain some clue as to why the validation failed, e.g. by noting the argument value or type.

## Contributing

Contributions to ValiDecor are welcome! Fork the repository, make your changes, and submit a pull request to contribute.

## License

ValiDecor is released under the MIT License. See the LICENSE file for more details.
