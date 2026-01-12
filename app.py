from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
from bson.objectid import ObjectId


app = Flask(__name__)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["crash_reporter"]
crashes = db["crashes"]

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/crashes", methods=["POST"])
def create_crash():
    data = request.get_json(silent=True) or {}

    crash = {
        "event_id": data.get("event_id"),
        "message": data.get("message"),
        "stacktrace": data.get("stacktrace"),
        "fatal": data.get("fatal", True),
        "thread": data.get("thread"),
        "package": data.get("package"),
        "device": data.get("device"),
        "android_version": data.get("android_version"),
        "raw": data,
        "timestamp": datetime.utcnow()
    }

    result = crashes.insert_one(crash)
    return jsonify({"status": "saved", "id": str(result.inserted_id), "event_id": crash["event_id"]}), 201

@app.route("/crashes", methods=["GET"])
def get_crashes():
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 200))

    items = []
    for c in crashes.find().sort("timestamp", -1).limit(limit):
        c["_id"] = str(c["_id"])
        items.append(c)

    return jsonify(items)

@app.route("/crashes/<crash_id>", methods=["GET"])
def get_crash(crash_id):
    try:
        doc = crashes.find_one({"_id": ObjectId(crash_id)})
    except Exception:
        return jsonify({"error": "invalid id"}), 400

    if not doc:
        return jsonify({"error": "not found"}), 404

    doc["_id"] = str(doc["_id"])
    return jsonify(doc)

@app.route("/crashes/<crash_id>", methods=["DELETE"])
def delete_crash(crash_id):
    try:
        result = crashes.delete_one({"_id": ObjectId(crash_id)})
    except Exception:
        return jsonify({"error": "invalid id"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "not found"}), 404

    return jsonify({"status": "deleted"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

