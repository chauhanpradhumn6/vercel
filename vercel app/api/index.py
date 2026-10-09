import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
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


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/")
@app.post("/api")
@app.post("/api/index")
def check(q: Query):
    out = {}
    for region in q.regions:
        rows = [r for r in DATA if r[REGION_KEY] == region]
        if not rows:
            out[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue
        lat = np.array([r[LATENCY_KEY] for r in rows], dtype=float)
        up = np.array([r[UPTIME_KEY] for r in rows], dtype=float)
        out[region] = {
            "avg_latency": float(lat.mean()),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(up.mean()),
            "breaches": int((lat > q.threshold_ms).sum()),
        }
    return {"regions": out}
