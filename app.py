from flask import Flask, request
from markupsafe import escape
import subprocess
import hashlib
import json
import shlex
import os

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
DEBUG_MODE = False

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>SecureScan Demo</h1>
    <p>Python application for security scanning demonstration (hardened).</p>
    <ul>
        <li><a href="/ping">Health Check</a></li>
        <li><a href="/greet?name=User">Greet Example</a></li>
        <li><a href="/run?cmd=echo+hello">Run Command (secured)</a></li>
        <li><a href="/hash?data=test">Hash Example (SHA-256)</a></li>
    </ul>
    """


@app.route("/ping")
def ping():
    return "<h2>Application is running!</h2>"


@app.route("/greet")
def greet():
    name = request.args.get("name", "Guest")
    return f"<h2>Hello, {escape(name)}!</h2>"


@app.route("/run")
def run_command():
    cmd_input = request.args.get("cmd", "echo Hello")
    try:
        parsed = shlex.split(cmd_input)
        result = subprocess.run(
            parsed,
            shell=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout if result.stdout else result.stderr
    except Exception as e:
        output = f"Error: {escape(str(e))}"
    return f"<pre>{escape(output)}</pre>"


@app.route("/hash")
def hash_data():
    data = request.args.get("data", "")
    hashed = hashlib.sha256(data.encode()).hexdigest()
    return f"<pre>SHA-256({escape(data)}) = {hashed}</pre>"


@app.route("/load", methods=["POST"])
def load_data():
    try:
        raw = request.get_data(as_text=True)
        obj = json.loads(raw)
        return f"<pre>Loaded: {escape(repr(obj))}</pre>"
    except Exception as e:
        return f"<pre>Error: {escape(str(e))}</pre>"


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=DEBUG_MODE)
