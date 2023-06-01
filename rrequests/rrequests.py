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


RESILIENT_METHODS = ("post", "get", "patch", "delete", "put", "head")
PROXIES_ATTRS = (
    "_timeout",
    "_error_threshold",
    "_open_duration",
    "_breaker",
    "_cache",
    "_session",
)


def decorate_method(method, cache, obj, timeout, breaker):
    if method not in cache:
        requests_method = getattr(obj, method)
        requests_method = timeout_decorator(timeout=timeout)(requests_method)
        requests_method = force_exception_on_status_error(requests_method)
        cache[method] = intercept_circuit_breaker_error(breaker(requests_method))
    return cache[method]


class BaseProxy:
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


class SessionProxy(BaseProxy):
    def __init__(
        self,
        timeout,
        error_threshold,
        open_duration,
        session,
    ):
        self._session = session
        super().__init__(timeout, error_threshold, open_duration)

    def __getattribute__(self, attribute):
        if attribute in RESILIENT_METHODS:
            return decorate_method(
                attribute, self._cache, self._session, self._timeout, self._breaker
            )
        if attribute in PROXIES_ATTRS:
            return super().__getattribute__(attribute)
        return getattr(self._session, attribute)

    def __call__(self, *args, **kwargs):
        return self


class RequestsProxy(BaseProxy):
    def __getattribute__(self, attribute):
        if attribute == "Session":
            return SessionProxy(
                self._timeout,
                self._error_threshold,
                self._open_duration,
                requests.Session(),
            )
        if attribute in RESILIENT_METHODS:
            return decorate_method(
                attribute, self._cache, requests, self._timeout, self._breaker
            )
        if attribute in PROXIES_ATTRS:
            return super(RequestsProxy, self).__getattribute__(attribute)
        return getattr(requests, attribute)
