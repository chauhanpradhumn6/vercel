from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import statistics

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA = [
  {"region": "apac", "service": "payments", "latency_ms": 226.3, "uptime_pct": 97.865, "timestamp": 20250301},
  {"region": "apac", "service": "recommendations", "latency_ms": 126.2, "uptime_pct": 98.32, "timestamp": 20250302},
  {"region": "apac", "service": "analytics", "latency_ms": 152.4, "uptime_pct": 97.937, "timestamp": 20250303},
  {"region": "apac", "service": "recommendations", "latency_ms": 176.51, "uptime_pct": 98.917, "timestamp": 20250304},
  {"region": "apac", "service": "support", "latency_ms": 173.67, "uptime_pct": 99.162, "timestamp": 20250305},
  {"region": "apac", "service": "recommendations", "latency_ms": 174.81, "uptime_pct": 99.112, "timestamp": 20250306},
  {"region": "apac", "service": "analytics", "latency_ms": 210.46, "uptime_pct": 97.503, "timestamp": 20250307},
  {"region": "apac", "service": "recommendations", "latency_ms": 182.6, "uptime_pct": 97.164, "timestamp": 20250308},
  {"region": "apac", "service": "checkout", "latency_ms": 218.69, "uptime_pct": 97.159, "timestamp": 20250309},
  {"region": "apac", "service": "analytics", "latency_ms": 163.46, "uptime_pct": 98.545, "timestamp": 20250310},
  {"region": "apac", "service": "analytics", "latency_ms": 123.37, "uptime_pct": 97.429, "timestamp": 20250311},
  {"region": "apac", "service": "support", "latency_ms": 157.96, "uptime_pct": 97.584, "timestamp": 20250312},
  {"region": "emea", "service": "checkout", "latency_ms": 178.16, "uptime_pct": 97.735, "timestamp": 20250301},
  {"region": "emea", "service": "catalog", "latency_ms": 158.88, "uptime_pct": 98.907, "timestamp": 20250302},
  {"region": "emea", "service": "payments", "latency_ms": 152.67, "uptime_pct": 98.086, "timestamp": 20250303},
  {"region": "emea", "service": "payments", "latency_ms": 153.56, "uptime_pct": 98.738, "timestamp": 20250304},
  {"region": "emea", "service": "recommendations", "latency_ms": 226.7, "uptime_pct": 97.43, "timestamp": 20250305},
  {"region": "emea", "service": "recommendations", "latency_ms": 175.54, "uptime_pct": 97.261, "timestamp": 20250306},
  {"region": "emea", "service": "recommendations", "latency_ms": 195.62, "uptime_pct": 98.64, "timestamp": 20250307},
  {"region": "emea", "service": "analytics", "latency_ms": 145.52, "uptime_pct": 98.491, "timestamp": 20250308},
  {"region": "emea", "service": "analytics", "latency_ms": 207.12, "uptime_pct": 97.166, "timestamp": 20250309},
  {"region": "emea", "service": "payments", "latency_ms": 200.21, "uptime_pct": 98.609, "timestamp": 20250310},
  {"region": "emea", "service": "analytics", "latency_ms": 163.65, "uptime_pct": 97.503, "timestamp": 20250311},
  {"region": "emea", "service": "analytics", "latency_ms": 184.54, "uptime_pct": 97.708, "timestamp": 20250312},
  {"region": "amer", "service": "analytics", "latency_ms": 206.88, "uptime_pct": 99.151, "timestamp": 20250301},
  {"region": "amer", "service": "payments", "latency_ms": 155.48, "uptime_pct": 99.02, "timestamp": 20250302},
  {"region": "amer", "service": "checkout", "latency_ms": 123.6, "uptime_pct": 97.872, "timestamp": 20250303},
  {"region": "amer", "service": "recommendations", "latency_ms": 158.5, "uptime_pct": 98.166, "timestamp": 20250304},
  {"region": "amer", "service": "support", "latency_ms": 149.7, "uptime_pct": 98.166, "timestamp": 20250305},
  {"region": "amer", "service": "analytics", "latency_ms": 185.53, "uptime_pct": 97.488, "timestamp": 20250306},
  {"region": "amer", "service": "analytics", "latency_ms": 149.07, "uptime_pct": 99.343, "timestamp": 20250307},
  {"region": "amer", "service": "payments", "latency_ms": 206.54, "uptime_pct": 99.493, "timestamp": 20250308},
  {"region": "amer", "service": "analytics", "latency_ms": 207.42, "uptime_pct": 98.254, "timestamp": 20250309},
  {"region": "amer", "service": "recommendations", "latency_ms": 165.54, "uptime_pct": 98.633, "timestamp": 20250310},
  {"region": "amer", "service": "analytics", "latency_ms": 121.53, "uptime_pct": 97.928, "timestamp": 20250311},
  {"region": "amer", "service": "recommendations", "latency_ms": 207.34, "uptime_pct": 98.109, "timestamp": 20250312},
]

def percentile(values, p):
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = k - f
    if f + 1 < len(s):
        return s[f] + c * (s[f + 1] - s[f])
    return s[f]

@app.post("/")
async def latency(request: Request):
    body = await request.json()
    regions = body["regions"]
    threshold = body["threshold_ms"]
    result = []
    for region in regions:
        rows = [r for r in DATA if r["region"] == region]
        lat = [r["latency_ms"] for r in rows]
        up = [r["uptime_pct"] for r in rows]
        result.append({
            "region": region,
            "avg_latency": round(statistics.mean(lat), 2),
            "p95_latency": round(percentile(lat, 0.95), 2),
            "avg_uptime": round(statistics.mean(up), 3),
            "breaches": sum(1 for v in lat if v > threshold),
        })
    return {"regions": result}