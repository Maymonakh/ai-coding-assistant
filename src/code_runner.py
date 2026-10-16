import subprocess
import sys
import uuid


DOCKER_IMAGE = "python:3.12-alpine"

MAX_CODE_LENGTH = 10_000
MAX_OUTPUT_LENGTH = 5_000
TIMEOUT_SECONDS = 10

ALLOW_LOCAL_RUN = False


def run_python_code(code):
    """Run Python code inside an isolated Docker container.

    Returns {"success": True/False, "output": "..."}
    """

    if not code.strip():
        return {"success": False, "output": "Please enter some Python code."}

    if len(code) > MAX_CODE_LENGTH:
        return {"success": False, "output": "Code is too long (max 10,000 characters)."}

    container_name = "code-runner-" + uuid.uuid4().hex[:12]

    # The safety options: no internet, small memory, no extra permissions
    command = [
        "docker", "run", "--rm",
        "--name", container_name,
        "--network", "none",
        "--memory", "128m",
        "--cpus", "0.5",
        "--pids-limit", "64",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--user", "1000:1000",
        DOCKER_IMAGE,
        "python", "-I", "-c", code
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS
        )

    except subprocess.TimeoutExpired:
        # Stop the container, because it may still be running
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        return {"success": False, "output": "Execution timed out. Please simplify your code."}

    except FileNotFoundError:
        if ALLOW_LOCAL_RUN:
            return run_locally(code)
        return {
            "success": False,
            "output": "Docker was not found. Please install Docker Desktop and start it."
        }

    output = (result.stdout + result.stderr)[:MAX_OUTPUT_LENGTH]

    return {
        "success": result.returncode == 0,
        "output": output or "(no output)"
    }


def run_locally(code):
    """Run code directly on this computer (only if ALLOW_LOCAL_RUN = True)."""
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-c", code],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Execution timed out."}

    output = (result.stdout + result.stderr)[:MAX_OUTPUT_LENGTH]

    return {
        "success": result.returncode == 0,
        "output": output or "(no output)"
    }
