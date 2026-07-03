from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

app = FastAPI()

# Only this origin is allowed
ALLOWED_ORIGIN = "https://dash-3dgicu.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware to add required headers
@app.middleware("http")
async def add_custom_headers(request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response


@app.get("/stats")
def get_stats(values: str):
    numbers = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": "25ds1000066@ds.study.iitm.ac.in",
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }