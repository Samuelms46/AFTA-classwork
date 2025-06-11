# 💵 Advanced Salary & Loan Calculator App 

This app is designed to assist users in requesting salary advances and calculating loan repayments. The application is built using a microservices architecture.

## 🔧 Project Overview & Architecture

- **Backend**: A FastAPI service that handles business logic, including eligibility checks, advance calculations, compound interest computations, and optional amortization schedules using Pandas. It runs on port `8000`

- **Frontend**: A Streamlit-based web interface that provides an interactive UI for users to input financial details and view results. It runs on port `8501` and communicates with the backend via HTTP requests.

The architecture is containerized using Docker Compose, with both services running in separate containers and communicating over a custom bridge network (`fintech`). The backend processes data and stores loan details in an in-memory store (replaceable with a database for production), while the frontend displays real-time results, including amortization schedules when requested.

## 🔗 API Endpoint Descriptions

- **POST `/calculate_advance`**  
  - **Description**: Calculates salary advance eligibility, maximum advance amount, fees, and optional loan repayment details (total repayable amount and amortization schedule).
  - **Request Body**: JSON object with:
    - `gross_salary` (float): User's gross salary.
    - `pay_frequency` (str): Pay frequency ("Weekly", "Bi-Weekly", "Monthly", "Annually").
    - `advance_amount` (float): Requested advance amount.
    - `loan_amount` (float, optional): Loan principal amount.
    - `interest_rate` (float, optional): Annual interest rate in percentage.
    - `loan_term` (int, optional): Loan term in months.
    - `include_amortization` (bool, optional): Flag to generate an amortization schedule.
  - **Response**: JSON object with:
    - `eligible` (bool): Eligibility status.
    - `max_advance` (float): Maximum allowable advance.
    - `approved_amount` (float): Approved advance amount.
    - `fee` (float): Calculated fee.
    - `total_repayable` (float, optional): Total loan repayment amount.
    - `amortization_schedule` (list, optional): Monthly payment breakdown.
    - `message` (str): Status message.
    - `loan_id` (str, optional): Unique loan identifier.
  - **Example**: `curl -X POST http://localhost:8000/calculate_advance -H "Content-Type: application/json" -d '{"gross_salary": 5000, "pay_frequency": "Monthly", "advance_amount": 1000, "loan_amount": 5000, "interest_rate": 5, "loan_term": 12, "include_amortization": true}'`

- **GET `/loan/{loan_id}`**  
  - **Description**: Retrieves details of a specific loan by its ID.
  - **Path Parameter**: `loan_id` (str): Unique identifier of the loan.
  - **Response**: JSON object containing loan details (e.g., advance amount, fee, loan amount, etc.).
  - **Example**: `curl http://localhost:8000/loan/<loan_id>`

## Pandas Logic Explained

Pandas is utilized in the FastAPI backend for financial calculations, ensuring efficient data manipulation and computation:

- **Compound Interest Calculation**: 
  - The `calculate_compound_interest` function creates a Pandas DataFrame to store the principal, rate per period, and number of compounding periods. It applies the compound interest formula \( A = P \left(1 + \frac{r}{n}\right)^{nt} \) (where \( n = 12 \) for monthly compounding, \( t \) is in years) using vectorized operations, returning the total repayable amount rounded to two decimal places.

- **Amortization Schedule Generation**: 
  - The `generate_amortization_schedule` function uses a Pandas DataFrame to compute a monthly payment schedule. It calculates the fixed monthly payment using the formula \( PMT = P \cdot \frac{r (1+r)^n}{(1+r)^n - 1} \) (where \( r \) is the monthly rate, \( n \) is the number of months), then iteratively updates the balance, interest, and principal paid for each month. The result is converted to a list of dictionaries for API response, with values rounded to two decimal places for clarity.

This approach leverages Pandas' data handling capabilities to ensure accuracy and scalability in financial computations.

## Setup Instructions

To set up and run the project locally:

```bash
git clone https://github.com/Samuelms46/AFTA-classwork.git
docker compose build
docker compose up
```

- **Prerequisites**: Install Docker and Docker Compose (see [docker.com](https://docs.docker.com/get-docker/) for instructions).
- **Post-Setup**: Access the frontend at `http://localhost:8501` and the backend Swagger UI at `http://localhost:8000/docs`.

## Assumptions Made

- **Loan Logic**: Eligibility requires a minimum monthly salary of $1000. The maximum advance is 50% of the monthly salary. A simple fee model applies (5% of the advance amount, with a minimum of $10 and a maximum of $50). Compound interest assumes monthly compounding \( n = 12 \), and the amortization schedule uses a fixed-rate loan formula.
- **Storage**: Loan details are stored in an in-memory dictionary for simplicity (intended for development; it can be replaced with a database like PostgreSQL in production).
- **Networking**: The frontend communicates with the backend using the service name `backend` within the Docker network, with `BACKEND_URL` set to `http://backend:8000/calculate_advance`.
- **Dependencies**: All required Python packages are listed in `requirements.txt` files, compatible with Python 3.12.

## Deployed URL

