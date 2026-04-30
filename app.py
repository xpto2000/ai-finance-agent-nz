import html
import json
import re

import pandas as pd
import plotly.express as px
import streamlit as st
from crewai import Crew, Task

from agents import get_analyst_agent, get_coach_agent
from classification_rules import NZ_CATEGORIES, build_classification_prompt
from example_files_disclaimer import (
    DISCLAIMER_TEXT,
    dataframe_to_csv_bytes,
    get_example_csvs,
)
from processor import merge_bank_files


st.set_page_config(
    page_title="AI Finance Agent NZ",
    page_icon="💸",
    layout="wide",
)

st.title("💸 AI Finance Agent NZ")

st.warning(DISCLAIMER_TEXT)

st.write("Upload your NZ bank CSV files to categorise money in and money out.")

st.subheader("Example CSV files")

example_csvs = get_example_csvs()

cols = st.columns(len(example_csvs))

for col, (filename, df) in zip(cols, example_csvs.items()):
    with col:
        st.download_button(
            label=f"Download {filename}",
            data=dataframe_to_csv_bytes(df),
            file_name=filename,
            mime="text/csv",
        )


uploaded_files = st.file_uploader(
    "Upload bank CSV files",
    type=["csv"],
    accept_multiple_files=True,
)


def extract_json_from_text(text):
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\[.*\]", str(text), re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None


def clean_summary_text(text):
    text = str(text)
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("#", "")
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("_", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def display_summary_card(summary_text):
    safe_text = html.escape(summary_text)
    summary_html = safe_text.replace("\n", "<br>")

    st.markdown(
        f"""
        <div style="
            background-color: white;
            color: #111;
            padding: 22px;
            border-radius: 12px;
            border: 1px solid #ddd;
            font-size: 16px;
            line-height: 1.6;
            font-family: Arial, sans-serif;
            margin-top: 10px;
            margin-bottom: 20px;
        ">
            {summary_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_nzd(value):
    return f"NZ${value:,.2f}"


if uploaded_files:
    combined_data = merge_bank_files(uploaded_files)

    if combined_data is None or combined_data.empty:
        st.error("No valid transactions found.")
        st.stop()

    combined_data["amount"] = pd.to_numeric(combined_data["amount"], errors="coerce")
    combined_data = combined_data.dropna(subset=["amount"]).reset_index(drop=True)
    combined_data["transaction_id"] = combined_data.index

    st.subheader("Combined Transactions")
    st.dataframe(combined_data, use_container_width=True)

    if st.button("Analyse Spending"):
        analyst = get_analyst_agent()
        coach = get_coach_agent()

        columns_to_send = ["transaction_id", "date", "amount"]

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

        task1 = Task(
            description=build_classification_prompt(classification_input),
            agent=analyst,
            expected_output="Valid JSON classification.",
        )

        crew1 = Crew(
            agents=[analyst],
            tasks=[task1],
            verbose=True,
        )

        with st.spinner("Classifying with AI..."):
            result1 = crew1.kickoff()

        category_json = None

        try:
            category_json = result1.tasks_output[0].json_dict
        except Exception:
            pass

        if not category_json:
            category_json = extract_json_from_text(result1.tasks_output[0].raw)

        if not category_json:
            st.error("AI classification failed.")
            st.stop()

        df_map = pd.DataFrame(category_json)

        df_map["transaction_id"] = pd.to_numeric(df_map["transaction_id"], errors="coerce")
        df_map = df_map.dropna(subset=["transaction_id"])
        df_map["transaction_id"] = df_map["transaction_id"].astype(int)

        df_map = df_map[df_map["category"].isin(NZ_CATEGORIES)]

        mapping = dict(zip(df_map["transaction_id"], df_map["category"]))

        combined_data["category"] = combined_data["transaction_id"].map(mapping)

        combined_data["category"] = combined_data.apply(
            lambda r: r["category"]
            if pd.notna(r["category"])
            else ("Other Income" if r["amount"] > 0 else "Other Expense"),
            axis=1,
        )

        money_in = combined_data[combined_data["amount"] > 0]
        money_out = combined_data[combined_data["amount"] < 0].copy()
        money_out["amount_abs"] = money_out["amount"].abs()

        total_in = money_in["amount"].sum()
        total_out = money_out["amount_abs"].sum()
        net = total_in - total_out

        st.divider()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total In", format_nzd(total_in))
        c2.metric("Total Out", format_nzd(total_out))
        c3.metric("Net", format_nzd(net))

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if not money_in.empty:
                s = money_in.groupby("category", as_index=False)["amount"].sum()
                fig = px.pie(s, values="amount", names="category", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if not money_out.empty:
                s = money_out.groupby("category", as_index=False)["amount_abs"].sum()
                fig = px.pie(s, values="amount_abs", names="category", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Categorised Transactions")
        st.dataframe(combined_data, use_container_width=True)
        task2 = Task(
            description=(
                "Write a warm, practical financial summary for a New Zealand user.\n\n"
                "Tone:\n"
                "- Encouraging, calm, and human.\n"
                "- Do not shame the user.\n"
                "- Do not say things like 'your numbers look bad'.\n"
                "- Do not give generic advice like 'consider saving more' unless it is tied to the actual data.\n"
                "- Be specific and useful.\n\n"
                "Content:\n"
                "- Start with a short plain-English overview of what happened.\n"
                "- Mention one or two positive observations if possible.\n"
                "- Point out the biggest spending areas gently.\n"
                "- Suggest realistic next actions the user could take this month.\n"
                "- Use New Zealand English and NZD context.\n"
                "- Do not provide investment, tax, mortgage, insurance, or legal advice.\n"
                "- Feel free to recommend free resources when appropriate.\n"
                "- Do not recommend specific financial products.\n"
                "- If possible provide at least one actionable tip and 5 recommendations.\n"
                "- Do not use markdown, bold, italics, or tables.\n"
                "- Use simple numbered points only.\n\n"
                f"Total money in: {format_nzd(total_in)}\n"
                f"Total money out: {format_nzd(total_out)}\n"
                f"Net position: {format_nzd(net)}\n\n"
                f"Money in by category:\n{money_in.groupby('category', as_index=False)['amount'].sum().to_string(index=False)}\n\n"
                f"Money out by category:\n{money_out.groupby('category', as_index=False)['amount_abs'].sum().sort_values(by='amount_abs', ascending=False).to_string(index=False)}"
            ),
            agent=coach,
            expected_output="A warm, practical NZ-focused financial summary with realistic suggestions.",
        )
        crew2 = Crew(agents=[coach], tasks=[task2])

        result2 = crew2.kickoff()

        st.subheader("💬 Financial Summary")
        summary = clean_summary_text(result2.tasks_output[0].raw)
        display_summary_card(summary)

else:
    st.info("Upload CSV files to begin.")