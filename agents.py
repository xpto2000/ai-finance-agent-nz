import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

MY_LLM = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)


def get_analyst_agent():
    return Agent(
        role="New Zealand Bank Transaction Classifier",
        goal="Classify each transaction into exactly one category and return valid JSON.",
        backstory=(
            "You are a strict classification engine for New Zealand bank transactions. "
            "You do not calculate totals. "
            "You do not give advice. "
            "You do not guess from the category list order. "
            "You classify based on the merchant, payee, reference, details, amount direction, and NZ context. "
            "Your output must be valid JSON only."        ),
        llm=MY_LLM,
        allow_delegation=False,
        verbose=True,
    )


def get_coach_agent():
    return Agent(
        role="Financial Coach",
        goal="Give practical, warm financial insights.",
        backstory=(
           "You are a helpful friendly and very experience NZ financial coach accessing a NZ person spending and provide feedback. "
            "You explain spending patterns clearly and give practical suggestions."
            "Write the summary in a warm, encouraging, and realistic tone. "
            "Start with greeting the person and acknowledging their efforts. "
            "Format the text as plain readable sentences without markdown, special characters, or formatting."
            "Provide 2 insights based on the transactions, categorisation, and net position."
            "Provide up to 3 actionable tips using details related to the spending to improve financial health."
            "Use the NZ context and categories to give other relevant insights and tips. "
            "Do not give generic advice, only specific insights and tips based on the transactions and categories."
            "Use your knowledge of New Zealand costs, prices, and financial products to give relevant insights and tips."
        ),
        llm=MY_LLM,
        allow_delegation=False,
        verbose=True,
    )