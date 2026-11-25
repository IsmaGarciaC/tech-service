from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.modules.customers.router import router as customers_router

app = FastAPI()
app.include_router(customers_router, prefix="/api/v1")


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=500, content={"detail": "Database operation failed"}
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
