"""
AI Supplier Support API
=======================
A beginner-friendly FastAPI backend for an accounts department
supplier support system. Uses mock data — no database needed.

Ready for:
  - Voiceflow chatbot / Playbooks integration
  - Telephone / voice agent integration
  - Railway deployment

Run locally:
    uvicorn main:app --reload
    Then open: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Supplier Support API",
    description="Handles supplier verification and invoice queries for accounts departments.",
    version="1.0.0",
)

# CORS middleware — allows Voiceflow, voice agents, and any frontend to call
# the API without browser errors.
# NOTE: allow_credentials must be False when allow_origins is "*".
#       Using both together violates the CORS spec and browsers will block it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mock data — replace with a database when ready
# ---------------------------------------------------------------------------

SUPPLIERS = {
    "SUP001": {
        "supplier_code": "SUP001",
        "company_name": "Acme Office Supplies Ltd",
        "contact_name": "Sarah Johnson",
        "email": "accounts@acmeoffice.co.uk",
    },
    "SUP002": {
        "supplier_code": "SUP002",
        "company_name": "FastPrint Solutions",
        "contact_name": "David Okafor",
        "email": "billing@fastprint.co.uk",
    },
    "SUP003": {
        "supplier_code": "SUP003",
        "company_name": "Green Facilities Management",
        "contact_name": "Priya Patel",
        "email": "finance@greenfm.co.uk",
    },
}

# Invoice statuses: "paid" | "unpaid" | "processing"
# Descriptions use plain commas (no em-dashes) so TTS reads them cleanly.
INVOICES = {
    # --- Acme Office Supplies ---
    "INV-1001": {
        "invoice_number": "INV-1001",
        "supplier_code": "SUP001",
        "amount": 1250.00,
        "currency": "GBP",
        "status": "paid",
        "issue_date": "2025-03-01",
        "due_date": "2025-03-31",
        "payment_date": "2025-03-28",
        "description": "Office stationery, March 2025",
    },
    "INV-1002": {
        "invoice_number": "INV-1002",
        "supplier_code": "SUP001",
        "amount": 875.50,
        "currency": "GBP",
        "status": "unpaid",
        "issue_date": "2025-04-01",
        "due_date": "2025-04-30",
        "payment_date": None,
        "description": "Printer cartridges, April 2025",
    },
    "INV-1003": {
        "invoice_number": "INV-1003",
        "supplier_code": "SUP001",
        "amount": 430.00,
        "currency": "GBP",
        "status": "processing",
        "issue_date": "2025-05-01",
        "due_date": "2025-05-31",
        "payment_date": None,
        "description": "Desk accessories, May 2025",
    },
    # --- FastPrint Solutions ---
    "INV-2001": {
        "invoice_number": "INV-2001",
        "supplier_code": "SUP002",
        "amount": 3400.00,
        "currency": "GBP",
        "status": "paid",
        "issue_date": "2025-02-15",
        "due_date": "2025-03-15",
        "payment_date": "2025-03-10",
        "description": "Brochure print run, February 2025",
    },
    "INV-2002": {
        "invoice_number": "INV-2002",
        "supplier_code": "SUP002",
        "amount": 1980.00,
        "currency": "GBP",
        "status": "unpaid",
        "issue_date": "2025-04-10",
        "due_date": "2025-05-10",
        "payment_date": None,
        "description": "Letterhead and envelope stock, April 2025",
    },
    "INV-2003": {
        "invoice_number": "INV-2003",
        "supplier_code": "SUP002",
        "amount": 760.00,
        "currency": "GBP",
        "status": "unpaid",
        "issue_date": "2025-05-01",
        "due_date": "2025-05-31",
        "payment_date": None,
        "description": "Poster printing, May 2025",
    },
    # --- Green Facilities Management ---
    "INV-3001": {
        "invoice_number": "INV-3001",
        "supplier_code": "SUP003",
        "amount": 5200.00,
        "currency": "GBP",
        "status": "paid",
        "issue_date": "2025-01-01",
        "due_date": "2025-01-31",
        "payment_date": "2025-01-29",
        "description": "Cleaning services, January 2025",
    },
    "INV-3002": {
        "invoice_number": "INV-3002",
        "supplier_code": "SUP003",
        "amount": 5200.00,
        "currency": "GBP",
        "status": "processing",
        "issue_date": "2025-04-01",
        "due_date": "2025-04-30",
        "payment_date": None,
        "description": "Cleaning services, April 2025",
    },
    "INV-3003": {
        "invoice_number": "INV-3003",
        "supplier_code": "SUP003",
        "amount": 320.00,
        "currency": "GBP",
        "status": "unpaid",
        "issue_date": "2025-05-01",
        "due_date": "2025-05-31",
        "payment_date": None,
        "description": "Window cleaning, May 2025",
    },
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def get_supplier_invoices(supplier_code: str) -> list:
    """Return all invoices belonging to a supplier."""
    return [inv for inv in INVOICES.values() if inv["supplier_code"] == supplier_code]


def format_currency(amount: float, currency: str = "GBP") -> str:
    """Format a number as a currency string."""
    symbol = "£" if currency == "GBP" else f"{currency} "
    return f"{symbol}{amount:,.2f}"


def status_phrase(status: str) -> str:
    """Return a human-friendly, TTS-safe status sentence."""
    return {
        "paid": "has been paid",
        "unpaid": "is currently unpaid",
        "processing": "is currently being processed for payment",
    }.get(status, status)


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class SupplierVerifyRequest(BaseModel):
    supplier_code: str

class InvoiceStatusRequest(BaseModel):
    supplier_code: str
    invoice_number: str

class PaymentDateRequest(BaseModel):
    supplier_code: str
    invoice_number: str

class UnpaidInvoicesCountRequest(BaseModel):
    supplier_code: str

class UnpaidInvoicesRequest(BaseModel):
    supplier_code: str

class RaiseQueryRequest(BaseModel):
    supplier_code: str
    invoice_number: str
    query_message: str

class GeneralQuestionRequest(BaseModel):
    supplier_code: Optional[str] = None
    question: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Health check — confirms the API is running."""
    return {
        "status": "ok",
        "display_message": (
            "Welcome to the AI Supplier Support API. "
            "The service is up and running. "
            "Please use the correct endpoint for your request."
        ),
        "available_endpoints": [
            "POST /verify-supplier",
            "POST /invoice-status",
            "POST /payment-date",
            "POST /unpaid-invoices-count",
            "POST /unpaid-invoices",
            "POST /raise-query",
            "POST /general-question",
        ],
    }


@app.post("/verify-supplier")
def verify_supplier(body: SupplierVerifyRequest):
    """
    Verify a supplier by their supplier code.
    This should be the first call before any other query.
    """
    code = body.supplier_code.strip().upper()
    supplier = SUPPLIERS.get(code)

    if not supplier:
        return {
            "verified": False,
            "display_message": (
                f"Sorry, I could not find a supplier with the code {body.supplier_code}. "
                "Please check your supplier code and try again, "
                "or contact the accounts team for assistance."
            ),
        }

    return {
        "verified": True,
        "supplier_code": supplier["supplier_code"],
        "company_name": supplier["company_name"],
        "contact_name": supplier["contact_name"],
        "display_message": (
            f"Thank you, I have verified your account. "
            f"Welcome, {supplier['contact_name']} from {supplier['company_name']}. "
            "How can I help you today?"
        ),
    }


@app.post("/invoice-status")
def invoice_status(body: InvoiceStatusRequest):
    """Return the current status of a specific invoice."""
    code = body.supplier_code.strip().upper()
    inv_num = body.invoice_number.strip().upper()

    if code not in SUPPLIERS:
        return {
            "found": False,
            "display_message": (
                f"Supplier code {body.supplier_code} was not recognised. "
                "Please verify your supplier code first."
            ),
        }

    invoice = INVOICES.get(inv_num)

    if not invoice:
        return {
            "found": False,
            "display_message": (
                f"I could not find invoice {body.invoice_number}. "
                "Please check the invoice number and try again."
            ),
        }

    if invoice["supplier_code"] != code:
        return {
            "found": False,
            "display_message": (
                f"Invoice {body.invoice_number} does not appear to be linked to your account. "
                "Please contact the accounts team if you believe this is an error."
            ),
        }

    amount_str = format_currency(invoice["amount"], invoice["currency"])
    payment_note = (
        f" Payment was made on {invoice['payment_date']}."
        if invoice["payment_date"]
        else ""
    )

    return {
        "found": True,
        "invoice_number": invoice["invoice_number"],
        "status": invoice["status"],
        "amount": invoice["amount"],
        "currency": invoice["currency"],
        "due_date": invoice["due_date"],
        "payment_date": invoice["payment_date"],
        "description": invoice["description"],
        "display_message": (
            f"Invoice {invoice['invoice_number']} for {amount_str}, "
            f"{invoice['description']}, {status_phrase(invoice['status'])}. "
            f"The due date is {invoice['due_date']}."
            f"{payment_note}"
        ),
    }


@app.post("/payment-date")
def payment_date(body: PaymentDateRequest):
    """Return the payment date, or the due date if not yet paid."""
    code = body.supplier_code.strip().upper()
    inv_num = body.invoice_number.strip().upper()

    if code not in SUPPLIERS:
        return {
            "found": False,
            "display_message": (
                f"Supplier code {body.supplier_code} was not recognised. "
                "Please verify your supplier code first."
            ),
        }

    invoice = INVOICES.get(inv_num)

    if not invoice or invoice["supplier_code"] != code:
        return {
            "found": False,
            "display_message": (
                f"I could not find invoice {body.invoice_number} on your account. "
                "Please check the invoice number and try again."
            ),
        }

    if invoice["payment_date"]:
        return {
            "found": True,
            "invoice_number": invoice["invoice_number"],
            "status": invoice["status"],
            "payment_date": invoice["payment_date"],
            "display_message": (
                f"Invoice {invoice['invoice_number']} was paid on {invoice['payment_date']}."
            ),
        }

    if invoice["status"] == "processing":
        return {
            "found": True,
            "invoice_number": invoice["invoice_number"],
            "status": invoice["status"],
            "payment_date": None,
            "due_date": invoice["due_date"],
            "display_message": (
                f"Invoice {invoice['invoice_number']} is currently being processed for payment. "
                f"The due date is {invoice['due_date']}. "
                "Payment will be made on or before this date."
            ),
        }

    # Status is "unpaid"
    return {
        "found": True,
        "invoice_number": invoice["invoice_number"],
        "status": invoice["status"],
        "payment_date": None,
        "due_date": invoice["due_date"],
        "display_message": (
            f"Invoice {invoice['invoice_number']} has not been paid yet. "
            f"The payment due date is {invoice['due_date']}. "
            "If you have not received payment by this date, please raise a query."
        ),
    }


@app.post("/unpaid-invoices-count")
def unpaid_invoices_count(body: UnpaidInvoicesCountRequest):
    """Return the total number of outstanding invoices for a supplier."""
    code = body.supplier_code.strip().upper()

    if code not in SUPPLIERS:
        return {
            "found": False,
            "display_message": (
                f"Supplier code {body.supplier_code} was not recognised. "
                "Please verify your supplier code first."
            ),
        }

    supplier = SUPPLIERS[code]
    all_invoices = get_supplier_invoices(code)
    unpaid = [inv for inv in all_invoices if inv["status"] == "unpaid"]
    processing = [inv for inv in all_invoices if inv["status"] == "processing"]
    total_outstanding = len(unpaid) + len(processing)

    if total_outstanding == 0:
        message = (
            f"Great news. {supplier['company_name']} has no outstanding invoices at this time. "
            "All invoices have been paid."
        )
    elif total_outstanding == 1:
        message = (
            f"{supplier['company_name']} currently has 1 outstanding invoice. "
            f"That is {len(unpaid)} unpaid and {len(processing)} being processed."
        )
    else:
        message = (
            f"{supplier['company_name']} currently has {total_outstanding} outstanding invoices. "
            f"That is {len(unpaid)} unpaid and {len(processing)} being processed."
        )

    return {
        "found": True,
        "company_name": supplier["company_name"],
        "unpaid_count": len(unpaid),
        "processing_count": len(processing),
        "total_outstanding": total_outstanding,
        "display_message": message,
    }


@app.post("/unpaid-invoices")
def unpaid_invoices(body: UnpaidInvoicesRequest):
    """Return the full list of unpaid and processing invoices for a supplier."""
    code = body.supplier_code.strip().upper()

    if code not in SUPPLIERS:
        return {
            "found": False,
            "display_message": (
                f"Supplier code {body.supplier_code} was not recognised. "
                "Please verify your supplier code first."
            ),
        }

    supplier = SUPPLIERS[code]
    all_invoices = get_supplier_invoices(code)
    outstanding = [inv for inv in all_invoices if inv["status"] in ("unpaid", "processing")]

    if not outstanding:
        return {
            "found": True,
            "company_name": supplier["company_name"],
            "invoices": [],
            "display_message": (
                f"There are no outstanding invoices for {supplier['company_name']} at this time. "
                "All invoices have been paid."
            ),
        }

    # Build a voice-friendly summary — plain commas, no special characters
    summaries = []
    for inv in outstanding:
        amount_str = format_currency(inv["amount"], inv["currency"])
        summaries.append(
            f"Invoice {inv['invoice_number']} for {amount_str}, "
            f"due {inv['due_date']}, status {inv['status']}"
        )

    display = (
        f"Here are the outstanding invoices for {supplier['company_name']}. "
        + ". ".join(summaries) + "."
    )

    return {
        "found": True,
        "company_name": supplier["company_name"],
        "invoices": outstanding,
        "display_message": display,
    }


@app.post("/raise-query")
def raise_query(body: RaiseQueryRequest):
    """
    Allow a supplier to raise a query about a specific invoice.
    The query is printed to the console for now.
    In production: save to a database, send an email, or open a support ticket.
    """
    code = body.supplier_code.strip().upper()
    inv_num = body.invoice_number.strip().upper()

    if code not in SUPPLIERS:
        return {
            "submitted": False,
            "display_message": (
                f"Supplier code {body.supplier_code} was not recognised. "
                "Please verify your supplier code first."
            ),
        }

    invoice = INVOICES.get(inv_num)

    if not invoice or invoice["supplier_code"] != code:
        return {
            "submitted": False,
            "display_message": (
                f"I could not find invoice {body.invoice_number} on your account. "
                "Please check the invoice number and try again."
            ),
        }

    supplier = SUPPLIERS[code]

    # Log the query to the console (replace with DB / email in production)
    print(
        f"\n[QUERY RECEIVED]\n"
        f"  Supplier : {supplier['company_name']} ({code})\n"
        f"  Invoice  : {inv_num}\n"
        f"  Message  : {body.query_message}\n"
    )

    return {
        "submitted": True,
        "supplier_code": code,
        "invoice_number": inv_num,
        "query_message": body.query_message,
        "display_message": (
            f"Thank you, {supplier['contact_name']}. "
            f"Your query about invoice {inv_num} has been submitted to the accounts team. "
            "A member of the team will be in touch within 2 business days. "
            "Is there anything else I can help you with?"
        ),
    }


@app.post("/general-question")
def general_question(body: GeneralQuestionRequest):
    """
    Answer common supplier questions using keyword matching.
    Replace with an LLM call or knowledge base in production.
    """
    q = body.question.lower()

    if any(kw in q for kw in ["payment term", "terms", "how long", "when do you pay"]):
        answer = (
            "Our standard payment terms are 30 days from the date of a valid invoice. "
            "Some suppliers have agreed 60-day terms. "
            "Please check your supplier agreement for details."
        )
    elif any(kw in q for kw in ["remittance", "remit"]):
        answer = (
            "Remittance advice is sent to your registered email address on the day payment is made. "
            "If you have not received one, please check your spam folder or raise a query."
        )
    elif any(kw in q for kw in ["contact", "phone", "email", "speak to someone", "human"]):
        answer = (
            "You can contact the accounts payable team by email at ap@company.co.uk, "
            "or by phone on 0800 123 4567, Monday to Friday, 9am to 5pm."
        )
    elif any(kw in q for kw in ["bank", "sort code", "account number", "bank details"]):
        answer = (
            "For security reasons, bank account details cannot be provided or changed through this service. "
            "Please contact the accounts team directly on 0800 123 4567."
        )
    elif any(kw in q for kw in ["dispute", "wrong amount", "incorrect", "overcharged"]):
        answer = (
            "If you believe an invoice amount is incorrect, please use the raise a query option "
            "with your invoice number and a description of the issue. "
            "Our team will investigate and respond within 2 business days."
        )
    elif any(kw in q for kw in ["statement", "account statement"]):
        answer = (
            "Supplier account statements are sent quarterly. "
            "If you need an urgent statement, please contact the accounts team by email."
        )
    elif any(kw in q for kw in ["late", "overdue", "not received payment"]):
        answer = (
            "If a payment is overdue, please raise a query using your invoice number "
            "and we will investigate as a priority. "
            "You can also call us on 0800 123 4567."
        )
    else:
        answer = (
            "Thank you for your question. I am not able to answer that automatically, "
            "but a member of the accounts team will be happy to help. "
            "Please contact us at ap@company.co.uk or call 0800 123 4567, "
            "Monday to Friday, 9am to 5pm."
        )

    return {
        "question": body.question,
        "display_message": answer,
    }
