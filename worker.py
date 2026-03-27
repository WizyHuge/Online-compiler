import redis
import json
import subprocess
import sys
import tempfile
import os

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

while True:
    task_raw = r.brpop("tasks", timeout=5)
    if not task_raw:
        continue

    _, task_json = task_raw
    task = json.loads(task_json)
    task_id = task["id"]
    code = task["code"]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        result = {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired:
        result = {"error": "Превышено время выполнения (10 сек)"}
    except Exception as e:
        result = {"error": str(e)}
    finally:
        os.unlink(tmp_path)

    r.setex(f"result:{task_id}", 60, json.dumps(result))