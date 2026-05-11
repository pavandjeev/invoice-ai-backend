# AI Supplier Support API

A beginner-friendly FastAPI backend for an accounts department supplier support system.  
Built to integrate with **Voiceflow chatbots**, **Voiceflow Playbooks**, **telephone/voice agents**, and deployable to **Railway**.

---

## What it does

Allows suppliers to self-serve common accounts queries:

| # | Action | Endpoint |
|---|--------|----------|
| 1 | Verify themselves | `POST /verify-supplier` |
| 2 | Check invoice status | `POST /invoice-status` |
| 3 | Check payment date | `POST /payment-date` |
| 4 | Count unpaid invoices | `POST /unpaid-invoices-count` |
| 5 | View unpaid invoices | `POST /unpaid-invoices` |
| 6 | Raise a query | `POST /raise-query` |
| 7 | Ask a general question | `POST /general-question` |

Every response includes a `display_message` field — a plain-English sentence ready for chatbot bubbles or text-to-speech.

---

## Mock data included

Three suppliers, each with three invoices (a mix of paid, unpaid, and processing):

| Supplier Code | Company |
|---------------|---------|
| `SUP001` | Acme Office Supplies Ltd |
| `SUP002` | FastPrint Solutions |
| `SUP003` | Green Facilities Management |

---

## Run locally

### 1. Clone / download the project

```bash
git clone <your-repo-url>
cd supplier-support-api
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Mac / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

```bash
uvicorn main:app --reload
```

The API will be available at: **http://127.0.0.1:8000**

### 5. Open the interactive docs

FastAPI generates automatic docs. Open your browser at:

- **Swagger UI** → http://127.0.0.1:8000/docs  
- **ReDoc** → http://127.0.0.1:8000/redoc

You can test every endpoint directly from the browser — no Postman needed.

---

## Example requests

All requests use `Content-Type: application/json`.

### Verify a supplier

```bash
curl -X POST http://127.0.0.1:8000/verify-supplier \
  -H "Content-Type: application/json" \
  -d '{"supplier_code": "SUP001"}'
```

### Check invoice status

```bash
curl -X POST http://127.0.0.1:8000/invoice-status \
  -H "Content-Type: application/json" \
  -d '{"supplier_code": "SUP001", "invoice_number": "INV-1002"}'
```

### Check payment date

```bash
curl -X POST http://127.0.0.1:8000/payment-date \
  -H "Content-Type: application/json" \
  -d '{"supplier_code": "SUP002", "invoice_number": "INV-2001"}'
```

### Count unpaid invoices

```bash
curl -X POST http://127.0.0.1:8000/unpaid-invoices-count \
  -H "Content-Type: application/json" \
  -d '{"supplier_code": "SUP002"}'
```

### View unpaid invoices

```bash
curl -X POST http://127.0.0.1:8000/unpaid-invoices \
  -H "Content-Type: application/json" \
  -d '{"supplier_code": "SUP003"}'
```

### Raise a query

```bash
curl -X POST http://127.0.0.1:8000/raise-query \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_code": "SUP001",
    "invoice_number": "INV-1002",
    "query_message": "This invoice was due on 30 April but I have not received payment."
  }'
```

### Ask a general question

```bash
curl -X POST http://127.0.0.1:8000/general-question \
  -H "Content-Type: application/json" \
  -d '{"question": "What are your payment terms?"}'
```

---

## Deploy to Railway

1. Push this project to a GitHub repository.
2. Go to [railway.app](https://railway.app) and create a new project.
3. Choose **Deploy from GitHub repo** and select your repository.
4. Railway will detect the `Procfile` automatically and start the server.
5. Your public URL will appear in the Railway dashboard — use this as your base URL in Voiceflow.

> **Note:** Railway injects a `$PORT` environment variable automatically.  
> The `Procfile` already uses `--port $PORT` so no extra configuration is needed.

---

## Connecting to Voiceflow

1. In Voiceflow, add an **API step**.
2. Set the method to `POST` and paste your Railway URL + endpoint (e.g. `https://your-app.railway.app/verify-supplier`).
3. Set the body to JSON with the required fields (e.g. `{"supplier_code": "{supplier_code_variable}"}`).
4. Map the `display_message` from the response to a **Speak** or **Text** block.

---

## Project structure

```
supplier-support-api/
├── main.py           ← All app logic and mock data
├── requirements.txt  ← Python dependencies
├── Procfile          ← Railway / Heroku process file
└── README.md         ← This file
```

---

## Next steps (when ready)

- [ ] Replace mock data with a real database (PostgreSQL via SQLAlchemy, or Supabase)
- [ ] Add authentication (API keys or JWT tokens)
- [ ] Connect `/raise-query` to an email service (SendGrid / Mailgun)
- [ ] Add a `/supplier-statement` endpoint
- [ ] Integrate an LLM into `/general-question` for smarter answers
