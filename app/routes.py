import subprocess
import threading
from flask import render_template, request, jsonify
import shlex
import yaml
import os
from . import app

wrapper_process = None
wrapper_running = False

def stream_wrapper_logs(pipe, target_list):
    """Thread target to read logs from wrapper process and store them."""
    global wrapper_running, wrapper_process
    login_successful = False
    
    try:
        for line in iter(pipe.readline, ''):
            line = line.strip()
            if line:
                target_list.append(line)
                print(f"[WRAPPER LOG] {line}")  # Debug print
                
                # Check for successful login message
                if "[.] response type 6" in line:
                    wrapper_running = True
                    login_successful = True
                    target_list.append("✅ Wrapper login successful! Ready for downloads.")
                    
    except Exception as e:
        target_list.append(f"Error reading wrapper logs: {str(e)}")
    finally:
        # Check if process ended
        if wrapper_process and wrapper_process.poll() is not None:
            exit_code = wrapper_process.poll()
            if not login_successful:
                # Process ended before successful login
                target_list.append(f"❌ Login failed - wrapper process exited with code: {exit_code}")
                wrapper_running = False
            elif exit_code != 0:
                target_list.append(f"❌ Wrapper process ended unexpectedly with exit code: {exit_code}")
                wrapper_running = False
            else:
                target_list.append("Wrapper process ended normally")
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
    wrapper_logs.append(f"Starting wrapper login for {email}...")
    
    # Use absolute path and proper command format
    import os
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wrapper_dir = os.path.join(script_dir, "wrapper")
    wrapper_path = os.path.join(wrapper_dir, "wrapper")
    
    cmd = [wrapper_path, "-L", f"{email}:{password}"]
    wrapper_logs.append(f"Executing: {' '.join(cmd)}")
    wrapper_logs.append(f"Working directory: {wrapper_dir}")
    
    try:
        wrapper_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            cwd=wrapper_dir  # Run from wrapper directory
        )
        
        # Don't set wrapper_running=True yet, wait for the success message
        threading.Thread(target=stream_wrapper_logs, args=(wrapper_process.stdout, wrapper_logs), daemon=True).start()
        
        wrapper_logs.append("Wrapper process started, waiting for login confirmation...")
        return jsonify({"status": "ok", "msg": "Wrapper process started, waiting for login..."})
        
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
    global wrapper_running, wrapper_process
    
    # Check if wrapper process is still running
    if wrapper_process and wrapper_process.poll() is not None:
        if wrapper_running:  # Process ended but we thought it was still running
            wrapper_running = False
    
    return jsonify({
        "wrapper": wrapper_logs[-200:],  # last 200 lines
        "downloader": downloader_logs[-200:],
        "wrapper_running": wrapper_running
    })

@app.route("/stop_wrapper", methods=["POST"])
def stop_wrapper():
    global wrapper_process, wrapper_running, wrapper_logs
    
    if wrapper_process and wrapper_process.poll() is None:
        wrapper_process.terminate()
        wrapper_logs.append("Wrapper process terminated by user")
        wrapper_running = False
        return jsonify({"status": "ok", "msg": "Wrapper stopped"})
    else:
        return jsonify({"status": "error", "msg": "Wrapper not running"})

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/get_config")
def get_config():
    try:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, "apple-music-downloader", "config.yaml")
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return jsonify({"status": "ok", "config": config})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route("/save_config", methods=["POST"])
def save_config():
    try:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, "apple-music-downloader", "config.yaml")
        
        config_data = request.json
        
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config_data, file, default_flow_style=False, allow_unicode=True)
            
        return jsonify({"status": "ok", "msg": "Configuration saved successfully"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})
