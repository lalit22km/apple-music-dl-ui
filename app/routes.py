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
    try:
        for line in iter(pipe.readline, ''):
            line = line.strip()
            if line:
                target_list.append(line)
                print(f"[WRAPPER LOG] {line}")  # Debug print
    except Exception as e:
        target_list.append(f"Error reading wrapper logs: {str(e)}")
    finally:
        wrapper_running = False
        target_list.append("Wrapper process ended")
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
    wrapper_logs.append(f"Starting wrapper login for {email}...")
    
    # Use absolute path and proper command format
    import os
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wrapper_path = os.path.join(script_dir, "wrapper", "wrapper")
    
    cmd = [wrapper_path, "-L", f"{email}:{password}"]
    wrapper_logs.append(f"Executing: {' '.join(cmd)}")
    
    try:
        wrapper_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        
        wrapper_running = True
        threading.Thread(target=stream_wrapper_logs, args=(wrapper_process.stdout, wrapper_logs), daemon=True).start()
        
        wrapper_logs.append("Wrapper process started successfully")
        return jsonify({"status": "ok", "msg": "Wrapper started"})
        
    except Exception as e:
        wrapper_logs.append(f"Error starting wrapper: {str(e)}")
        return jsonify({"status": "error", "msg": f"Failed to start wrapper: {str(e)}"})


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
