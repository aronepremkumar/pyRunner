
from flask import Flask, request, jsonify, abort
import os
import json
import subprocess
import sys
import ast
import uuid
import tempfile


app = Flask("PyRunner")

MAX_SCRIPT_SIZE = 200 * 1024
TIME_LIMIT_SECONDS = 5


def validate_script_has_main(script_src: str):
    """
    Parse AST and ensure there's a function def named 'main' with no args or with args optional.
    """
    try:
        tree = ast.parse(script_src)
    except SyntaxError as e:
        raise ValueError(f"SyntaxError parsing script: {e}")

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            return True
    raise ValueError("No function named 'main' found in script.")

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
    
    # Validate presence of main()
    try:
        validate_script_has_main(script)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    # Create a temp directory to hold script and runner
    run_id = str(uuid.uuid4())
    tmpdir = tempfile.mkdtemp(prefix=f"exec_{run_id}_")

    user_script_path = os.path.join(tmpdir, "user_script.py")
    runner_path = os.path.join(tmpdir, "runner.py")
    
    
    result,exec_error  = None, None
    
    return jsonify({"result": result, "stdout": ""}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)