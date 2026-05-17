import os
import threading
from datetime import datetime

import pandas as pd
import openpyxl
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Supplier Invoice Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Absolute path to the Excel file (works on Railway and locally)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "supplier_invoice_test_data_v2.xlsx")

# Thread lock so only one request writes to Excel at a time
write_lock = threading.Lock()

# Statuses that count as "unpaid" for this system
UNPAID_STATUSES = {"unpaid", "overdue", "processing"}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize(value: str) -> str:
    """Strip whitespace and convert to uppercase."""
    return str(value).strip().upper()


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and strip whitespace."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def load_suppliers() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, sheet_name="Suppliers", dtype=str)
    df = clean_columns(df)
    df["supplier_code"] = df["supplier_code"].apply(normalize)
    return df


def load_invoices() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, sheet_name="Invoices", dtype=str)
    df = clean_columns(df)
    df["supplier_code"] = df["supplier_code"].apply(normalize)
    df["invoice_number"] = df["invoice_number"].apply(normalize)
    df["status"] = df["status"].str.strip().str.lower()
    return df


def load_queries() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, sheet_name="Queries", dtype=str)
    df = clean_columns(df)
    return df


def find_supplier(supplier_code: str) -> dict | None:
    """Return the supplier row as a dict, or None if not found."""
    suppliers = load_suppliers()
    match = suppliers[suppliers["supplier_code"] == normalize(supplier_code)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def find_invoice(supplier_code: str, invoice_number: str) -> dict | None:
    """Return an invoice row filtered by BOTH supplier_code and invoice_number."""
    invoices = load_invoices()
    match = invoices[
        (invoices["supplier_code"] == normalize(supplier_code)) &
        (invoices["invoice_number"] == normalize(invoice_number))
    ]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def append_query_to_excel(supplier_code: str, invoice_number: str,
                           query_message: str) -> None:
    """Append a new row to the Queries sheet using openpyxl (thread-safe)."""
    with write_lock:
        wb = openpyxl.load_workbook(EXCEL_PATH)
        ws = wb["Queries"]
        ws.append([
            normalize(supplier_code),
            normalize(invoice_number),
            query_message.strip(),
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "open",
        ])
        wb.save(EXCEL_PATH)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SupplierRequest(BaseModel):
    supplier_code: str

class InvoiceRequest(BaseModel):
    supplier_code: str
    invoice_number: str

class QueryRequest(BaseModel):
    supplier_code: str
    invoice_number: str
    query_message: str

class GeneralQuestionRequest(BaseModel):
    question: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "display_message": "Supplier Invoice Support API is running.",
    }


@app.post("/verify-supplier")
def verify_supplier(req: SupplierRequest):
    """Check whether a supplier code exists in the Suppliers sheet."""
    supplier = find_supplier(req.supplier_code)

    if not supplier:
        return {
            "verified": False,
            "supplier_code": normalize(req.supplier_code),
            "display_message": (
                f"I could not find a supplier with code {normalize(req.supplier_code).upper()}. "
                "Please double-check the code and try again."
            ),
        }

    return {
        "verified": True,
        "supplier_code": supplier["supplier_code"],
        "supplier_name": supplier.get("supplier_name", ""),
        "display_message": (
            f"Supplier verified: {supplier.get('supplier_name', '')} "
            f"({supplier['supplier_code']})."
        ),
    }


@app.post("/invoice-status")
def invoice_status(req: InvoiceRequest):
    """Return the current status of a specific invoice."""
    # Verify supplier first
    if not find_supplier(req.supplier_code):
        return {
            "found": False,
            "display_message": (
                f"Supplier code {normalize(req.supplier_code)} was not recognised. "
                "Please verify your supplier code."
            ),
        }

    invoice = find_invoice(req.supplier_code, req.invoice_number)

    if not invoice:
        return {
            "found": False,
            "display_message": (
                f"Invoice {normalize(req.invoice_number)} was not found for supplier "
                f"{normalize(req.supplier_code)}. Please check the invoice number."
            ),
        }

    status = invoice.get("status", "unknown")
    amount = invoice.get("amount", "N/A")

    status_messages = {
        "paid":       f"Invoice {invoice['invoice_number']} has been paid. Amount: £{amount}.",
        "unpaid":     f"Invoice {invoice['invoice_number']} is currently unpaid. Amount due: £{amount}.",
        "processing": f"Invoice {invoice['invoice_number']} is being processed. Amount: £{amount}.",
        "overdue":    f"Invoice {invoice['invoice_number']} is overdue. Amount outstanding: £{amount}. I recommend raising a query so the accounts team can review this.",
        "on-hold":    f"Invoice {invoice['invoice_number']} is currently on hold. Amount: £{amount}. Please contact us for more information.",
    }

    display = status_messages.get(
        status,
        f"Invoice {invoice['invoice_number']} has status '{status}'. Amount: £{amount}.",
    )

    return {
        "found": True,
        "invoice_number": invoice["invoice_number"],
        "supplier_code": invoice["supplier_code"],
        "status": status,
        "amount": amount,
        "display_message": display,
    }


@app.post("/payment-date")
def payment_date(req: InvoiceRequest):
    """Return the payment date or due date for an invoice."""
    if not find_supplier(req.supplier_code):
        return {
            "found": False,
            "display_message": (
                f"Supplier code {normalize(req.supplier_code)} was not recognised."
            ),
        }

    invoice = find_invoice(req.supplier_code, req.invoice_number)

    if not invoice:
        return {
            "found": False,
            "display_message": (
                f"Invoice {normalize(req.invoice_number)} was not found for supplier "
                f"{normalize(req.supplier_code)}."
            ),
        }

    status = invoice.get("status", "unknown")
    payment_date_val = invoice.get("payment_date", "")
    due_date_val = invoice.get("due_date", "")
    inv_num = invoice["invoice_number"]

    # Clean up date values (pandas may return 'nan' strings)
    def clean_date(val):
        if not val or str(val).strip().lower() in ("nan", "none", ""):
            return None
        return str(val).strip()

    payment_date_clean = clean_date(payment_date_val)
    due_date_clean = clean_date(due_date_val)

    if status == "paid":
        if payment_date_clean:
            msg = f"Invoice {inv_num} was paid on {payment_date_clean}."
        else:
            msg = f"Invoice {inv_num} has been paid, but no payment date is recorded."

    elif status == "overdue":
        if due_date_clean:
            msg = (
                f"Invoice {inv_num} was due on {due_date_clean} and is now overdue. "
                "I recommend raising a query so the accounts team can review this."
            )
        else:
            msg = (
                f"Invoice {inv_num} is overdue. "
                "I recommend raising a query so the accounts team can review this."
            )

    elif status == "unpaid":
        if due_date_clean:
            msg = f"Invoice {inv_num} is unpaid. Payment is due by {due_date_clean}."
        else:
            msg = f"Invoice {inv_num} is unpaid. Please contact us for payment terms."

    elif status == "processing":
        if due_date_clean:
            msg = (
                f"Invoice {inv_num} is currently being processed. "
                f"Payment is expected by {due_date_clean}."
            )
        else:
            msg = f"Invoice {inv_num} is currently being processed. A payment date will be confirmed shortly."

    elif status == "on-hold":
        msg = (
            f"Invoice {inv_num} is on hold. "
            "Please contact our accounts team for further information."
        )

    else:
        msg = (
            f"Invoice {inv_num} has status '{status}'. "
            f"Due date: {due_date_clean or 'not recorded'}."
        )

    return {
        "found": True,
        "invoice_number": inv_num,
        "status": status,
        "payment_date": payment_date_clean,
        "due_date": due_date_clean,
        "display_message": msg,
    }


@app.post("/unpaid-invoices-count")
def unpaid_invoices_count(req: SupplierRequest):
    """Return the number of unpaid/overdue/processing invoices for a supplier."""
    if not find_supplier(req.supplier_code):
        return {
            "found": False,
            "display_message": (
                f"Supplier code {normalize(req.supplier_code)} was not recognised."
            ),
        }

    invoices = load_invoices()
    supplier_invoices = invoices[
        invoices["supplier_code"] == normalize(req.supplier_code)
    ]
    unpaid = supplier_invoices[supplier_invoices["status"].isin(UNPAID_STATUSES)]
    count = len(unpaid)

    if count == 0:
        msg = f"There are no outstanding invoices for supplier {normalize(req.supplier_code)}."
    elif count == 1:
        msg = f"There is 1 outstanding invoice for supplier {normalize(req.supplier_code)}."
    else:
        msg = f"There are {count} outstanding invoices for supplier {normalize(req.supplier_code)}."

    return {
        "found": True,
        "supplier_code": normalize(req.supplier_code),
        "unpaid_count": count,
        "display_message": msg,
    }


@app.post("/unpaid-invoices")
def unpaid_invoices(req: SupplierRequest):
    """Return the full list of unpaid/overdue/processing invoices for a supplier."""
    if not find_supplier(req.supplier_code):
        return {
            "found": False,
            "display_message": (
                f"Supplier code {normalize(req.supplier_code)} was not recognised."
            ),
        }

    invoices = load_invoices()
    supplier_invoices = invoices[
        invoices["supplier_code"] == normalize(req.supplier_code)
    ]
    unpaid = supplier_invoices[supplier_invoices["status"].isin(UNPAID_STATUSES)]

    if unpaid.empty:
        return {
            "found": True,
            "supplier_code": normalize(req.supplier_code),
            "unpaid_invoices": [],
            "display_message": (
                f"There are no outstanding invoices for supplier {normalize(req.supplier_code)}."
            ),
        }

    results = []
    lines = []
    for _, row in unpaid.iterrows():
        status = row.get("status", "unknown")
        status_label = "overdue" if status == "overdue" else status
        results.append({
            "invoice_number": row.get("invoice_number", ""),
            "status": status,
            "amount": row.get("amount", ""),
            "due_date": row.get("due_date", ""),
        })
        lines.append(
            f"• {row.get('invoice_number','')} — {status_label.capitalize()}, "
            f"£{row.get('amount','N/A')}, due {row.get('due_date','N/A')}"
        )

    summary = (
        f"Outstanding invoices for {normalize(req.supplier_code)} "
        f"({len(results)} total):\n" + "\n".join(lines)
    )

    return {
        "found": True,
        "supplier_code": normalize(req.supplier_code),
        "unpaid_invoices": results,
        "display_message": summary,
    }


@app.post("/raise-query")
def raise_query(req: QueryRequest):
    """Log a new query against an invoice in the Queries sheet."""
    if not find_supplier(req.supplier_code):
        return {
            "success": False,
            "display_message": (
                f"Supplier code {normalize(req.supplier_code)} was not recognised. "
                "Query was not submitted."
            ),
        }

    invoice = find_invoice(req.supplier_code, req.invoice_number)
    if not invoice:
        return {
            "success": False,
            "display_message": (
                f"Invoice {normalize(req.invoice_number)} was not found for supplier "
                f"{normalize(req.supplier_code)}. Query was not submitted."
            ),
        }

    if not req.query_message.strip():
        return {
            "success": False,
            "display_message": "Query message cannot be empty. Please provide details.",
        }

    try:
        append_query_to_excel(req.supplier_code, req.invoice_number, req.query_message)
    except Exception as e:
        return {
            "success": False,
            "display_message": (
                "There was a problem saving your query. Please try again later."
            ),
        }

    return {
        "success": True,
        "supplier_code": normalize(req.supplier_code),
        "invoice_number": normalize(req.invoice_number),
        "display_message": (
            f"Your query for invoice {normalize(req.invoice_number)} has been submitted successfully. "
            "Our team will review it and get back to you."
        ),
    }


@app.post("/general-question")
def general_question(req: GeneralQuestionRequest):
    """
    Catch-all endpoint for general questions.
    Returns a helpful fallback message directing the user to specific endpoints.
    """
    question = req.question.strip()

    return {
        "received": True,
        "question": question,
        "display_message": (
            "Thank you for your question. "
            "I can help you with the following:\n"
            "• Verify a supplier\n"
            "• Check invoice status\n"
            "• Look up a payment or due date\n"
            "• List outstanding invoices\n"
            "• Raise a query against an invoice\n\n"
            "Please provide your supplier code and, where relevant, your invoice number "
            "so I can assist you further."
        ),
    }
