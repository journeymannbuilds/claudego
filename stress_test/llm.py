import os
import re
from pathlib import Path
import anthropic

MODEL = "claude-sonnet-4-5-20250929"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"


def _get_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text()


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from a response."""
    text = text.strip()
    match = re.match(r"^```(?:sql)?\s*\n?(.*?)```$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def generate_sql(question: str) -> str:
    """Call Claude to generate a SQL query from a natural language question."""
    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_get_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ],
    )
    raw = response.content[0].text
    return _strip_code_fences(raw)


def assess_gap(question: str, sql: str, row_count: int, success: bool) -> str:
    """Call Claude to assess whether the question exposed a data model gap."""
    client = _get_client()
    user_message = (
        f"The user asked: {question}\n\n"
        f"The SQL I generated: {sql}\n\n"
        f"Result: {row_count} rows returned, success={success}\n\n"
        "In one line, flag whether this question exposed a gap in the data model "
        "— a missing table, missing column, ambiguous join, or a concept the model "
        "can't express. If no gap, say 'NO_GAP'. If there is a gap, start with "
        "'GAP:' followed by a one-line description."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=_get_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": user_message,
            }
        ],
    )
    return response.content[0].text.strip()
