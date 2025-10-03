import subprocess
import threading
from flask import render_template, request, jsonify
import shlex
from . import app

wrapper_process = None
wrapper_running = False

def stream_wrapper_logs(pipe, target_list):
    """Thread target to read logs from wrapper process and store them."""
    global wrapper_running
    for line in iter(pipe.readline, b''):
        line = line.decode(errors="ignore").strip()
        if line:
            target_list.append(line)
    wrapper_running = False
    pipe.close()

wrapper_logs = []
downloader_logs = []


@app.route("/")
def index():
    return render_template("index.html", wrapper_running=wrapper_running)


@app.route("/login_wrapper", methods=["POST"])
def login_wrapper():
    global wrapper_process, wrapper_running, wrapper_logs
    email = request.form.get("email")
    password = request.form.get("password")

    if wrapper_process and wrapper_process.poll() is None:
        return jsonify({"status": "error", "msg": "Wrapper already running"})

    wrapper_logs = []  # reset logs
    cmd = f"./wrapper/wrapper -L {email}:{password}"
    wrapper_process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1
    )

    wrapper_running = True
    threading.Thread(target=stream_wrapper_logs, args=(wrapper_process.stdout, wrapper_logs), daemon=True).start()

    return jsonify({"status": "ok", "msg": "Wrapper started"})


@app.route("/download", methods=["POST"])
def download():
    link = request.form.get("link")
    format_choice = request.form.get("format")
    if not wrapper_running:
        return jsonify({"status": "error", "msg": "Wrapper not running"})
    msg = f"Started download: {link} [{format_choice}]"
    downloader_logs.append(msg)
    return jsonify({"status": "ok", "msg": msg})


@app.route("/get_logs")
def get_logs():
    return jsonify({
        "wrapper": wrapper_logs[-200:],  # last 200 lines
        "downloader": downloader_logs[-200:]
    })
