from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

# Initialize FastAPI app
app = FastAPI(title="Fintech App - Salary Advance API")

# Define input model for salary advance request
class AdvanceRequest(BaseModel):
    gross_salary: float
    pay_frequency: str
    advance_amount: float
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    loan_term: Optional[int] = None

# Define response model for advance calculation
class AdvanceResponse(BaseModel):
    eligible: bool
    max_advance: float
    approved_amount: float
    fee: float
    message: str
    loan_id: Optional[str] = None

# In-memory store for loans (replace with database in production)
loans_db = {}

# Helper function to convert annual salary to monthly for consistency
def convert_to_monthly_salary(gross_salary: float, pay_frequency: str) -> float:
    if pay_frequency == "Weekly":
        return gross_salary * 52 / 12  # 52 weeks in a year
    elif pay_frequency == "Bi-Weekly":
        return gross_salary * 26 / 12  # 26 bi-weekly periods
    elif pay_frequency == "Monthly":
        return gross_salary
    elif pay_frequency == "Annually":
        return gross_salary / 12
    else:
        raise ValueError("Invalid pay frequency")

# Endpoint to calculate salary advance
@app.post("/calculate_advance", response_model=AdvanceResponse)
async def calculate_advance(request: AdvanceRequest):
    try:
        # Step 1: Determine eligibility
        monthly_salary = convert_to_monthly_salary(request.gross_salary, request.pay_frequency)
        min_salary_threshold = 1000  # Minimum monthly salary for eligibility ($1000)
        eligible = monthly_salary >= min_salary_threshold

        if not eligible:
            return AdvanceResponse(
                eligible=False,
                max_advance=0.0,
                approved_amount=0.0,
                fee=0.0,
                message="Ineligible: Monthly salary is below the minimum threshold of $1000."
            )

        # Step 2: Calculate maximum advance (e.g., 50% of monthly salary)
        max_advance = monthly_salary * 0.5

        # Step 3: Perform final checks
        if request.advance_amount > max_advance:
            return AdvanceResponse(
                eligible=True,
                max_advance=max_advance,
                approved_amount=0.0,
                fee=0.0,
                message=f"Requested advance (${request.advance_amount:,.2f}) exceeds maximum allowed (${max_advance:,.2f})."
            )

        # Step 4: Calculate fee (simple fee model: 5% of advance amount, min $10, max $50)
        fee = max(10.0, min(50.0, request.advance_amount * 0.05))

        # Step 5: Record the loan
        loan_id = str(uuid.uuid4())
        loan_record = {
            "loan_id": loan_id,
            "advance_amount": request.advance_amount,
            "fee": fee,
            "timestamp": datetime.now().isoformat(),
            "gross_salary": request.gross_salary,
            "pay_frequency": request.pay_frequency,
            "loan_amount": request.loan_amount,
            "interest_rate": request.interest_rate,
            "loan_term": request.loan_term
        }
        loans_db[loan_id] = loan_record

        # Step 6: Return response
        message = f"Advance approved! Amount: ${request.advance_amount:,.2f}, Fee: ${fee:,.2f}"
        if request.loan_amount and request.interest_rate and request.loan_term:
            message += f". Loan details recorded: ${request.loan_amount:,.2f} at {request.interest_rate}% for {request.loan_term} months."

        return AdvanceResponse(
            eligible=True,
            max_advance=max_advance,
            approved_amount=request.advance_amount,
            fee=fee,
            message=message,
            loan_id=loan_id
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Endpoint to retrieve loan details (for verification)
@app.get("/loan/{loan_id}")
async def get_loan(loan_id: str):
    if loan_id not in loans_db:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loans_db[loan_id]