import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA = json.loads((Path(__file__).parent.parent / "telemetry.json").read_text())

# Adjust these three keys if your bundle uses different names
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
            out[region] = {"avg_latency": None, "p95_latency": None,
                           "avg_uptime": None, "breaches": 0}
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

  
