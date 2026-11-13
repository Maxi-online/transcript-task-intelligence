import json
import re
import difflib
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.infrastructure.api.v1.dependencies import (
    get_summarizer_agents,
    get_llm_monitoring,
)
from src.infrastructure.providers import OpenAIProvider  # NEW: провайдер для GPT-оценки
from src.core.agents.summarization import SummarizationAgent, SummarizationDTO


PROJECT_ROOT = Path(__file__).resolve().parent
VAL_PATH = PROJECT_ROOT / "val.json"

# -----------------------
# Helpers
# -----------------------

def extract_tasks(prompt: str) -> List[str]:
    """Парсинг нумерованного списка задач в prompt.

    Если нумерованных пунктов нет, возвращаем весь prompt как одну задачу.
    """
    # Удаляем перевод строки с Windows и пробелы в начале строк
    prompt_clean = re.sub(r"\r", "", prompt)
    # Ищем строки вида "1. <текст>" / "2. <текст>" и т. д.
    tasks = re.findall(r"^\s*\d+\.\s*(.+)$", prompt_clean, flags=re.MULTILINE)
    if tasks:
        return [t.strip() for t in tasks]
    return [prompt.strip()]


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def check_list(expected_list: List[Any], generated: str) -> Tuple[bool, List[str]]:  # edited signature to Any
    """Проверяем, что все элементы списка присутствуют в ответе.

    expected_list может содержать либо строки, либо словари с ключом "name".
    """
    missing: List[str] = []
    gen_norm = normalise(generated)
    for item in expected_list:
        # Поддержка как строк, так и словарей вида {"name": ..., "stock_status": ...}
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
    return matcher.ratio() >= 0.7  # допускаем ~30% расхождения формулировок


def build_expected_answer(expected: Dict[str, Any]) -> str:  # NEW helper
    """Собирает человекочитаемое представление эталонного ответа."""
    parts: List[str] = []
    if "list_of_items" in expected:
        # Приводим элементы к строке "<name> — <stock_status>" или просто имя
        items_str = []
        for el in expected["list_of_items"]:
            if isinstance(el, dict):
                items_str.append(f"{el.get('name', '')} — {el.get('stock_status', '')}")
            else:
                items_str.append(str(el))
        parts.append("Список товаров: " + ", ".join(items_str))
    elif "items" in expected:
        parts.append("Items: " + ", ".join(expected["items"]))

    if "stock_status" in expected:
        parts.append(f"Статус наличия: {expected['stock_status']}")

    if "summary" in expected:
        parts.append(f"Саммари: {expected['summary']}")

    # Если ничего не подошло — сериализуем как JSON
    if not parts:
        parts.append(json.dumps(expected, ensure_ascii=False))

    return "\n".join(parts)


def gpt_evaluate(prompt_text: str, expected: str, generated: str, provider: OpenAIProvider) -> Dict[str, Any]:
    """Оценивает качество ответа с помощью GPT-модели.
    Возвращает словарь вида
    {
        "score": float (0-100),
        "explanation": str,            # основные причины такой оценки
        "recommendations": str         # как улучшить ответ/агента
    }
    """
    eval_prompt = (
        "Ты — эксперт, который оценивает, насколько ответ ассистента соответствует эталону. "
        "Сначала выставь оценку (0–100, где 100 — полное совпадение). "
        "Затем перечисли до 5 КОНКРЕТНЫХ причин (ссылайся на отсутствующие товары, неверные статусы, несоблюдение инструкций и т.д.), почему поставлена именно эта оценка. "
        "Учитывай, насколько ассистент следовал задачам из промпта. "
        "Верни STRICT JSON без пояснений вне JSON, пример:\n"
        "{\\\"score\\\": 85, \\\"explanation\\\": \\\"...\\\"}\n\n"
        f"Промпт пользователя (задачи):\n{prompt_text}\n\n"
        f"Эталонный ответ:\n{expected}\n\n"
        f"Ответ ассистента:\n{generated}"
    )

    try:
        raw_response = provider.generate(eval_prompt)
        # Выделяем JSON — ищем блок кода ```json … ``` или фигурные скобки
        code_match = re.search(r"```json\s*(\{[\s\S]+?\})\s*```", raw_response)
        if code_match:
            json_segment = code_match.group(1)
        else:
            start = raw_response.find('{')
            end = raw_response.rfind('}')
            json_segment = raw_response[start:end+1] if start != -1 and end != -1 else raw_response.strip()

        data = json.loads(json_segment)
    except Exception:
        # fallback: найти первое число и использовать весь ответ как explanation
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
    """Формирует итоговый отчёт и рекомендации по улучшению на основе всех результатов."""
    if not results:
        return "Нет данных для итоговой оценки."

    lines = []
    for r in results:
        lines.append(f"ID: {r['id']} | score: {r['gpt_score']} | comment: {r['gpt_explanation']}")
    joined = "\n".join(lines)

    prompt = (
        "Ты — опытный аудитор LLM. На основе приведённых ниже индивидуальных оценок сформулируй: "
        "1) краткий общий вердикт качества ответов, 2) ключевые слабые места, 3) рекомендации, как улучшить агента. "
        "Ответ структурируй в виде списка пунктов.\n\n"
        f"Индивидуальные оценки:\n{joined}"
    )
    try:
        return provider.generate(prompt)
    except Exception:
        return "Не удалось получить итоговую рекомендацию от GPT."


def validate_item(
    item: Dict[str, Any],
    agent: SummarizationAgent,
    evaluator: OpenAIProvider,
    llm_monitoring
) -> Dict[str, Any]:
    """Запускает агента на одном примере и возвращает результат валидации."""
    # Подготовка входных данных
    prompt: str = item["prompt"]
    dialog_key = "dialog" if "dialog" in item["input"] else "dialog_excerpt"
    text: str = item["input"][dialog_key]
    tasks = extract_tasks(prompt)

    # Создаем trace для всей валидации данного item (независимо от трэйса внутри SummarizationAgent)
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

    # Сравнение с эталоном
    expected = item["expected_output"]
    expected_readable = build_expected_answer(expected)  # NEW
    ok = True
    details: Dict[str, Any] = {}

    # 1. Список товаров / items
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

    # 2. Статус наличия товара
    if "stock_status" in expected:
        passed = check_stock_status(expected["stock_status"], generated_answer)
        ok &= passed
        if not passed:
            details["stock_status_mismatch"] = expected["stock_status"]

    # 3. Саммари (для pharmacy_summary)
    if "summary" in expected:
        passed = check_summary(expected["summary"], generated_answer)
        ok &= passed
        if not passed:
            details["summary_low_similarity"] = True

    # NEW: GPT-оценка
    gpt_score_data = gpt_evaluate(prompt, expected_readable, generated_answer, evaluator)

    # NEW: считаем тест пройденным, только если GPT поставил 100 из 100
    ok = gpt_score_data["score"] >= 100.0

    # Сохраняем пояснение GPT
    details["gpt_explanation"] = gpt_score_data.get("explanation", "")
    
    # Записываем оценку в Langfuse (от 0 до 1)
    if gpt_score_data["score"] >= 0:
        llm_monitoring.score(
            trace_id=trace.id,
            name="gpt_quality",
            value=round(gpt_score_data["score"] / 100, 4),
            comment="LLM-as-a-judge",
        )

    # Обновляем trace выводом
    llm_monitoring.update_trace(
        trace,
        output={
            "generated": generated_answer,
            "expected": expected_readable,
            "gpt_score": gpt_score_data["score"],
            "gpt_explanation": gpt_score_data.get("explanation", ""),
            # рекомендации убраны
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
        # рекомендации убраны
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

    # NEW: провайдер для оценки качества
    evaluator_system_message = "Ты — эксперт-оценщик ответов."
    gpt_evaluator = OpenAIProvider(evaluator_system_message)

    # NEW: провайдер для итоговой оценки
    overall_system_message = "Ты — эксперт-аудитор ответов."
    overall_reviewer = OpenAIProvider(overall_system_message)

    results: List[Dict[str, Any]] = []
    for item in val_json.get("items", []):
        result = validate_item(item, agent, gpt_evaluator, llm_monitoring)  # UPDATED call
        results.append(result)
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['id']} — GPT score: {result['gpt_score']}")  # UPDATED output
        print("   Эталон:", result["expected"])
        print("   Ответ бота:", result["generated"])
        print("   Пояснение:", result["gpt_explanation"])
        # рекомендации убраны
        if not result["passed"]:
            print("   Details:", result["details"])

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print("\n====================")
    print(f"Итого: {passed}/{total} тестов пройдено успешно")

    # NEW: выводим процент пройденных тестов и среднюю оценку GPT
    percent_passed = round((passed / total) * 100, 2) if total else 0.0
    valid_scores = [r["gpt_score"] for r in results if r["gpt_score"] >= 0]
    avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

    print(f"Процент прохождения: {percent_passed}%")
    print(f"Средний GPT-балл: {avg_score}/100")

    # Итоговый обзор и рекомендации от GPT (один вызов)
    final_report = overall_review(results, overall_reviewer)
    print("\n==== Итоговый отчёт GPT ====")
    print(final_report)

    # Отправляем все накопленные наблюдения в Langfuse
    try:
        llm_monitoring.flush()
    except Exception as e:
        print("Не удалось выгрузить данные в Langfuse:", e)


if __name__ == "__main__":
    main() 