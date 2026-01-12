from flask import Flask, request, jsonify, render_template_string
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
        ts = c.get("timestamp")
        if isinstance(ts, datetime):
            c["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
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
    ts = doc.get("timestamp")
    if isinstance(ts, datetime):
        doc["timestamp"] = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
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

DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Crash Reporter Admin</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    h1 { margin-bottom: 6px; }
    .small { font-size: 12px; color: #666; margin-bottom: 14px; }
    .controls { display: flex; gap: 10px; align-items: center; margin-bottom: 14px; }
    input { padding: 8px; width: 140px; }
    button { padding: 8px 12px; cursor: pointer; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }
    th { background: #f5f5f5; text-align: left; }
    .tag { padding: 2px 8px; border-radius: 12px; font-size: 12px; display: inline-block; }
    .fatal { background: #ffe5e5; }
    .nonfatal { background: #e6f3ff; }
    pre { white-space: pre-wrap; word-break: break-word; margin: 0; max-width: 700px; }
    .row-actions { white-space: nowrap; }
  </style>
</head>
<body>
  <h1>Crash Reporter Admin</h1>
  <div class="small">Minimal admin portal: list + view + delete</div>

  <div class="controls">
    <label>Limit:</label>
    <input id="limit" type="number" min="1" max="200" value="50" />
    <button onclick="loadCrashes()">Refresh</button>
  </div>

  <table id="tbl">
    <thead>
      <tr>
        <th>Time</th>
        <th>Package</th>
        <th>Message</th>
        <th>Type</th>
        <th>Device</th>
        <th>Android</th>
        <th>Stacktrace</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

<script>
function esc(s) {
  return (s ?? '').toString()
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'","&#039;");
}

async function loadCrashes() {
  const limit = document.getElementById('limit').value || 50;
  const res = await fetch('/crashes?limit=' + encodeURIComponent(limit));
  const data = await res.json();

  const tbody = document.querySelector('#tbl tbody');
  tbody.innerHTML = '';

  data.forEach(c => {
    const raw = c.raw || {};

    const msg = raw.message || c.message || '';
    const pkg = raw.package || c.package || '';
    const device = raw.device || c.device || '';
    const androidV = raw.android_version || c.android_version || '';
    const stack = raw.stacktrace || c.stacktrace || '';

    const typeLabel = c.fatal ? 'FATAL' : 'NON-FATAL';
    const typeClass = c.fatal ? 'tag fatal' : 'tag nonfatal';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${esc(c.timestamp || '')}</td>
      <td>${esc(pkg)}</td>
      <td>${esc(msg)}</td>
      <td><span class="${typeClass}">${typeLabel}</span></td>
      <td>${esc(device)}</td>
      <td>${esc(androidV)}</td>
      <td><pre>${esc(stack)}</pre></td>
      <td class="row-actions">
        <button onclick="openJson('${c._id}')">View</button>
        <button onclick="deleteCrash('${c._id}')">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function deleteCrash(id) {
  if (!confirm('Delete this crash report?')) return;
  const res = await fetch('/crashes/' + id, { method: 'DELETE' });
  if (res.ok) loadCrashes();
  else alert('Delete failed');
}

function openJson(id) {
  window.open('/crashes/' + id, '_blank');
}

loadCrashes();
</script>
</body>
</html>
"""

@app.route("/admin", methods=["GET"])
def admin_dashboard():
    return render_template_string(DASHBOARD_HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
