# ______________import_____________
from flask import Flask, request, jsonify, render_template, Response, url_for

import redis
import json
import uuid
import time


#_______________init_______________

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ______________routes____________

@app.route('/')
def index():
    return render_template('index.html', title='Main page')

@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "Код пустой"}), 400

    ip = request.remote_addr
    rate_key = f"rate:{ip}"
    count = r.incr(rate_key)
    if count == 1:
        r.expire(rate_key, 60)
    if count > 5:
        return jsonify({"error": "Слишком много запросов, подожди минуту"}), 429

    task_id = str(uuid.uuid4())
    task = {"id": task_id, "code": code}
    r.lpush("tasks", json.dumps(task))

    return jsonify({"task_id": task_id})

@app.route("/api/stream/<task_id>")
def stream(task_id):
    def generate():
        for _ in range(150):
            result = r.get(f"result:{task_id}")
            if result:
                yield f"data: {result}\n\n"
                return
            time.sleep(0.1)
        yield f"data: {json.dumps({'error': 'Таймаут выполнения'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")



# ______________start_____________
def main():
    app.run(debug=True)

if __name__ == "__main__":
    main()