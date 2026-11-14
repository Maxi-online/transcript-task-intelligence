import json
import re
import difflib
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.infrastructure.api.v1.dependencies import (
    get_summarizer_agents,
    get_llm_monitoring,
)
from src.infrastructure.providers import OpenAIProvider  # NEW: GPT provider
from src.core.agents.summarization import SummarizationAgent, SummarizationDTO


PROJECT_ROOT = Path(__file__).resolve().parent
VAL_PATH = PROJECT_ROOT / "val.json"

# -----------------------
# Helpers
# -----------------------

def extract_tasks(prompt: str) -> List[str]:
    """Parsing the numbered list of tasks in prompt.

    If there are no numbered items, return the entire prompt as one task.
    """
    # Delete the text from Windows and the blanks at the beginning of the lines
    prompt_clean = re.sub(r"\r", "", prompt)
    # We're looking for a line of species "1. <text>" / "2. <text>", etc.
    tasks = re.findall(r"^\s*\d+\.\s*(.+)$", prompt_clean, flags=re.MULTILINE)
    if tasks:
        return [t.strip() for t in tasks]
    return [prompt.strip()]


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def check_list(expected_list: List[Any], generated: str) -> Tuple[bool, List[str]]:  # edited signature to Any
    """Check that all elements of the list are present in the response.

    expected_list may contain either rows or dictionaries with a "name" key".
    """
    missing: List[str] = []
    gen_norm = normalise(generated)
    for item in expected_list:
        # Support for both rows and dictionaries of species {"name": ..., "stock_status"": ...}
        if isinstance(item, dict):
            expected_item = str(item.get("name", "")).strip()
        else:
            expected_item = str(item).strip()

        if normalise(expected_item) not in gen_norm:
            missing.append(expected_item)
    return len(missing) == 0, missing


def check_stock_status(expected_status: str, generated: str) -> bool:
    return normalise(expected_status) in normalise(generated)


def check_summary(expected_summary: str, generated: str) -> bool:
    matcher = difflib.SequenceMatcher(None, normalise(expected_summary), normalise(generated))
    return matcher.ratio() >= 0.7  # allowed ~30 per cent divergence of wording


def build_expected_answer(expected: Dict[str, Any]) -> str:  # NEW helper
    'Collects a man-readable benchmarking response.'
    parts: List[str] = []
    if "list_of_items" in expected:
        # Listed elements for the line "<name> — <stock_status>" or simply name
        items_str = []
        for el in expected["list_of_items"]:
            if isinstance(el, dict):
                items_str.append(f"{el.get('name', '')} — {el.get('stock_status', '')}")
            else:
                items_str.append(str(el))
        parts.append('List of items: ' + ", ".join(items_str))
    elif "items" in expected:
        parts.append("Items: " + ", ".join(expected["items"]))

    if "stock_status" in expected:
        parts.append(f"Availability status: {expected['stock_status']}")

    if "summary" in expected:
        parts.append(f"Sammari: {expected['summary']}")

    # If nothing fits, we're gonna do it like JSON.
    if not parts:
        parts.append(json.dumps(expected, ensure_ascii=False))

    return "\n".join(parts)


def gpt_evaluate(prompt_text: str, expected: str, generated: str, provider: OpenAIProvider) -> Dict[str, Any]:
    """Assesss the quality of the response using the GPT model.
    Returns the Vocabulary of the View
    {
        "score": float (0-100),
        "explanation": str,            # Main reasons for this assessment
        "recommendations": str         # How to Improve Response/agent
    }
    """
    eval_prompt = (
        "You're an expert who evaluates how the assistant's response matches the benchmark. "
        'First, make an estimate (0–100), where 100 is a complete match). '
        'Then list up to 5 SPECIAL reasons (refer to missing goods, incorrect status, non-compliance with instructions, etc.), why this assessment is given. '
        'Consider the extent to which the assistant followed the prompt task. '
        'Return STRICT JSON without explanation outside JSON, example:\n'
        "{\\\"score\\\": 85, \\\"explanation\\\": \\\"...\\\"}\n\n"
        f"User Prompt (tasks): \n{prompt_text}\n\n"
        f"Reference reply: \n{expected}\n\n"
        f"Assistant response:\n{generated}"
    )

    try:
        raw_response = provider.generate(eval_prompt)
        # Select JSON, looking for code block ```json … `'' or figure brackets
        code_match = re.search(r"```json\s*(\{[\s\S]+?\})\s*```", raw_response)
        if code_match:
            json_segment = code_match.group(1)
        else:
            start = raw_response.find('{')
            end = raw_response.rfind('}')
            json_segment = raw_response[start:end+1] if start != -1 and end != -1 else raw_response.strip()

        data = json.loads(json_segment)
    except Exception:
        # fallback: Find the first number and use the whole answer as an expansion
        try:
            first_num = re.search(r"\d{1,3}(?:\.\d+)?", raw_response)
            score_fallback = float(first_num.group(0)) if first_num else -1.0
            return {"score": score_fallback, "explanation": raw_response}
        except Exception:
            return {"score": -1.0, "explanation": ""}

    # post-processing JSON
    score_val = float(data.get("score", -1))
    result = {
        "score": max(0.0, min(100.0, score_val)),
        "explanation": data.get("explanation", "")
    }
    return result


def overall_review(results: List[Dict[str, Any]], provider: OpenAIProvider) -> str:
    'Formulates final report and recommendations for improvement based on all results.'
    if not results:
        return 'No data for the final evaluation.'

    lines = []
    for r in results:
        lines.append(f"ID: {r['id']} | score: {r['gpt_score']} | comment: {r['gpt_explanation']}")
    joined = "\n".join(lines)

    prompt = (
        "You're an experienced auditor of LLM. Based on individual assessments below, form: "
        '(1) short general agreement on the quality of responses, (2) key weaknesses, (3) recommendations on how to improve the agent. '
        'Set the answer in the form of a list of paragraphs.\n\n'
        f"Individual estimates: \n{joined}"
    )
    try:
        return provider.generate(prompt)
    except Exception:
        return 'It was not possible to obtain a final recommendation from GPT.'


def validate_item(
    item: Dict[str, Any],
    agent: SummarizationAgent,
    evaluator: OpenAIProvider,
    llm_monitoring
) -> Dict[str, Any]:
    'Runs an agent on one example and returns the validation result.'
    # Production of input data
    prompt: str = item["prompt"]
    dialog_key = "dialog" if "dialog" in item["input"] else "dialog_excerpt"
    text: str = item["input"][dialog_key]
    tasks = extract_tasks(prompt)

    # Create a trade for the entire validation of this item (regardless of the track inside the SummaryAgent))
    trace = llm_monitoring.trace(
        name="validation-item",
        user_id="validation_user",
        input={
            "item_id": item["id"],
            "prompt": prompt,
            "tasks": tasks,
        },
    )

    dto = SummarizationDTO(user_id="validation_user", text=text, tasks=tasks)
    generated_answer = agent.execute(dto)

    # Comparison with the Master Standard
    expected = item["expected_output"]
    expected_readable = build_expected_answer(expected)  # NEW
    ok = True
    details: Dict[str, Any] = {}

    # 1. List of goods / items
    if "list_of_items" in expected:
        passed, missing = check_list(expected["list_of_items"], generated_answer)
        ok &= passed
        if not passed:
            details["missing_items"] = missing
    elif "items" in expected:
        passed, missing = check_list(expected["items"], generated_answer)
        ok &= passed
        if not passed:
            details["missing_items"] = missing

    # 2. Status of availability of goods
    if "stock_status" in expected:
        passed = check_stock_status(expected["stock_status"], generated_answer)
        ok &= passed
        if not passed:
            details["stock_status_mismatch"] = expected["stock_status"]

    # 3. Sammari (for pharmacy_summary))
    if "summary" in expected:
        passed = check_summary(expected["summary"], generated_answer)
        ok &= passed
        if not passed:
            details["summary_low_similarity"] = True

    # NEW: GPT evaluation
    gpt_score_data = gpt_evaluate(prompt, expected_readable, generated_answer, evaluator)

    # NEW: Consider the test passed only if GPT delivered 100 out of 100
    ok = gpt_score_data["score"] >= 100.0

    # Save GPT explanation.
    details["gpt_explanation"] = gpt_score_data.get("explanation", "")
    
    # Write down the Langfuse estimate (from 0 to 1)
    if gpt_score_data["score"] >= 0:
        llm_monitoring.score(
            trace_id=trace.id,
            name="gpt_quality",
            value=round(gpt_score_data["score"] / 100, 4),
            comment="LLM-as-a-judge",
        )

    # Update track output
    llm_monitoring.update_trace(
        trace,
        output={
            "generated": generated_answer,
            "expected": expected_readable,
            "gpt_score": gpt_score_data["score"],
            "gpt_explanation": gpt_score_data.get("explanation", ""),
            # recommendations removed
            "passed": ok,
            "details": details,
        },
    )

    return {
        "id": item["id"],
        "passed": ok,
        "generated": generated_answer,
        "expected": expected_readable,
        "gpt_score": gpt_score_data["score"],
        "gpt_explanation": gpt_score_data.get("explanation", ""),
        # recommendations removed
        "details": details,
    }


# -----------------------
# Entry point
# -----------------------

def main(val_file: Path = VAL_PATH):
    with open(val_file, "r", encoding="utf-8") as f:
        val_json = json.load(f)

    summarizers = get_summarizer_agents()
    llm_monitoring = get_llm_monitoring()
    agent = SummarizationAgent(llm_monitoring, summarizers)

    # NEW: Quality assessment provider
    evaluator_system_message = "You're an expert response rater."
    gpt_evaluator = OpenAIProvider(evaluator_system_message)

    # NEW: Supplier for final evaluation
    overall_system_message = "You're an expert responder."
    overall_reviewer = OpenAIProvider(overall_system_message)

    results: List[Dict[str, Any]] = []
    for item in val_json.get("items", []):
        result = validate_item(item, agent, gpt_evaluator, llm_monitoring)  # UPDATED call
        results.append(result)
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['id']} — GPT score: {result['gpt_score']}")  # UPDATED output
        print('   Reference:', result["expected"])
        print("   Boat's answer is:", result["generated"])
        print('   Description:', result["gpt_explanation"])
        # recommendations removed
        if not result["passed"]:
            print("   Details:", result["details"])

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print("\n====================")
    print(f"Total: {passed}/{total} Test passed successfully")

    # NEW: Take out the test rate and GPT average
    percent_passed = round((passed / total) * 100, 2) if total else 0.0
    valid_scores = [r["gpt_score"] for r in results if r["gpt_score"] >= 0]
    avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

    print(f"Percentage of pass: {percent_passed}%")
    print(f"Medium GPT ball: {avg_score}/100")

    # Outcome review and recommendations from GPT (one challenge)
    final_report = overall_review(results, overall_reviewer)
    print('\n== sync, corrected by elderman == @elder_man')
    print(final_report)

    # Send all stored observations to Langfuse
    try:
        llm_monitoring.flush()
    except Exception as e:
        print('Could not unload the data to Langfuse:', e)


if __name__ == "__main__":
    main() 