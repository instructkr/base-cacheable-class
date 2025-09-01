from collections.abc import Callable
from typing import Any


def default_key(f: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
    arg_str = str(args)
    kwarg_str = str(kwargs) if kwargs else "{}"
    func_name = getattr(f, "__name__", "unknown")
    return f"{func_name}:{arg_str}:{kwarg_str}"


def default_pattern(target_func_name: str, param_mapping: dict[str, str] | None, **kwargs: Any) -> str:
    pattern = rf"{target_func_name}:\(.*\):{{.*}}"
    if param_mapping:
        # 매핑된 파라미터 값 추출
        mapped_kwargs = {
            target_param: kwargs[source_param]
            for target_param, source_param in param_mapping.items()
            if source_param in kwargs
        }
        kwargs_patterns = [rf".*'{k}':\s*'{v!s}'" for k, v in mapped_kwargs.items()]
        pattern = rf"{target_func_name}:\(.*\):{{" + ".*".join(kwargs_patterns) + ".*}"
    return pattern
