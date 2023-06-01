import pybreaker as pybreaker
import requests

from rrequests.exceptions import CircuitBreakerError


def get_rrequests(
    timeout=None,
    error_threshold=5,
    open_duration=30,
):
    return RequestsProxy(
        timeout=timeout if timeout else 10,
        error_threshold=error_threshold,
        open_duration=open_duration,
    )


def timeout_decorator(timeout):
    def decorator_request_method(request_method):
        def wrapper(url, **kwargs):
            kwargs["timeout"] = timeout
            return request_method(url, **kwargs)

        return wrapper

    return decorator_request_method


def force_exception_on_status_error(request_method):
    def wrapper(*args, **kwargs):
        response = request_method(*args, **kwargs)
        response.raise_for_status()
        return response

    return wrapper


def intercept_circuit_breaker_error(circuit_breaker_method):
    def wrapper(*args, **kwargs):
        try:
            return circuit_breaker_method(*args, **kwargs)
        except pybreaker.CircuitBreakerError as err:
            raise CircuitBreakerError(str(err))

    return wrapper


class RequestsProxy:
    def __init__(
        self,
        timeout,
        error_threshold,
        open_duration,
    ):
        self._timeout = timeout
        self._error_threshold = error_threshold
        self._open_duration = open_duration
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=error_threshold, reset_timeout=open_duration
        )
        self._cache = dict()

    def _getattribute(self, attribute):
        if attribute not in self._cache:
            requests_method = getattr(requests, attribute)
            requests_method = timeout_decorator(timeout=self._timeout)(requests_method)
            requests_method = force_exception_on_status_error(requests_method)
            self._cache[attribute] = intercept_circuit_breaker_error(
                self._breaker(requests_method)
            )
        return self._cache[attribute]

    def __getattribute__(self, attribute):
        if attribute in ("post", "get", "patch", "delete", "put", "head"):
            return self._getattribute(attribute)
        if attribute in (
            "_timeout",
            "_error_threshold",
            "_open_duration",
            "_breaker",
            "_cache",
            "_getattribute",
        ):
            return super(RequestsProxy, self).__getattribute__(attribute)
        return getattr(requests, attribute)
