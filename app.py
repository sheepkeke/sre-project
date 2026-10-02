from flask import Flask, Response, request
import os, redis, pymysql
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter('flask_requests_total', 'Total requests', ['method', 'endpoint'])

@app.before_request
def count_request():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()

@app.route("/")
def index():
    return "Hello from K8s SRE Project"

@app.route("/health")
def health():
    return "ok", 200

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/db")
def db():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "mysql"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "root123"),
        database=os.getenv("DB_NAME", "test")
    )
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        return str(cur.fetchone())

@app.route("/redis")
def redis_check():
    r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)
    r.set("key", "value")
    return r.get("key").decode()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
