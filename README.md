# Crash Reporter API (Flask + MongoDB)

A backend REST API for collecting Android crash reports (fatal and non-fatal), storing them in MongoDB, and providing a minimal admin interface for viewing and managing crashes. This service is designed to work together with a custom **Android Crash Reporter SDK**.

---

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Framework:** Flask
* **Database:** MongoDB (Local or Atlas)
* **Protocol:** REST API

---

## ✨ Features

* **Receive Crash Reports:** Ingest fatal and non-fatal data from Android clients.
* **Full Payload Storage:** Stores the original JSON payload for comprehensive debugging.
* **Querying:** Retrieve latest reports with limit support (Default 50, Max 200).
* **Management:** Retrieve a single crash by ID or delete resolved reports.
* **Admin UI:** Minimal web interface for monitoring and manual deletions.
* **Health Check:** Dedicated endpoint for uptime monitoring.

---

## 📡 API Endpoints

### 1. Health Check
`GET /health`
* **Description:** Verifies the server is running.
* **Response:** `{ "status": "ok" }`

### 2. Create Crash Report
`POST /crashes`
* **Expected JSON body:**
    ```json
    {
      "message": "NullPointerException",
      "fatal": true,
      "stacktrace": "...",
      "package": "com.example.app",
      "device": "Pixel 7",
      "android_version": "14"
    }
    ```
* **Response:** `{ "status": "saved" }`

### 3. Retrieve & Delete
* **GET `/crashes?limit=50`**: Retrieve latest crashes (Max limit: 200).
* **GET `/crashes/<crash_id>`**: Retrieve specific crash details by ID.
* **DELETE `/crashes/<crash_id>`**: Permanently delete a crash report.

---

## 🖥 Admin Portal
`GET /admin`

A minimal web interface that allows:
* Viewing a list of recent crash reports.
* Inspecting specific crash details and stack traces.
* Deleting crash reports directly from the browser.

---

## 📊 Data Model
Each crash report is stored with the following structure:
* `message`: Brief error summary.
* `fatal`: Boolean flag for crash type.
* `timestamp`: Time the report was received.
* `raw`: The full original JSON payload sent by the client.
* `_id`: MongoDB unique identifier.


### Dashbord biew
![View](images/screenshots/admin dashbord.png)
---
### Deployment
The API can be deployed to any cloud provider such as Render, Koyeb, AWS, or GCP. After deployment, verify your endpoints:
* GET /health
* GET /admin
* 
## ⚙️ Running Locally

### Requirements
* Python 3.10+
* MongoDB (local or Atlas)
* Environment variable: `MONGO_URI`

### Installation
```bash
pip install -r requirements.txt

### Run the server
export MONGO_URI="mongodb+srv://<user>:<password>@<cluster>/<db>"
python app.py


