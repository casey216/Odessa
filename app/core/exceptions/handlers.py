from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError

from app.core.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    """Call this once from your app factory / main.py, e.g.:

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(manufacturer_router)

    Keeping this registration separate (rather than each router catching its
    own exceptions) means every service in the app gets the same NotFound ->
    404 / Conflict -> 409 mapping for free, without repeating try/except in
    every endpoint.
    """

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> Response:
        resp = Response(status_code=status.HTTP_404_NOT_FOUND)
        resp.headers["HX-Flash"] = f"error:{str(exc)}"
        return resp

    @app.exception_handler(ConflictError)
    async def handle_conflict(request: Request, exc: ConflictError) -> Response:
        resp = Response(status_code=status.HTTP_409_CONFLICT)
        resp.headers["HX-Flash"] = f"error:{str(exc)}"
        return resp

    @app.exception_handler(ValidationError)
    async def handle_validation(request: Request, exc: ValidationError) -> Response:
        resp = Response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        resp.headers["HX-Flash"] = f"error:{str(exc)}"
        return resp

    @app.exception_handler(RequestValidationError)
    async def handle_rvalidation(request: Request, exc: RequestValidationError) -> Response:
        resp = Response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        for error in exc.errors():
            field = error["loc"][1].replace("_", " ")
            msg = error["msg"]
            error_message = f"{field}: {msg}"
            resp.headers["HX-Flash"] = f"error:{error_message}"
        return resp

    @app.exception_handler(AuthenticationError)
    async def handle_authentication(request: Request, exc: AuthenticationError) -> Response:
        return RedirectResponse("/auth/login", status_code=302)

    @app.exception_handler(AuthorizationError)
    async def handle_authorization(request: Request, exc: AuthorizationError) -> Response:
        if request.headers.get("HX-Request"):
            resp = Response(status_code=status.HTTP_403_FORBIDDEN)
            resp.headers["HX-Flash"] = f"error:{str(exc)}"
            return resp
        return request.app.state.templates.TemplateResponse(
            "403.html", {"request": request}, status_code=403
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError) -> Response:
        logger.exception("Unhandled IntegrityError", exc_info=exc)

        resp = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        resp.headers["HX-Flash"] = "error:Database error."
        return resp

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: IntegrityError) -> Response:
        logger.exception("Unhandled Exception", exc_info=exc)

        resp = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        resp.headers["HX-Flash"] = "error:Internal server error."
        return resp
