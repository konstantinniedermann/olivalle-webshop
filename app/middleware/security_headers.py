import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# CSP ohne 'unsafe-eval': Tailwind wird zur Build-Zeit kompiliert (Issue #88),
# Inline-Scripts laufen über Nonces (Issue #89).
CSP_TEMPLATE = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}' https://js.stripe.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "img-src 'self' data:; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "connect-src 'self' https://api.stripe.com; "
    "frame-src https://js.stripe.com https://hooks.stripe.com; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self' https://checkout.stripe.com"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP_TEMPLATE.format(nonce=nonce)

        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
