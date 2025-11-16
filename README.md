# **Hospital Batch Processor**

A FastAPI-based system for bulk hospital processing with CSV upload, asynchronous background execution, and real-time progress tracking.

---

## **Features**

* Asynchronous CSV upload with instant `batch_id`
* Parallel processing
* Real-time progress polling
* Batch activation & status lifecycle
* In-memory batch tracking
* Auto-generated OpenAPI docs
* Docker-ready
* Health check endpoint

---

## **Prerequisites**

* Python **3.8+**
* Docker & Docker Compose (optional)

---

## **Quick Start**

### **Option 1 — Docker (Recommended)**

**Build & run:**

```sh
docker-compose build
```

**Detached mode:**

```sh
docker-compose up -d
```

**View logs:**

```sh
docker-compose logs -f
```

**Stop:**

```sh
docker-compose down
```

---

### **Option 2 — Local Development**

**Create virtual environment:**

```sh
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

**Install dependencies:**

```sh
pip install -r requirements.txt
```

**Run application:**

```sh
python -m app.main
```

or

```sh
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## **API Documentation**

After starting the service:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## **API Endpoints**

### **Health Check**

```
GET /health
```

### **Upload CSV (returns batch_id)**

```
POST /batch/upload-csv
```

### **Get Progress**

```
GET /batch/{batch_id}/progress
```

### **Get Final Status**

```
GET /batch/{batch_id}/status
```

---

## **Workflow**

### **1. Prepare CSV**

`hospitals.csv`:

```
name,address,phone
General Hospital,123 Main Street,555-0100
City Medical Center,456 Oak Avenue,555-0200
Community Hospital,789 Pine Road,
```

**Requirements:**

* Headers: `name,address,phone`
* `name` & `address`: required
* `phone`: optional

---

### **2. Upload CSV**

```sh
curl -X POST "http://localhost:8000/batch/upload-csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@hospitals.csv"
```

**Sample Response:**

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_hospitals": 25,
  "message": "CSV upload initiated. Use batch_id to track progress.",
  "status": "pending"
}
```

---

### **3. Poll Progress**

```sh
curl "http://localhost:8000/batch/{batch_id}/progress"
```

**Example Response:**

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress_percentage": 60.0,
  "processing_status": "processing",
  "processed_hospitals": 15,
  "total_hospitals": 25,
  "failed_hospitals": 0,
  "current_message": "Processing hospital 15/25"
}
```

---

### **4. Fetch Final Status**

```sh
curl "http://localhost:8000/batch/{batch_id}/status"
```

---

## **Environment Variables**

`.env`:

```
EXTERNAL_API_BASE_URL=https://hospital-directory.onrender.com
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

---

## **Project Structure**

```
hospital-batch-processor/
├── app/
│   ├── controllers/      # API routes
│   ├── services/         # Business logic
│   ├── repositories/     # Data access
│   ├── models/           # Schemas & enums
│   ├── utils/            # Validators & exceptions
│   ├── core/             # Config
│   └── main.py           # Application entrypoint
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── README.md
```

---

## **Performance**

* **20 parallel tasks** during hospital creation
* Fully asynchronous processing
* Real-time progress polling

---

## **Processing Status Values**

* `pending`
* `processing`
* `completed`
* `partially_completed`
* `failed`

---

## **Hospital Status Values**

* `created_and_activated`
* `created`
* `failed`
* `deleted`

---

## **Error Handling**

Example validation response:

```json
{
  "detail": [
    {
      "loc": ["file", "headers"],
      "msg": "CSV headers must be exactly: name,address,phone",
      "type": "invalid_headers"
    }
  ]
}
