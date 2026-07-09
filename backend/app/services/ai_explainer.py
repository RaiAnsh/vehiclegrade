"""Optional LLM layer that turns an already-computed report into a
buyer-friendly plain-English narrative.

This is an enhancement only - it is never the source of any number in the
report. It is hard-instructed to reuse the figures it's handed and never
invent its own price/cost figures, and it fails silently (returns None) if
no LLM is configured or anything goes wrong, so the rest of the report is
never affected by this being on or off.
"""

from pydantic import BaseModel, Field

from app.services.llm_client import get_llm

SYSTEM_PROMPT = """You are a plain-English explainer for a used-vehicle analysis report.

You will be given a JSON summary of numbers and facts that have ALREADY been
computed deterministically (score, market value, suggested offer, known
issues, repair-cost estimates, verdict, etc.) plus the raw listing description
text if one was provided.

Your ONLY job is to write a short, friendly narrative that helps a buyer
understand what these numbers mean in practice, and 2-4 short additional
notes worth highlighting.

Strict rules:
- Never state a dollar amount, percentage, score, or any other number that
  is not already present in the JSON you were given. If you want to reference
  a number, copy it exactly from the input.
- Never invent facts about the vehicle that aren't in the input.
- Do not repeat the verdict paragraph verbatim - add color and context instead.
- Keep the narrative to 3-5 sentences.
"""


class Explanation(BaseModel):
    narrative: str = Field(description="A short, plain-English narrative explaining the report to a buyer.")
    additional_notes: list[str] = Field(description="2-4 short, additional notes worth highlighting.")


def generate_explanation(report_summary, description_text):
    """Returns an Explanation-shaped dict, or None if no LLM is configured
    or generation fails for any reason."""
    llm = get_llm()
    if llm is None:
        return None

    try:
        structured_llm = llm.with_structured_output(Explanation)
        result = structured_llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Report summary (JSON):\n{report_summary}\n\n"
                    f"Original listing description text:\n{description_text or '(none provided)'}"
                ),
            },
        ])
        return result.model_dump()
    except Exception:
        return None
