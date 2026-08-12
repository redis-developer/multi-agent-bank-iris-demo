"""Banking ACTION tools the agents can call.

Each tool writes (or gates a write to) real state in Redis: NOCs are only
issued for closed loans, LANs are generated from a Redis counter, and
disbursements flip journey state.

Note what is NOT here: the read tools (profile, loans, offers). Those are
*generated* from the semantic model in `src/context/retriever.py` — the
Section 4 Context Retriever exercise. Hand-written code is for actions;
retrieval is declared, not coded.
"""

import json
from datetime import date

from langchain_core.tools import tool

from src import config
from src.data.loader import get_redis

def _get_loan(r, lan: str):
    """Read a loan record whether it was written as JSON (this app's action
    tools) or as a hash (records imported through the Context Retriever)."""
    key = f"{config.LOAN_KEY_PREFIX}{lan}"
    try:
        loan = r.json().get(key)
        if loan:
            return loan
    except Exception:
        pass
    data = r.hgetall(key)
    return data or None


REQUIRED_DOCS = {
    "salaried": ["pan", "aadhaar", "salary slips", "bank statement"],
    "self_employed": ["pan", "aadhaar", "itr", "bank statement",
                      "business proof"],
    "preapproved": ["pan", "aadhaar"],
}


@tool
def calculate_emi(principal: float, annual_rate: float,
                  tenure_months: int) -> str:
    """Calculate the monthly EMI, total interest, and total payable for a
    loan using the reducing-balance formula. annual_rate is in percent,
    e.g. 11.5 for 11.5% p.a."""
    r = annual_rate / 12 / 100
    if r == 0:
        emi = principal / tenure_months
    else:
        factor = (1 + r) ** tenure_months
        emi = principal * r * factor / (factor - 1)
    total = emi * tenure_months
    return json.dumps({
        "emi": round(emi),
        "total_interest": round(total - principal),
        "total_payable": round(total),
        "principal": principal,
        "annual_rate": annual_rate,
        "tenure_months": tenure_months,
    })


@tool
def check_noc_eligibility(customer_id: str, lan: str) -> str:
    """Check whether an NOC can be issued for a loan: the loan must belong to
    the customer and its status must be 'closed' with zero outstanding."""
    loan = _get_loan(get_redis(), lan)
    if not loan:
        return f"No loan found for LAN {lan}."
    if loan["customer_id"] != customer_id:
        return "This LAN does not belong to the verified customer."
    if loan["status"] != "closed" or float(loan.get("outstanding", 1)) != 0:
        return json.dumps({
            "eligible": False,
            "reason": f"Loan {lan} is {loan['status']} with outstanding "
                      f"₹{loan.get('outstanding', 'unknown')}. NOC is only "
                      "issued after full closure.",
        })
    return json.dumps({"eligible": True, "lan": lan,
                       "closed_on": loan.get("closed_on")})


@tool
def issue_noc(customer_id: str, lan: str) -> str:
    """Issue a digital NOC for a CLOSED loan. Always run
    check_noc_eligibility first. Returns the NOC reference number."""
    r = get_redis()
    loan = _get_loan(r, lan)
    if not loan or loan["status"] != "closed":
        return "Cannot issue NOC: loan is not closed."
    ref = f"NOC-{lan}-{date.today().strftime('%Y%m%d')}"
    r.json().set(f"{config.NOC_KEY_PREFIX}{lan}", "$", {
        "noc_ref": ref, "lan": lan, "customer_id": customer_id,
        "issued_on": date.today().isoformat(), "channel": "whatsapp",
    })
    return json.dumps({"noc_ref": ref,
                       "delivery": "PDF sent on WhatsApp and registered email "
                                   "within 15 working days (digital copy is "
                                   "usually instant)."})


@tool
def qualify_documents(customer_type: str, documents_provided: list[str]) -> str:
    """Qualify uploaded documents against the checklist for the customer
    type: 'salaried', 'self_employed', or 'preapproved'. Returns what is
    missing, if anything."""
    required = REQUIRED_DOCS.get(customer_type)
    if not required:
        return "customer_type must be salaried, self_employed, or preapproved."
    provided = {d.strip().lower() for d in documents_provided}
    missing = [doc for doc in required if doc not in provided]
    return json.dumps({"qualified": not missing, "required": required,
                       "missing": missing})


@tool
def generate_lan(customer_id: str, product: str, amount: float,
                 annual_rate: float, tenure_months: int) -> str:
    """Generate a new Loan Account Number (LAN) once documents qualify and
    the customer accepts the offer terms. Creates the loan in 'sanctioned'
    state."""
    r = get_redis()
    seq = r.incr(config.LAN_COUNTER_KEY)
    lan = f"LAN{date.today().year}{seq:04d}"
    r.json().set(f"{config.LOAN_KEY_PREFIX}{lan}", "$", {
        "lan": lan, "customer_id": customer_id, "product": product,
        "principal": amount, "annual_rate": annual_rate,
        "tenure_months": tenure_months, "status": "sanctioned",
        "outstanding": amount,
    })
    return json.dumps({"lan": lan, "status": "sanctioned",
                       "next_step": "e-sign the sanction letter, then "
                                    "disbursement can be initiated."})


@tool
def initiate_disbursement(lan: str) -> str:
    """Initiate disbursement for a sanctioned LAN. Flips the loan to
    'active' and returns the expected credit time."""
    r = get_redis()
    key = f"{config.LOAN_KEY_PREFIX}{lan}"
    loan = r.json().get(key)  # disbursement applies to app-sanctioned loans
    if not loan:
        return f"No loan found for LAN {lan}."
    if loan["status"] != "sanctioned":
        return f"Loan {lan} is {loan['status']}; only sanctioned loans can be disbursed."
    r.json().set(key, "$.status", "active")
    r.json().set(key, "$.disbursed_on", date.today().isoformat())
    return json.dumps({"lan": lan, "status": "disbursement_initiated",
                       "eta": "within 4 business hours for pre-approved, "
                              "otherwise 24–48 hours",
                       "first_emi_due": "5th of next month"})
