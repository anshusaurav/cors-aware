from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time, uuid

ALLOWED_ORIGIN = "https://dash-saz67x.example.com"
EMAIL = "anshu.saurav@gmail.com"

app = FastAPI()

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

@app.middleware("http")
async def strict_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    response = await call_next(request)
    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Vary"] = "Origin"
    return response

@app.options("/stats")
async def stats_preflight(request: Request):
    origin = request.headers.get("origin")
    headers = {}
    if origin == ALLOWED_ORIGIN:
        headers = {
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "*"),
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }
    return Response(status_code=200, headers=headers)

@app.get("/stats")
async def stats(values: str = Query(...)):
    try:
        nums = [int(p.strip()) for p in values.split(",") if p.strip() != ""]
        if not nums:
            raise ValueError
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "invalid values"})
    count = len(nums)
    total = sum(nums)
    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": total / count,
    }