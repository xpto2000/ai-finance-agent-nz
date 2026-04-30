import pandas as pd


def merge_bank_files(uploaded_files):
    all_dfs = []

    for file in uploaded_files:
        df = pd.read_csv(file)

        # Standardise column names
        df.columns = [c.strip().lower() for c in df.columns]

        if "date" not in df.columns or "amount" not in df.columns:
            continue

        all_dfs.append(df)

    if not all_dfs:
        return None

    combined = pd.concat(all_dfs, ignore_index=True)

    # NZ/AU style dates: 05/01/2024 = 5 Jan 2024
    combined["date"] = pd.to_datetime(
        combined["date"],
        dayfirst=True,
        errors="coerce",
    )

    combined = combined.dropna(subset=["date", "amount"])

    combined["amount"] = pd.to_numeric(combined["amount"], errors="coerce")
    combined = combined.dropna(subset=["amount"])

    combined = combined.sort_values(by="date")
    combined["date"] = combined["date"].dt.strftime("%d/%m/%Y")

    return combined