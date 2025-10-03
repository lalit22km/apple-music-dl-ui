from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Fake state (later we’ll hook it to your wrapper program)
wrapper_running = False

@app.route("/")
def index():
    return render_template("index.html", wrapper_running=wrapper_running)

@app.route("/toggle_wrapper", methods=["POST"])
def toggle_wrapper():
    global wrapper_running
    wrapper_running = not wrapper_running
    return jsonify({"running": wrapper_running})

@app.route("/download", methods=["POST"])
def download():
    link = request.form.get("link")
    format_choice = request.form.get("format")
    # For now just simulate
    return jsonify({"status": "ok", "msg": f"Started download: {link} [{format_choice}]"})

if __name__ == "__main__":
    app.run(debug=True)
