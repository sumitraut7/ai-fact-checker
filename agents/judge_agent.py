from tools.local_llm import local_llm_chain_ask
from tools.scrape_url import extract_percentage

JUDGE_PROMPT_TEMPLATE = """
You are a reliable fact-checking AI.

You will receive:
- A claim to evaluate.
- A summary of a source article.

Your task is to analyze the article summary and determine if it:
1. **Supports** the claim
2. **Refutes** the claim
3. Is **Neutral** or **Inconclusive**

Then explain your reasoning and provide a confidence score from 0 to 100 (without the % symbol).

Respond **exactly** in this format:
---
Verdict: [Supports / Refutes / Neutral]
Confidence: [0-100]
Reason: [short explanation]
---

Claim: "{claim}"
Article Summary: "{summary}"
"""

def judge_claim_against_summary(claim: str, summary: str) -> dict:
    """Runs the judgment LLM and parses its response into a dict."""
    raw_output = local_llm_chain_ask(
        prompt_text="",
        template=JUDGE_PROMPT_TEMPLATE.format(claim=claim, summary=summary)
    )

    try:
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        verdict_line = next(line for line in lines if line.startswith("Verdict:"))
        confidence_line = next(line for line in lines if line.startswith("Confidence:"))
        reason_line = next(line for line in lines if line.startswith("Reason:"))

        return {
            "verdict": verdict_line.split(":", 1)[1].strip(),
            "confidence": extract_percentage(confidence_line.split(":", 1)[1].strip()),
            "reason": reason_line.split(":", 1)[1].strip(),
            "raw": raw_output
        }
    except Exception as e:
        return {
            "verdict": "Neutral",
            "confidence": 0,
            "reason": f"Failed to parse judgment: {str(e)}",
            "raw": raw_output
        }