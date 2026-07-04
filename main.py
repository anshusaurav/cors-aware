import time
import uuid

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ---- Config -----------------------------------------------------------
ALLOWED_ORIGIN = "https://dash-saz67x.example.com"
EMAIL = "25f1002017@ds.study.iitm.ac.in"

app = FastAPI()


# ---- Middleware: X-Request-ID + X-Process-Time -------------------------
class TimingAndRequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.6f}"
        return response


app.add_middleware(TimingAndRequestIdMiddleware)


# ---- Strict, hand-rolled CORS handling ---------------------------------
# We avoid Starlette's built-in CORSMiddleware here so we have full,
# explicit control over exactly when the ACAO header is emitted
# (only for the one allowed origin, never a wildcard).

@app.middleware("http")
async def strict_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")

    # Handle preflight requests directly.
    if request.method == "OPTIONS":
        if origin == ALLOWED_ORIGIN:
            headers = {
                "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": request.headers.get(
                    "access-control-request-headers", "*"
                ),
                "Access-Control-Max-Age": "600",
                "Vary": "Origin",
            }
            return JSONResponse(content={}, status_code=200, headers=headers)
        else:
            # No ACAO header for disallowed / missing origins.
            return JSONResponse(content={}, status_code=200)

    # Normal (non-preflight) requests.
    response = await call_next(request)
    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Vary"] = "Origin"
    return response


# ---- Explicit preflight handler (belt-and-braces alongside the middleware) --
@app.options("/stats")
async def stats_preflight(request: Request):
    origin = request.headers.get("origin")
    headers = {}
    if origin == ALLOWED_ORIGIN:
        headers = {
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": request.headers.get(
                "access-control-request-headers", "*"
            ),
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }
    return JSONResponse(content={}, status_code=200, headers=headers)


# ---- /stats endpoint -----------------------------------------------------
@app.get("/stats")
async def stats(values: str = Query(..., description="Comma-separated integers")):
    try:
        parts = [p.strip() for p in values.split(",") if p.strip() != ""]
        nums = [int(p) for p in parts]
        if not nums:
            raise ValueError("empty list")
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": "values must be a comma-separated list of integers"},
        )

    count = len(nums)
    total = sum(nums)
    minimum = min(nums)
    maximum = max(nums)
    mean = total / count

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": minimum,
        "max": maximum,
        "mean": mean,
    }


@app.get("/")
async def root():
    return {"status": "ok"}
