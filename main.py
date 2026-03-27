# ______________import_____________
from flask import Flask, render_template, url_for, request, jsonify

import tempfile
import subprocess
import os
import sys

from data import db


#_______________init_______________

app = Flask(__name__)

# ______________routes____________

@app.route('/')
def index():
    return render_template('index.html', title='Main page')

@app.route('/api/run')
@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "Код пустой"}), 400

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Превышено время выполнения ({10}с)"}), 408

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        os.unlink(tmp_path)



# ______________start_____________
def main():
    db.global_init("db/database.db")
    app.run(debug=True)

if __name__ == '__main__':
    main()