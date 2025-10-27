
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
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
CPU_TIME_LIMIT = 5
NSJAIL_PATH = "/usr/sbin/nsjail"
PYTHON_BIN = "/usr/local/bin/python" if os.path.exists("/usr/local/bin/python") else "/usr/bin/python3"



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
    
    # Write user script
    with open(user_script_path, "w", encoding="utf-8") as f:
        # Important: ensure user module name is importable; runner imports 'user_script'
        f.write(script)

    # Write runner that imports the user_script and executes main()
        runner_code = r'''
    import importlib.util
    import json
    import sys
    import traceback
    from types import ModuleType

    # Import user_script.py from the same directory
    spec = importlib.util.spec_from_file_location("user_script", "user_script.py")
    user_mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(user_mod)
    except Exception as e:
        # Any import-time errors should be reported as an execution failure
        sys.stderr.write(json.dumps({"__error__": f"Error executing script import: {traceback.format_exc()}})}) + "\n")
        sys.exit(1)

    if not hasattr(user_mod, "main"):
        sys.stderr.write(json.dumps({"__error__": "No 'main' function found after import"}) + "\n")
        sys.exit(1)

    try:
        # Capture return value of main()
        result = user_mod.main()
    except Exception:
        import traceback as _tb
        sys.stderr.write(json.dumps({"__error__": f"Error while running main(): {_tb.format_exc()}"}) + "\n")
        sys.exit(1)

    # Validate result is JSON serializable
    try:
        json.dumps(result)
    except TypeError:
        sys.stderr.write(json.dumps({"__error__": "Return value from main() is not JSON serializable"}) + "\n")
        sys.exit(1)

    # Write the JSON-serializable result to stderr as a single JSON line.
    # stdout remains available for the user's print() output; the parent process will collect both streams.
    sys.stderr.write(json.dumps({"__result__": result}) + "\n")
    sys.exit(0)
    '''
        
    # Note: runner writes result JSON to stderr
    with open(runner_path, "w", encoding="utf-8") as f:
        f.write(runner_code)

    # Build nsjail command
    nsjail_cmd = [
        NSJAIL_PATH,
        "--stderr_to_null", "false",          # keep stderr
        "--cwd", tmpdir,
        "--time_limit", str(TIME_LIMIT_SECONDS),
        "--rlimit_as", str(MEMORY_LIMIT_BYTES),
        "--rlimit_cpu", str(CPU_TIME_LIMIT),
        "--max_cpus", "1",
        # network isolation flags - if nsjail supports them
        "--disable_clone_newnet",
        "--user", "65534",
        "--group", "65534",
        "--",  # end of nsjail options, program follows
        PYTHON_BIN,
        runner_path
    ]


    result,exec_error  = None, None
    
    return jsonify({"result": result, "stdout": ""}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)