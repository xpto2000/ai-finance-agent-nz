from crewai import Agent
from dotenv import load_dotenv

load_dotenv()

MY_LLM = "groq/llama-3.3-70b-versatile"


def get_analyst_agent():
    return Agent(
        role="New Zealand Bank Transaction Classifier",
        goal=(
            "Classify each transaction into exactly one allowed New Zealand personal finance category. "
            "Return only valid JSON."
        ),
        backstory=(
            "You are a strict classification engine for New Zealand bank transactions. "
            "You do not calculate totals. "
            "You do not give advice. "
            "You do not guess from the category list order. "
            "You classify based on the merchant, payee, reference, details, amount direction, and NZ context. "
            "Your output must be valid JSON only."
        ),
        llm=MY_LLM,
        allow_delegation=False,
        verbose=True,
    )


def get_coach_agent():
    return Agent(
        role="Financial Coach",
        goal="Give practical, concise spending insights based on categorized transaction data.",
        backstory=(
            "You are a helpful financial coach. "
            "You explain spending patterns clearly and give practical suggestions."
        ),
        llm=MY_LLM,
        allow_delegation=False,
        verbose=True,
    )