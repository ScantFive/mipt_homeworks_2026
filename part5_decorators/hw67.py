import json
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


def _seconds_passed(time: datetime) -> float:
    return (datetime.now(UTC) - time).total_seconds()


def _validate(critical_count: int, time_to_recover: int) -> None:
    errors = []
    if not isinstance(critical_count, int) or critical_count <= 0:
        errors.append(ValueError(INVALID_CRITICAL_COUNT))
    if not isinstance(time_to_recover, int) or time_to_recover <= 0:
        errors.append(ValueError(INVALID_RECOVERY_TIME))
    if errors:
        raise ExceptionGroup(VALIDATIONS_FAILED, errors)


class CircuitBreaker:
    def __init__(self, critical_count=5, time_to_recover=30, triggers_on: type[Exception] = Exception) -> None:
        _validate(critical_count, time_to_recover)
        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self._failures = 0
        self.time_of_closure = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        func_name = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            return self._process_call(func, func_name, args, kwargs)

        return wrapper

    def _process_call(
        self,
        func: CallableWithMeta[P, R_co],
        func_name: str,
        args: tuple,
        kwargs: dict,
    ) -> R_co:
        if self.time_of_closure is not None:
            if _seconds_passed(self.time_of_closure) < self.time_to_recover:
                raise BreakerError(func_name, self.time_of_closure)
            self._failures = 0
            self.time_of_closure = None

        try:
            result = func(*args, **kwargs)
        except self.triggers_on as exc:
            self._failures += 1
            if self._failures >= self.critical_count:
                self.time_of_closure = datetime.now(UTC)
                raise BreakerError(func_name, self.time_of_closure) from exc
            raise
        else:
            self._failures = 0
            return result


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
