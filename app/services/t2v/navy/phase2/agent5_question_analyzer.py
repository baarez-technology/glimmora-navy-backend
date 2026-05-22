"""
Agent 5 — Question Analyzer (Navy)
Parses user question about LM2500 Gas Turbine into structured intent object.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
from config import LLM_FAST
from json_utils import safe_parse_json

SYSTEM_PROMPT = """You are a naval engineering domain intent parser for the LM2500 Gas Turbine.
Given a user question about LM2500 systems, operations, or maintenance, extract:
- primary_topic: the main system or procedure being asked about
- subtopics: list of sub-components or sub-events involved
- question_type: "sequential_process" | "single_concept" | "comparison" | "troubleshooting"
- estimated_frames: how many animation steps will be needed (4-10)
- search_terms: list of keywords to use for document retrieval

Return JSON only:
{
  "primary_topic": "...",
  "subtopics": ["...", "..."],
  "question_type": "sequential_process",
  "estimated_frames": 6,
  "search_terms": ["...", "..."]
}"""


def analyze(question: str) -> dict:
    import asyncio
    from app.services.ai_service import chat
    resp_text = asyncio.run(chat(
        model=LLM_FAST,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}"}
        ]
    ))
    # clean JSON block if needed
    intent = safe_parse_json(resp_text)
    intent["original_question"] = question
    return intent


if __name__ == "__main__":
    result = analyze("How does the LM2500 compressor section work?")
    print(json.dumps(result, indent=2))
