import pybreaker as pybreaker
import requests


def get_rrequests(
    timeout=None,
    error_threshold=3,
    open_duration=30,
):
    return RRequest(
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


class RRequest:
    def __init__(
        self,
        timeout,
        error_threshold,
        open_duration,
    ):
        self.timeout = timeout
        self.error_threshold = error_threshold
        self.open_duration = open_duration
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=error_threshold, reset_timeout=open_duration
        )
        self.cache = dict()

    def _getattribute(self, attribute):
        if attribute not in self.cache:
            function = timeout_decorator(timeout=self.timeout)(
                getattr(requests, attribute)
            )
            self.cache[attribute] = self.breaker(function)
        return self.cache[attribute]

    def __getattribute__(self, attribute):
        if attribute in ("post", "get", "patch", "delete", "put"):
            return self._getattribute(attribute)
        return super(RRequest, self).__getattribute__(attribute)
