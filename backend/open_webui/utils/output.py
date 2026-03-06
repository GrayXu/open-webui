from __future__ import annotations

import html
import json

_OPENAI_TOOL_DISPLAY_NAMES = {
    "web_search_call": "Web Search",
    "file_search_call": "File Search",
    "computer_call": "Computer Use",
}


def split_content_and_whitespace(content: str) -> tuple[str, str]:
    content_stripped = content.rstrip()
    original_whitespace = (
        content[len(content_stripped) :] if len(content) > len(content_stripped) else ""
    )
    return content_stripped, original_whitespace


def is_opening_code_block(content: str) -> bool:
    backtick_segments = content.split("```")
    # Even number of segments means the last backticks are opening a new block
    return len(backtick_segments) > 1 and len(backtick_segments) % 2 == 0


def _extract_text(parts: list[dict]) -> str:
    text = ""
    for part in parts:
        if "text" in part:
            value = part.get("text", "")
            text += str(value) if not isinstance(value, str) else value
    return text


def _collect_reasoning_render_state(output: list) -> dict:
    reasoning_segments = []
    total_duration = 0
    has_duration = False
    in_progress = False
    has_reasoning = False

    total_items = len(output)
    for idx, item in enumerate(output):
        if item.get("type") != "reasoning":
            continue

        has_reasoning = True
        source_list = item.get("summary", []) or item.get("content", [])
        reasoning_text = _extract_text(source_list).strip()
        if reasoning_text:
            reasoning_segments.append(reasoning_text)

        duration = item.get("duration")
        if isinstance(duration, (int, float)):
            total_duration += int(duration)
            has_duration = True

        is_last_item = idx == total_items - 1
        is_completed = (
            item.get("status") == "completed" or duration is not None or not is_last_item
        )
        if not is_completed:
            in_progress = True

    return {
        "has_reasoning": has_reasoning,
        "text": "\n".join(reasoning_segments).strip(),
        "duration": total_duration,
        "has_duration": has_duration,
        "in_progress": in_progress,
    }


def _render_reasoning_block(output: list) -> str:
    reasoning_state = _collect_reasoning_render_state(output)
    if not reasoning_state["has_reasoning"]:
        return ""

    display = html.escape(
        "\n".join(
            (f"> {line}" if not line.startswith(">") else line)
            for line in reasoning_state["text"].splitlines()
        )
    )

    body = f"{display}\n" if display else ""
    if reasoning_state["in_progress"]:
        return (
            '<details type="reasoning" done="false">\n'
            "<summary>Thinking…</summary>\n"
            f"{body}</details>\n"
        )

    duration = reasoning_state["duration"] if reasoning_state["has_duration"] else 0
    return (
        f'<details type="reasoning" done="true" duration="{duration}">\n'
        f"<summary>Thought for {duration} seconds</summary>\n"
        f"{body}</details>\n"
    )


def _render_openai_tool_call_handler(item: dict, done: bool) -> str:
    item_type = item.get("type", "")
    call_id = item.get("id", "")
    display_name = _OPENAI_TOOL_DISPLAY_NAMES.get(item_type, item_type)

    summary = ""
    if item_type == "web_search_call":
        action = item.get("action", {})
        if isinstance(action, dict):
            action_type = action.get("type", "")
            if action_type == "search":
                queries = action.get("queries") or []
                query = action.get("query", "")
                summary = (
                    f'Search: {", ".join(str(q) for q in queries)}'
                    if queries
                    else (f"Search: {query}" if query else "")
                )
            elif action_type == "open_page" and action.get("url"):
                summary = f'Open page: {action.get("url", "")}'
            elif action_type == "find_in_page" and action.get("pattern"):
                summary = f'Find in page: {action.get("pattern", "")}'
    elif item_type == "file_search_call":
        queries = item.get("queries", [])
        if queries:
            summary = f'Queries: {", ".join(str(q) for q in queries)}'
    elif item_type == "computer_call":
        action = item.get("action")
        actions = item.get("actions")
        if isinstance(action, dict):
            summary = f'Action: {action.get("type", "unknown")}'
        elif isinstance(actions, list) and actions:
            summary = (
                "Actions: "
                + ", ".join(
                    action_item.get("type", "?")
                    for action_item in actions
                    if isinstance(action_item, dict)
                )
            )

    escaped_name = html.escape(display_name)
    if done:
        return (
            f'<details type="tool_calls" done="true" id="{call_id}" '
            f'name="{escaped_name}" arguments="">\n'
            "<summary>Tool Executed</summary>\n"
            f"{html.escape(summary)}\n"
            "</details>\n"
        )

    return (
        f'<details type="tool_calls" done="false" id="{call_id}" '
        f'name="{escaped_name}" arguments="">\n'
        "<summary>Executing...</summary>\n"
        "</details>\n"
    )


def serialize_output(output: list) -> str:
    """
    Convert OR-aligned output items to HTML for display.
    For LLM consumption, use convert_output_to_messages() instead.
    """
    content = _render_reasoning_block(output)

    # First pass: collect function_call_output items by call_id for lookup
    tool_outputs = {}
    for item in output:
        if item.get("type") == "function_call_output":
            tool_outputs[item.get("call_id")] = item

    # Second pass: render non-reasoning items in order
    for idx, item in enumerate(output):
        item_type = item.get("type", "")

        if item_type == "reasoning":
            continue

        if item_type == "message":
            for content_part in item.get("content", []):
                if "text" in content_part:
                    text = content_part.get("text", "").strip()
                    if text:
                        content = f"{content}{text}\n"

        elif item_type == "function_call":
            # Render tool call inline with its result (if available)
            if content and not content.endswith("\n"):
                content += "\n"

            call_id = item.get("call_id", "")
            name = item.get("name", "")
            arguments = item.get("arguments", "")

            result_item = tool_outputs.get(call_id)
            if result_item:
                result_text = ""
                for result_output in result_item.get("output", []):
                    if "text" in result_output:
                        output_text = result_output.get("text", "")
                        result_text += (
                            str(output_text)
                            if not isinstance(output_text, str)
                            else output_text
                        )
                files = result_item.get("files")
                embeds = result_item.get("embeds", "")

                content += f'<details type="tool_calls" done="true" id="{call_id}" name="{name}" arguments="{html.escape(json.dumps(arguments))}" result="{html.escape(json.dumps(result_text, ensure_ascii=False))}" files="{html.escape(json.dumps(files)) if files else ""}" embeds="{html.escape(json.dumps(embeds))}">\n<summary>Tool Executed</summary>\n</details>\n'
            else:
                content += f'<details type="tool_calls" done="false" id="{call_id}" name="{name}" arguments="{html.escape(json.dumps(arguments))}">\n<summary>Executing...</summary>\n</details>\n'

        elif item_type == "function_call_output":
            # Already handled inline with function_call above
            pass

        elif item_type in _OPENAI_TOOL_DISPLAY_NAMES:
            status = item.get("status", "in_progress")
            done = status in ("completed", "failed", "incomplete") or idx != len(output) - 1
            content += _render_openai_tool_call_handler(item, done)

        elif item_type == "open_webui:code_interpreter":
            content_stripped, original_whitespace = split_content_and_whitespace(
                content
            )
            if is_opening_code_block(content_stripped):
                content = content_stripped.rstrip("`").rstrip() + original_whitespace
            else:
                content = content_stripped + original_whitespace

            if content and not content.endswith("\n"):
                content += "\n"

            # Render the code_interpreter item as a <details> block
            # so the frontend Collapsible renders "Analyzing..."/"Analyzed".
            code = item.get("code", "").strip()
            lang = item.get("lang", "python")
            status = item.get("status", "in_progress")
            duration = item.get("duration")
            is_last_item = idx == len(output) - 1

            # Build inner content: code block
            display = ""
            if code:
                display = f"```{lang}\n{code}\n```"

            # Build output attribute as HTML-escaped JSON for CodeBlock.svelte
            ci_output = item.get("output")
            output_attr = ""
            if ci_output:
                if isinstance(ci_output, dict):
                    output_json = json.dumps(ci_output, ensure_ascii=False)
                else:
                    output_json = json.dumps(
                        {"result": str(ci_output)}, ensure_ascii=False
                    )
                output_attr = f' output="{html.escape(output_json)}"'

            if status == "completed" or duration is not None or not is_last_item:
                content += f'<details type="code_interpreter" done="true" duration="{duration or 0}"{output_attr}>\n<summary>Analyzed</summary>\n{display}\n</details>\n'
            else:
                content += f'<details type="code_interpreter" done="false"{output_attr}>\n<summary>Analyzing…</summary>\n{display}\n</details>\n'

    return content.strip()
