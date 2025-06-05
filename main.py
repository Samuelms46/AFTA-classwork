from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import pandas as pd
import numpy as np

app = FastAPI(title="Fintech App - Salary Advance and Loan API")

# input model for salary advance and loan request
class AdvanceRequest(BaseModel):
    gross_salary: float
    pay_frequency: str
    advance_amount: float
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    loan_term: Optional[int] = None
    include_amortization: Optional[bool] = False

# response model for advance and loan calculation
class AdvanceResponse(BaseModel):
    eligible: bool
    max_advance: float
    approved_amount: float
    fee: float
    total_repayable: Optional[float] = None
    amortization_schedule: Optional[list] = None
    message: str
    loan_id: Optional[str] = None

# In-memory store for loans
loans_db = {}

# Helper function to convert annual salary to monthly
def convert_to_monthly_salary(gross_salary: float, pay_frequency: str) -> float:
    if pay_frequency == "Weekly":
        return gross_salary * 52 / 12
    elif pay_frequency == "Bi-Weekly":
        return gross_salary * 26 / 12
    elif pay_frequency == "Monthly":
        return gross_salary
    elif pay_frequency == "Annually":
        return gross_salary / 12
    else:
        raise ValueError("Invalid pay frequency")

# Helper function to calculate compound interest using Pandas
def calculate_compound_interest(principal: float, rate: float, term_months: int) -> float:
    n = 12  # Monthly compounding
    t = term_months / 12  # Convert months to years
    rate = rate / 100  # Convert percentage to decimal
    
    # Pandas DataFrame for calculation
    df = pd.DataFrame({
        "principal": [principal],
        "rate_per_period": [rate / n],
        "periods": [n * t]
    })
    
    # Calculate total repayable amount using compound interest formula
    df["total_repayable"] = df["principal"] * (1 + df["rate_per_period"]) ** df["periods"]
    return round(df["total_repayable"].iloc[0], 2)

# Helper function to generate amortization schedule using Pandas
def generate_amortization_schedule(principal: float, rate: float, term_months: int) -> list:
    monthly_rate = rate / 100 / 12
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    monthly_payment = round(monthly_payment, 2)

    # Initialize DataFrame for amortization schedule
    df = pd.DataFrame({
        "Month": range(1, term_months + 1),
        "Balance": principal,
        "Payment": monthly_payment
    })
    
    # Calculate interest, principal paid, and remaining balance
    df["Interest"] = df["Balance"] * monthly_rate
    df["Principal"] = df["Payment"] - df["Interest"]
    df["Balance"] = df["Balance"].shift(1, fill_value=principal) - df["Principal"].cumsum()
    df["Balance"] = df["Balance"].clip(lower=0)  # Ensure balance doesn't go negative
    
    # Format DataFrame and convert to list of dictionaries
    df = df[["Month", "Payment", "Principal", "Interest", "Balance"]]
    df = df.round(2)
    return df.to_dict("records")

# Endpoint to calculate salary advance and loan
@app.post("/calculate_advance", response_model=AdvanceResponse)
async def calculate_advance(request: AdvanceRequest):
    try:
        # Step 1: Determine eligibility
        monthly_salary = convert_to_monthly_salary(request.gross_salary, request.pay_frequency)
        min_salary_threshold = 1000
        eligible = monthly_salary >= min_salary_threshold

        if not eligible:
            return AdvanceResponse(
                eligible=False,
                max_advance=0.0,
                approved_amount=0.0,
                fee=0.0,
                message="Ineligible: Monthly salary is below the minimum threshold of $1000."
            )

        # Step 2: Calculate maximum advance (50% of monthly salary)
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

        # Step 4: Calculate fee (5% of advance, min $10, max $50)
        fee = max(10.0, min(50.0, request.advance_amount * 0.05))

        # Step 5: Calculate loan repayment (if provided)
        total_repayable = None
        amortization_schedule = None
        if request.loan_amount and request.interest_rate and request.loan_term:
            total_repayable = calculate_compound_interest(
                request.loan_amount, request.interest_rate, request.loan_term
            )
            if request.include_amortization:
                amortization_schedule = generate_amortization_schedule(
                    request.loan_amount, request.interest_rate, request.loan_term
                )

        # Step 6: Record the loan
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
            "loan_term": request.loan_term,
            "total_repayable": total_repayable,
            "amortization_schedule": amortization_schedule
        }
        loans_db[loan_id] = loan_record

        # Step 7: Return response
        message = f"Advance approved! Amount: ${request.advance_amount:,.2f}, Fee: ${fee:,.2f}"
        if total_repayable:
            message += f". Loan repayable: ${total_repayable:,.2f} over {request.loan_term} months."

        return AdvanceResponse(
            eligible=True,
            max_advance=max_advance,
            approved_amount=request.advance_amount,
            fee=fee,
            total_repayable=total_repayable,
            amortization_schedule=amortization_schedule,
            message=message,
            loan_id=loan_id
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Endpoint to retrieve loan details
@app.get("/loan/{loan_id}")
async def get_loan(loan_id: str):
    if loan_id not in loans_db:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loans_db[loan_id]