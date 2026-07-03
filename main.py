from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import time
import uuid
import os
import yaml
from dotenv import load_dotenv, dotenv_values

app = FastAPI()

# Load OS environment (does NOT override existing OS vars)
load_dotenv()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Middleware --------------------
@app.middleware("http")
async def add_custom_headers(request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response

# -------------------- JWT Config --------------------
PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4LlgniT7GlkL9Mce3b0wGLs9/7ZIXdQIDAQAB
-----END PUBLIC KEY-----
"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-r393h5hh.apps.exam.local"

# -------------------- Models --------------------
class TokenRequest(BaseModel):
    token: str

# -------------------- Helpers --------------------
def to_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in [
        "true",
        "1",
        "yes",
        "on"
    ]


def load_yaml_config():
    try:
        with open("config.development.yaml", "r") as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}

# -------------------- Q1 --------------------
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

# -------------------- Q2 --------------------
@app.post("/verify")
def verify_token(data: TokenRequest):

    try:
        payload = jwt.decode(
            data.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
        }

    except jwt.PyJWTError:
        return JSONResponse(
            status_code=401,
            content={
                "valid": False
            },
        )

# -------------------- Q3 --------------------
@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    # Layer 1 - Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # Layer 2 - YAML
    yaml_config = load_yaml_config()

    config.update(yaml_config)

    # Layer 3 - .env ONLY
    env_file = dotenv_values(".env")

    if env_file.get("NUM_WORKERS"):
        config["workers"] = int(env_file["NUM_WORKERS"])

    if env_file.get("APP_DEBUG"):
        config["debug"] = to_bool(env_file["APP_DEBUG"])

    if env_file.get("APP_LOG_LEVEL"):
        config["log_level"] = env_file["APP_LOG_LEVEL"]

    if env_file.get("APP_API_KEY"):
        config["api_key"] = env_file["APP_API_KEY"]

    # Layer 4 - OS Environment Variables
    if "APP_PORT" in os.environ:
        config["port"] = int(os.environ["APP_PORT"])

    if "APP_WORKERS" in os.environ:
        config["workers"] = int(os.environ["APP_WORKERS"])

    if "APP_DEBUG" in os.environ:
        config["debug"] = to_bool(os.environ["APP_DEBUG"])

    if "APP_LOG_LEVEL" in os.environ:
        config["log_level"] = os.environ["APP_LOG_LEVEL"]

    if "APP_API_KEY" in os.environ:
        config["api_key"] = os.environ["APP_API_KEY"]

    # Layer 5 - CLI overrides
    for item in set:

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in ["port", "workers"]:
            config[key] = int(value)

        elif key == "debug":
            config[key] = to_bool(value)

        else:
            config[key] = value

    # Mask secret
    config["api_key"] = "****"

    return config