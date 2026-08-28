# Data Automation & Notification Backend

A robust backend service and web API designed for parsing, managing, and processing large sets of structured unstructured external provider data. Built for high reliability and strictly typed data integration workflows.

## Core Architecture

This service acts as an abstraction layer between external data providers and internal systems, handling normalization, status tracking, and automated event triggers.

```text
data-automation-service/
├── api/
│   ├── routes.py          ← REST API endpoints for downstream consumers
│   └── webhooks.py        ← Ingestion endpoints for external pushes
├── core/
│   ├── parser.py          ← Normalization logic for unstructured external data
│   └── dedup.py           ← Strict hashing engine to prevent duplicate processing
├── notifications/
│   ├── router.py          ← Event-based routing (Webhooks, SMTP, etc.)
│   └── templates.py       ← Standardized reporting formats
├── config/
│   └── providers.json     ← Provider mapping and credential management
└── requirements.txt
```

## Key Features

1. **Massive Data Normalization:** Converts dynamic and rapidly changing feeds from external providers into strict, predictable tracking schemas.
2. **Reliable External Routing:** Includes highly reliable deduplication logic to safely trigger real-time notifications or external downstream alerts the moment database conditions are met.
3. **State Management:** Logs every parsed payload with timestamp, source, and ingestion status, allowing complete auditability.

## Installation & Setup

**Configure Environment:**
Copy the template and fill in your secure credentials or provider keys.
```bash
cp .env.example .env
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**Start the Service:**
Depending on your server environment, run the service with Uvicorn (or equivalent ASGI server):
```bash
uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload
```

## Notification Workflow

When the `parser.py` engine detects a new valid record or a state change, it automatically formats the payload and triggers the notification router. 

Example of a standard downstream webhook payload:
```json
{
  "event_id": "evt_948fha",
  "provider": "source_alpha",
  "status": "PROCESSED",
  "data": {
    "normalized_amount": 1500.00,
    "transaction_ref": "tx_001928"
  },
  "timestamp": "2026-03-24T10:15:30Z"
}
```


<!-- activity-sync: 2026-08-28 -->
