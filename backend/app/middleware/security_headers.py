"""Security headers middleware.

Injects OWASP-recommended security headers on every HTTP response.
Environment-conditional: HSTS (production only), CSP report-only (dev).
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_PRODUCTION_CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
_PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=()"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, is_production: bool = False, **kwargs):
        super().__init__(app, **kwargs)
        self._is_production = is_production

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if "x-content-type-options" not in response.headers:
            response.headers["x-content-type-options"] = "nosniff"

        if "x-frame-options" not in response.headers:
            response.headers["x-frame-options"] = "DENY"

        if "referrer-policy" not in response.headers:
            response.headers["referrer-policy"] = "strict-origin-when-cross-origin"

        if "permissions-policy" not in response.headers:
            response.headers["permissions-policy"] = _PERMISSIONS_POLICY

        if "x-request-id" not in response.headers:
            response.headers["x-request-id"] = str(uuid.uuid4())

        if self._is_production:
            if "strict-transport-security" not in response.headers:
                response.headers["strict-transport-security"] = (
                    "max-age=63072000; includeSubDomains; preload"
                )
            if "content-security-policy" not in response.headers:
                response.headers["content-security-policy"] = _PRODUCTION_CSP
        else:
            if "content-security-policy-report-only" not in response.headers:
                response.headers["content-security-policy-report-only"] = _PRODUCTION_CSP

        return response
