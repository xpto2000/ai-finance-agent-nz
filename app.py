# ------------------------------------------------------------
# Standard + third-party imports
# ------------------------------------------------------------
# html: safely render text in UI (used for summaries if needed)
# json + re: used to extract structured JSON from AI responses
import html
import json
import re

# Data processing + visualisation
import pandas as pd
import plotly.express as px

# Streamlit = UI framework
import streamlit as st

# CrewAI = agent orchestration (LLM tasks)
from crewai import Crew, Task


# ------------------------------------------------------------
# Internal modules (your project logic)
# ------------------------------------------------------------
# agents: defines AI roles (analyst + coach)
# classification_rules: builds prompt for AI classification
# example_files_disclaimer: disclaimer + sample CSVs
# processor: merges and cleans uploaded CSV files
from agents import get_analyst_agent, get_coach_agent
from classification_rules import NZ_CATEGORIES, build_classification_prompt
from example_files_disclaimer import (
    DISCLAIMER_TEXT,
    dataframe_to_csv_bytes,
    get_example_csvs,
)
from processor import merge_bank_files


# ------------------------------------------------------------
# Streamlit page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="AI Finance Agent NZ",
    page_icon="💸",
    layout="wide",
)

st.title("💸 AI Finance Agent NZ")

# Show disclaimer at the top so users understand limitations
st.warning(DISCLAIMER_TEXT)

st.write("Upload your NZ bank CSV files to categorise money in and money out.")


# ------------------------------------------------------------
# Example CSV downloads (helps users understand format)
# ------------------------------------------------------------
st.subheader("Example CSV files")

example_csvs = get_example_csvs()
cols = st.columns(len(example_csvs))

# Create a download button for each example file
for col, (filename, df) in zip(cols, example_csvs.items()):
    with col:
        st.download_button(
            label=f"Download {filename}",
            data=dataframe_to_csv_bytes(df),
            file_name=filename,
            mime="text/csv",
        )


# ------------------------------------------------------------
# File uploader (main input from user)
# ------------------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload bank CSV files",
    type=["csv"],
    accept_multiple_files=True,
)


# ------------------------------------------------------------
# Helper: safely extract JSON from AI output
# AI sometimes returns extra text → we extract the JSON block
# ------------------------------------------------------------
def extract_json_from_text(text):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\[.*\]", str(text), re.DOTALL)
        if match:
            return json.loads(match.group(0))
    return None


# ------------------------------------------------------------
# Helper: format NZD currency nicely
# ------------------------------------------------------------
def format_nzd(value):
    return f"NZ${value:,.2f}"

def clean_summary_text(text):
    text = str(text)

    # Fix numbers like "5 , 070 . 45"
    text = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', text)
    text = re.sub(r'(\d)\s*\.\s*(\d)', r'\1.\2', text)

    # Fix currency spacing: "N Z $ 5,000" → "NZ$5,000"
    text = re.sub(r'N\s*Z\s*\$\s*', 'NZ$', text)

    # Collapse multiple spaces (but keep normal spacing)
    text = re.sub(r'\s{2,}', ' ', text)

    return text.strip()

# ------------------------------------------------------------
# Main logic (runs only after files are uploaded)
# ------------------------------------------------------------
if uploaded_files:

    # Merge multiple CSVs into one clean dataset
    combined_data = merge_bank_files(uploaded_files)

    # Stop execution if no valid data
    if combined_data is None or combined_data.empty:
        st.error("No valid transactions found.")
        st.stop()

    # Ensure amount column is numeric
    combined_data["amount"] = pd.to_numeric(combined_data["amount"], errors="coerce")

    # Drop invalid rows and reset index
    combined_data = combined_data.dropna(subset=["amount"]).reset_index(drop=True)

    # Create unique ID per transaction (used for AI mapping)
    combined_data["transaction_id"] = combined_data.index

    # Display raw combined transactions
    st.subheader("Combined Transactions")
    st.dataframe(combined_data, use_container_width=True)


    # --------------------------------------------------------
    # Run analysis when button is clicked
    # --------------------------------------------------------
    if st.button("Analyse Spending"):

        # Create AI agents
        analyst = get_analyst_agent()   # classification agent
        coach = get_coach_agent()       # summary/advice agent

        # Select relevant columns to send to AI
        columns_to_send = ["transaction_id", "date", "amount"]

        # Dynamically include optional fields (depends on bank CSV format)
        for col in [
            "description",
            "details",
            "particulars",
            "payee",
            "memo",
            "reference",
            "code",
            "transaction type",
            "type",
        ]:
            if col in combined_data.columns:
                columns_to_send.append(col)

        classification_input = combined_data[columns_to_send]


        # ----------------------------------------------------
        # Task 1: AI classification of transactions
        # ----------------------------------------------------
        task1 = Task(
            description=build_classification_prompt(classification_input),
            agent=analyst,
            expected_output="Valid JSON classification of transactions.",
        )

        # Create crew (agent + task)
        crew1 = Crew(
            agents=[analyst],
            tasks=[task1],
            verbose=True,
        )

        # Run classification
        with st.spinner("Classifying transactions with AI..."):
            result1 = crew1.kickoff()

        # Extract JSON from AI output
        category_json = extract_json_from_text(result1.tasks_output[0].raw)

        # Fail safely if AI output is invalid
        if not category_json:
            st.error("AI classification failed.")
            st.stop()

        # Map AI output back to dataframe using transaction_id
        ai_map = {
            item["transaction_id"]: item["category"]
            for item in category_json
        }

        combined_data["category"] = combined_data["transaction_id"].map(ai_map)

        # Fallback for any missing classifications
        combined_data["category"] = combined_data.apply(
            lambda row: row["category"]
            if pd.notna(row["category"])
            else ("Other Income" if row["amount"] > 0 else "Other Expense"),
            axis=1,
        )


        # ----------------------------------------------------
        # Split money in vs money out
        # ----------------------------------------------------
        money_in_df = combined_data[combined_data["amount"] > 0].copy()
        money_out_df = combined_data[combined_data["amount"] < 0].copy()

        # Convert expenses to positive for aggregation
        money_out_df["amount_abs"] = money_out_df["amount"].abs()

        # Calculate totals
        total_in = money_in_df["amount"].sum()
        total_out = money_out_df["amount_abs"].sum()
        net_position = total_in - total_out


        # ----------------------------------------------------
        # Display summary metrics
        # ----------------------------------------------------
        st.divider()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Money In", format_nzd(total_in))
        col2.metric("Total Money Out", format_nzd(total_out))
        col3.metric("Net Position", format_nzd(net_position))


        # ----------------------------------------------------
        # Charts (Money In vs Money Out breakdown)
        # ----------------------------------------------------
        st.divider()

        chart_col1, chart_col2 = st.columns(2)

        # Money IN chart
        with chart_col1:
            st.subheader("💰 Money In")

            if not money_in_df.empty:
                money_in_summary = (
                    money_in_df.groupby("category", as_index=False)["amount"]
                    .sum()
                    .sort_values("amount", ascending=False)
                )

                fig_in = px.pie(
                    money_in_summary,
                    values="amount",
                    names="category",
                    hole=0.4,
                )

                st.plotly_chart(fig_in, use_container_width=True)

        # Money OUT chart
        with chart_col2:
            st.subheader("💸 Money Out")

            if not money_out_df.empty:
                money_out_summary = (
                    money_out_df.groupby("category", as_index=False)["amount_abs"]
                    .sum()
                    .sort_values("amount_abs", ascending=False)
                )

                fig_out = px.pie(
                    money_out_summary,
                    values="amount_abs",
                    names="category",
                    hole=0.4,
                )

                st.plotly_chart(fig_out, use_container_width=True)


        # ----------------------------------------------------
        # Show final categorised transactions
        # ----------------------------------------------------
        st.subheader("Categorised Transactions")
        st.dataframe(combined_data, use_container_width=True)


        # ----------------------------------------------------
        # Task 2: AI financial summary / coaching
        # ----------------------------------------------------
        task2 = Task(
            description=(
                "Write a warm, clear, structured, practical financial summary for a New Zealand user.\n"
                "Be encouraging and realistic.\n"
                "Give useful next steps without judgement.\n\n"
                "Formatting rules:\n"
                "- Use short paragraphs\n"
                "- Use bullet points for suggestions\n"
                "- Use simple emojis for sections (e.g. 💡 📊 💰)\n"
                "- Do NOT use asterisks, underscores, or markdown formatting like bold/italic\n"
                "- Do NOT break words or numbers\n"
                "- Check all text before sending to make sure everything is clean, following the formatting rules, and readable\n\n"
                "Structure:\n"
                "1. Short positive opening\n"
                "2. Summary of numbers\n"
                "3. 2 or 3 key insights (bullet points)\n"
                "4. 2 or 3 practical actions (bullet points)\n"
            ),
            agent=coach,
            expected_output="Helpful financial suggestions.",
        )

        crew2 = Crew(
            agents=[coach],
            tasks=[task2],
            verbose=True,
        )

        # Generate summary
        with st.spinner("Generating financial summary..."):
            result2 = crew2.kickoff()

        st.subheader("💬 Your Financial Summary")
        summary_text = clean_summary_text(result2.tasks_output[0].raw)
        st.markdown(summary_text)


# ------------------------------------------------------------
# Default state (before any files are uploaded)
# ------------------------------------------------------------
else:
    st.info("Upload CSV files to begin.")