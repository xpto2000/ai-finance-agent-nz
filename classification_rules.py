import json

NZ_CATEGORIES = [
    "Salary / Wages",
    "IRD / Tax",
    "WINZ / Benefits",
    "ACC Payments",
    "Interest Income",
    "Transfers In",
    "Refunds",
    "Rent / Mortgage",
    "Rates",
    "Power",
    "Gas",
    "Water",
    "Internet / Mobile",
    "Groceries",
    "Fuel",
    "Public Transport",
    "Vehicle / Rego / WOF",
    "Insurance",
    "Healthcare / Pharmacy",
    "Dining / Takeaways",
    "Coffee / Cafes",
    "Entertainment",
    "Subscriptions",
    "Shopping",
    "Education",
    "Childcare / School",
    "Pets",
    "Travel / Holidays",
    "Flights",
    "Accommodation",
    "Bank Fees",
    "Credit Card / Loan Payments",
    "Investments / KiwiSaver",
    "Savings Transfers",
    "Cash Withdrawal",
    "Gifts / Donations",
    "Transfers Out",
    "Other Income",
    "Other Expense",
]


def build_classification_prompt(df):
    return (
        "Classify each New Zealand bank transaction into one category.\n\n"
        "Use your judgement from the transaction text and amount.\n"
        "Do not use code rules or keyword matching.\n"
        "Do not classify everything into the same category.\n"
        "Only use Other Income or Other Expense when there is truly not enough information.\n\n"
        "Important examples:\n"
        "- Inland Revenue Dept or IRD = IRD / Tax\n"
        "- Spark, One NZ, Vodafone, 2degrees, broadband, mobile, phone = Internet / Mobile\n"
        "- Transfer, online banking, payment to, payment from = Transfers In or Transfers Out depending on amount\n"
        "- Transfer to savings = Savings Transfers\n"
        "- Pak n Save, Countdown, Woolworths, New World = Groceries\n"
        "- Z Energy, BP, Mobil, Caltex = Fuel\n"
        "- Air New Zealand, Jetstar, Qantas = Flights\n"
        "- Auckland Council rates = Rates\n\n"
        "Allowed categories:\n"
        f"{json.dumps(NZ_CATEGORIES, indent=2)}\n\n"
        "Return only valid JSON like this:\n"
        "[\n"
        '  {"transaction_id": 0, "category": "Groceries"},\n'
        '  {"transaction_id": 1, "category": "Transfers Out"}\n'
        "]\n\n"
        f"Transactions:\n{df.to_string(index=False)}"
    )