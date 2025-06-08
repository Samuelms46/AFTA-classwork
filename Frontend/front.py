import streamlit as st
import requests
import os

# Set page configuration
st.set_page_config(page_title="Fintech App - User Input", layout="centered")

# FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL","http://localhost:8000/calculate_advance")

# Title and description
st.title("💸Advance and Loan Calculator")
st.write("Enter your financial details below to request an advance or calculate a loan.")

with st.form(key="user_input_form"):
    st.header("Salary Details")
    gross_salary = st.number_input(
        "Gross Salary ($)",
        min_value=0.0,
        step=100.0,
        format="%.2f",
        help="Enter your gross salary (before taxes)."
    )
    pay_frequency = st.selectbox(
        "Pay Frequency",
        options=["Weekly", "Bi-Weekly", "Monthly", "Annually"],
        help="Select how often you are paid."
    )

    # Requested Advance Amount
    st.header("Advance Request")
    advance_amount = st.number_input(
        "Requested Advance Amount ($)",
        min_value=0.0,
        step=50.0,
        format="%.2f",
        help="Enter the amount you wish to request as an advance."
    )

    # Optional Loan Details
    st.header("Loan Details")
    include_loan = st.checkbox("Include Loan Calculation", help="Check to enter loan details.")

    loan_amount = None
    interest_rate = None
    loan_term = None

    if include_loan:
        loan_amount = st.number_input(
            "Loan Amount ($)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            help="Enter the loan amount."
        )
        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.2f",
            help="Enter the annual interest rate for the loan."
        )
        loan_term = st.number_input(
            "Loan Term (Months)",
            min_value=1,
            step=1,
            help="Enter the loan term in months."
        )

    # Submit button
    submit_button = st.form_submit_button(label="Submit")

# Handle form submission
if submit_button:
    # Prepare data for backend
    payload = {
        "gross_salary": gross_salary,
        "pay_frequency": pay_frequency,
        "advance_amount": advance_amount,
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "loan_term": loan_term
    }

    try:
        # Send request to FastAPI backend
        response = requests.post(BACKEND_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        # Display results
        st.subheader("Advance Calculation Result")
        st.write(f"**Eligibility**: {'Eligible' if result['eligible'] else 'Not Eligible'}")
        st.write(f"**Maximum Advance**: ${result['max_advance']:,.2f}")
        st.write(f"**Approved Amount**: ${result['approved_amount']:,.2f}")
        st.write(f"**Fee**: ${result['fee']:,.2f}")
        st.write(f"**Message**: {result['message']}")
        if result['loan_id']:
            st.write(f"**Loan ID**: {result['loan_id']}")

    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with backend: {str(e)}")