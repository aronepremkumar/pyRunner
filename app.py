
from flask import Flask, request, jsonify, abort
import os
import json
import subprocess
import sys
app = Flask("PyRunner")

MAX_SCRIPT_SIZE = 200 * 1024
TIME_LIMIT_SECONDS = 5

@app.route("/execute", methods=["POST"])
def execute():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON with 'script' field"}), 400
    body = request.get_json()
    if "script" not in body:
        return jsonify({"error": "Missing 'script' field in JSON body"}), 400
    script = body["script"]
    if not isinstance(script, str):
        return jsonify({"error": "'script' must be a string"}), 400
    if len(script.encode("utf-8")) > MAX_SCRIPT_SIZE:
        return jsonify({"error": f"Script too large (max {MAX_SCRIPT_SIZE} bytes)"}), 400
    
    
    result,exec_error  = None, None
    
    return jsonify({"result": result, "stdout": ""}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)