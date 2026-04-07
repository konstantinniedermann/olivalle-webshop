from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RedirectWwwMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        host = request.headers.get("host", "")
        if host.startswith("www."):
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            new_url = request.url.replace(netloc=host[4:], scheme=proto)
            return RedirectResponse(url=str(new_url), status_code=301)
        return await call_next(request)
