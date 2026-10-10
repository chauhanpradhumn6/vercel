import json
import io
import re
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin, Content-Type",
    "Access-Control-Max-Age": "86400",
}


@app.middleware("http")
async def add_cors(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=204, headers=CORS_HEADERS)
    try:
        response = await call_next(request)
    except Exception as e:
        response = JSONResponse({"error": str(e)}, status_code=500)
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v
    return response


DATA = json.loads((Path(__file__).parent.parent / "telemetry.json").read_text())
REGION_KEY, LATENCY_KEY, UPTIME_KEY = "region", "latency_ms", "uptime_pct"


def run_latency(body: dict):
    regions = body.get("regions")
    threshold = body.get("threshold_ms")
    if not isinstance(regions, list) or threshold is None:
        return JSONResponse({"detail": "regions and threshold_ms required"}, status_code=422)
    out = {}
    for region in regions:
        rows = [r for r in DATA if r[REGION_KEY] == region]
        if not rows:
            out[region] = {"avg_latency": None, "p95_latency": None,
                           "avg_uptime": None, "breaches": 0}
            continue
        lat = np.array([r[LATENCY_KEY] for r in rows], dtype=float)
        up = np.array([r[UPTIME_KEY] for r in rows], dtype=float)
        out[region] = {
            "avg_latency": float(lat.mean()),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(up.mean()),
            "breaches": int((lat > float(threshold)).sum()),
        }
    return {"regions": out}


def execute_python_code(code: str) -> dict:
    buf = io.StringIO()
    env = {"__name__": "__main__"}
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            exec(compile(code, "<string>", "exec"), env)
        return {"success": True, "output": buf.getvalue()}
    except BaseException as e:
        tb = e.__traceback__.tb_next if e.__traceback__ else None
        output = (
            "Traceback (most recent call last):\n"
            + "".join(traceback.format_tb(tb))
            + "".join(traceback.format_exception_only(type(e), e))
        )
        return {"success": False, "output": output}


def run_code(code: str):
    result = execute_python_code(code)
    if result["success"]:
        return {"error": [], "result": result["output"]}
    nums = re.findall(r'File "<string>", line (\d+)', result["output"])
    return {"error": [int(nums[-1])] if nums else [], "result": result["output"]}


@app.post("/")
@app.post("/api")
@app.post("/api/index")
@app.post("/code-interpreter")
@app.post("/api/code-interpreter")
async def dispatch(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "invalid JSON"}, status_code=422)
    if isinstance(body, dict) and "code" in body:
        return run_code(body["code"])
    if isinstance(body, dict):
        return run_latency(body)
    return JSONResponse({"detail": "invalid body"}, status_code=422)
