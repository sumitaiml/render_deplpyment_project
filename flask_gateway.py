"""
Single-command gateway for HRTech Platform.

Starts FastAPI backend (if not already running), serves frontend with Flask,
and proxies /api calls to backend so frontend and backend run from one command.

Run:
    python flask_gateway.py
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, redirect, request, send_from_directory

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
BACKEND_BASE_URL = "http://127.0.0.1:8000"
GATEWAY_HOST = "0.0.0.0"
GATEWAY_PUBLIC_HOST = "localhost"
GATEWAY_PORT = int(os.environ.get("PORT", "10000"))
IS_RENDER = os.environ.get("RENDER") == "true"

FRONTEND_FILE = "index_professional.html" if (ROOT_DIR / "index_professional.html").exists() else "index.html"
LOADING_FILE = "loading_dashboard.html"
LOGIN_FILE = "login.html"
SIGNUP_FILE = "signup.html"

app = Flask(__name__, static_folder=str(ROOT_DIR), static_url_path="")
_backend_process: subprocess.Popen | None = None


def _is_backend_running() -> bool:
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _is_gateway_running() -> bool:
    try:
        response = requests.get(f"http://{GATEWAY_PUBLIC_HOST}:{GATEWAY_PORT}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _start_backend() -> None:
    global _backend_process

    if _is_backend_running():
        print("[gateway] Backend already running on http://127.0.0.1:8000")
        return

    if not BACKEND_DIR.exists():
        raise RuntimeError(f"Backend directory not found: {BACKEND_DIR}")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    if not IS_RENDER:
        cmd.append("--reload")

    print("[gateway] Starting backend...")
    _backend_process = subprocess.Popen(cmd, cwd=str(BACKEND_DIR))

    warmup_seconds = 120 if IS_RENDER else 45
    for _ in range(warmup_seconds):
        if _is_backend_running():
            print("[gateway] Backend is ready.")
            return
        if _backend_process.poll() is not None:
            print(f"[gateway] Backend process exited with code {_backend_process.returncode}")
            return
        time.sleep(1)

    print("[gateway] Backend is taking longer than expected to become ready.")


def _start_backend_async() -> None:
    thread = threading.Thread(target=_start_backend, daemon=True)
    thread.start()


def _ensure_backend_running(max_wait_seconds: int = 120) -> bool:
    if _is_backend_running():
        return True

    _start_backend_async()
    for _ in range(max_wait_seconds):
        if _is_backend_running():
            return True
        time.sleep(1)
    return False


def _stop_backend() -> None:
    if _backend_process and _backend_process.poll() is None:
        print("[gateway] Stopping backend process...")
        _backend_process.terminate()
        try:
            _backend_process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            _backend_process.kill()


@atexit.register
def _cleanup() -> None:
    _stop_backend()


@app.route("/")
def root() -> Response:
    if (ROOT_DIR / LOADING_FILE).exists():
        return send_from_directory(ROOT_DIR, LOADING_FILE)
    return send_from_directory(ROOT_DIR, FRONTEND_FILE)


@app.route("/app")
def main_app() -> Response:
    return send_from_directory(ROOT_DIR, FRONTEND_FILE)


@app.route("/login")
def login_page() -> Response:
    return send_from_directory(ROOT_DIR, LOGIN_FILE)


@app.route("/signup")
def signup_page() -> Response:
    return send_from_directory(ROOT_DIR, SIGNUP_FILE)


@app.route("/<path:filename>")
def serve_file(filename: str):
    candidate = ROOT_DIR / filename
    if candidate.is_file():
        return send_from_directory(ROOT_DIR, filename)
    return redirect("/")


@app.route("/health")
def gateway_health():
    return jsonify(
        {
            "status": "ok",
            "service": "hrtech-platform-gateway",
            "frontend": FRONTEND_FILE,
            "backend_running": _is_backend_running(),
        }
    )


@app.route("/api/health")
def gateway_api_health():
    return jsonify(
        {
            "status": "ok",
            "service": "hrtech-platform-gateway",
            "backend_running": _is_backend_running(),
        }
    )


@app.route("/docs")
def docs_redirect():
    return redirect(f"{BACKEND_BASE_URL}/docs")


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def proxy_api(path: str):
    if not _ensure_backend_running():
        return jsonify({"detail": "Backend is starting. Please retry in a few seconds."}), 503

    target_url = f"{BACKEND_BASE_URL}/api/{path}"

    request_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length", "accept-encoding", "connection"}
    }

    last_error: Exception | None = None
    for attempt in range(1, 13):
        try:
            upstream_response = requests.request(
                method=request.method,
                url=target_url,
                headers=request_headers,
                params=request.args,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=180,
            )
            break
        except requests.ConnectionError as exc:
            last_error = exc
            if attempt == 12:
                return jsonify({"detail": f"Gateway error while contacting backend: {exc}"}), 502
            time.sleep(1)
            continue
        except requests.RequestException as exc:
            return jsonify({"detail": f"Gateway error while contacting backend: {exc}"}), 502
    else:
        return jsonify({"detail": f"Gateway error while contacting backend: {last_error}"}), 502

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [
        (name, value)
        for name, value in upstream_response.headers.items()
        if name.lower() not in excluded
    ]

    return Response(upstream_response.content, upstream_response.status_code, response_headers)


def main() -> None:
    app_url = f"http://{GATEWAY_PUBLIC_HOST}:{GATEWAY_PORT}"
    print("[gateway] ------------------------------------------------------------")
    print(f"[gateway] Frontend: {app_url}")
    print(f"[gateway] Gateway health: {app_url}/health")
    print(f"[gateway] Backend docs: {app_url}/docs")
    print("[gateway] Press Ctrl+C to stop gateway and backend.")
    print("[gateway] ------------------------------------------------------------")

    _start_backend_async()

    if not IS_RENDER:
        try:
            webbrowser.open(app_url)
        except Exception:
            pass

    app.run(host=GATEWAY_HOST, port=GATEWAY_PORT, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
