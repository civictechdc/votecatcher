from asgi_correlation_id import CorrelationIdMiddleware as _CorrelationIdMiddleware


class CorrelationIdMiddleware(_CorrelationIdMiddleware):
    def __init__(self, app, **kwargs):
        kwargs.setdefault("header_name", "X-Correlation-ID")
        super().__init__(app, **kwargs)


__all__ = ["CorrelationIdMiddleware"]
