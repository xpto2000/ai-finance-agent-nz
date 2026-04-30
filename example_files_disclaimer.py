import pandas as pd


DISCLAIMER_TEXT = (
    "Disclaimer: This tool is for general budgeting and personal finance education only. "
    "It does not provide financial, investment, tax, legal, mortgage, insurance, KiwiSaver, "
    "accounting, or tax advice. Transaction categorisation is automated and may be inaccurate, "
    "especially where bank descriptions are unclear or transfers are involved. Always review the "
    "categorised transactions and totals before making financial decisions. For advice specific "
    "to your situation, speak with a qualified financial adviser, accountant, "
    "tax adviser, or other appropriate professional."
 )


def dataframe_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def get_example_csvs():
    example_basic = pd.DataFrame(
        [
            {"date": "01/03/2026", "description": "Salary Payment ABC Limited", "amount": 4250.00},
            {"date": "02/03/2026", "description": "Countdown Auckland CBD", "amount": -142.35},
            {"date": "03/03/2026", "description": "Z Energy Kingsland", "amount": -118.20},
            {"date": "04/03/2026", "description": "Spark NZ Ltd Mobile", "amount": -89.00},
            {"date": "05/03/2026", "description": "Transfer to Savings Account", "amount": -600.00},
            {"date": "06/03/2026", "description": "Netflix Subscription", "amount": -24.99},
            {"date": "07/03/2026", "description": "Chemist Warehouse", "amount": -38.70},
            {"date": "07/03/2026", "description": "Pak n Save Glen Innes", "amount": -223.45},
            {"date": "08/03/2026", "description": "IRD Refund", "amount": 320.45},
        ]
    )

    example_details = pd.DataFrame(
        [
            {"date": "5/03/2026", "details": "New World Victoria Park", "amount": -96.40},
            {"date": "6/03/2026", "details": "Auckland Transport AT HOP", "amount": -50.00},
            {"date": "7/03/2026", "details": "Mercury Energy", "amount": -214.56},
            {"date": "7/03/2026", "details": "Watercare Services", "amount": -78.30},
            {"date": "11/03/2026", "details": "Air New Zealand", "amount": -385.00},
            {"date": "15/03/2026", "details": "Transfer from Savings Account", "amount": 500.00},
            {"date": "16/03/2026", "details": "Sharesies Investment", "amount": -250.00},
        ]
    )

    example_payee_reference = pd.DataFrame(
        [
            {"date": "2/03/2026", "payee": "Rent Payment", "reference": "Weekly rent", "amount": -720.00},
            {"date": "3/03/2026", "payee": "Pak n Save Albany", "reference": "Groceries", "amount": -183.22},
            {"date": "4/03/2026", "payee": "BP Connect", "reference": "Fuel", "amount": -102.10},
            {"date": "4/03/2026", "payee": "One NZ", "reference": "Mobile plan", "amount": -65.00},
            {"date": "11/03/2026", "payee": "Uber Eats", "reference": "Dinner", "amount": -44.80},
            {"date": "14/03/2026", "payee": "Trademe shopping", "reference": "Bhy98#", "amount": -41.33},
            {"date": "14/03/2026", "payee": "Auckland Council", "reference": "Rates", "amount": -540.00},
        ]
    )

    return {
        "example_nz_bank_basic.csv": example_basic,
        "example_nz_bank_details_column.csv": example_details,
        "example_nz_bank_payee_reference.csv": example_payee_reference,
    }