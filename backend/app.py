import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from transform import run_transform

load_dotenv()

app = Flask(__name__)
CORS(app)


@app.route("/api/transform", methods=["POST"])
def transform():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body is required"}), 400

    origin = body.get("origin", "").strip()
    destination = body.get("destination", "").strip()

    if not origin or not destination:
        return jsonify({"error": "Both 'origin' and 'destination' are required"}), 400

    try:
        result = run_transform(origin, destination)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
