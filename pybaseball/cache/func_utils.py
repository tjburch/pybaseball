import copy
import hashlib
import re
from typing import Callable, Dict, Hashable, Iterable, Optional, Tuple, Union

MAX_ARGS_KEY_LENGTH = 128

def get_value_hash(value: Optional[Union[str, Dict, Hashable, Iterable]], include_designators: bool = True) -> str:
    def _strip_invalid(value: str) -> str:
        # Remove invalid filename characters
        stripped = copy.copy(value)
        stripped = str(stripped).strip().replace(' ', '_')
        stripped = re.sub(r'(?u)[^-\w.]', '', stripped)
        stripped = stripped.replace("'", "\'")

        return stripped

    if value is None:
        return 'None'

    if isinstance(value, str):
        stripped = _strip_invalid(value)
        if value == stripped:
            # If nothing got changed, then the value is safe
            if include_designators:
                return f"'{value}'"
            return f"{value}"

    if isinstance(value, tuple):
        values = ', '.join([f"{get_value_hash(sub_value)}" for sub_value in value]).strip(', ')
        if include_designators:
            return f"({values})"
        return f"{values}"

    if isinstance(value, list):
        values = ', '.join([f"{get_value_hash(sub_value)}" for sub_value in value]).strip(', ')
        if include_designators:
            return f"[{values}]"
        return f"{values}"
    
    if isinstance(value, dict):
        values = ', '.join([
            f"{get_value_hash(key, include_designators=False)}={get_value_hash(value[key])}"
            for key in value.keys()
        ]).strip(', ')
        if include_designators:
            return "{" + values + "}"
        return values

    if hasattr(value, '__dict__'):
        dict_value = get_value_hash(value.__dict__)
        if hasattr(value, '__class__'):
            return f"{_strip_invalid(value.__class__.__name__)}({dict_value})"
        else:
            return dict_value

    try:
        return str(value.__hash__())
    except:
        raise ValueError(f"value {value} of type {type(value)} is not hashable.")


def get_func_name(func: Callable) -> str:
    if '__self__' in dir(func):
        # This is a class method
        return f"{func.__getattribute__('__self__').__class__.__name__}.{func.__name__}"
    return f"{func.__name__}"


def get_func_hash(func: Callable, args: Tuple, kwargs: Dict) -> str:
    f_hash = f"{get_func_name(func)}"

    args_hash = get_value_hash(args, include_designators=False)
    kwargs_hash = get_value_hash(kwargs, include_designators=False)

    args_key = ', '.join([args_hash, kwargs_hash]).strip(', ')

    # If the args_key is very long, just use a sha hash

    if len(args_key) > MAX_ARGS_KEY_LENGTH:
        # Let's hash this to make the filename shorter
        args_key = hashlib.sha256(args_key.encode('utf-8')).hexdigest()

    return f"{f_hash}({args_key})"
