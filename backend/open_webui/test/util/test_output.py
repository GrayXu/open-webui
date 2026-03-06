import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "utils" / "output.py"
SPEC = importlib.util.spec_from_file_location("open_webui_output_utils", MODULE_PATH)
OUTPUT_UTILS = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
SPEC.loader.exec_module(OUTPUT_UTILS)

serialize_output = OUTPUT_UTILS.serialize_output


def test_serialize_output_moves_interleaved_reasoning_to_the_top():
    output = [
        {
            "type": "reasoning",
            "status": "completed",
            "duration": 2,
            "content": [{"type": "output_text", "text": "First thought"}],
        },
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "First answer"}],
        },
        {
            "type": "reasoning",
            "status": "completed",
            "duration": 3,
            "content": [{"type": "output_text", "text": "Second thought"}],
        },
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "Second answer"}],
        },
    ]

    rendered = serialize_output(output)

    assert rendered.count('type="reasoning"') == 1
    assert 'duration="5"' in rendered
    assert rendered.index("First thought") < rendered.index("First answer")
    assert rendered.index("Second thought") < rendered.index("First answer")
    assert rendered.index("First answer") < rendered.index("Second answer")


def test_serialize_output_keeps_late_reasoning_in_the_top_block_while_streaming():
    output = [
        {
            "type": "message",
            "content": [{"type": "output_text", "text": "Visible answer"}],
        },
        {
            "type": "reasoning",
            "status": "in_progress",
            "attributes": {"type": "reasoning_content"},
            "content": [{"type": "output_text", "text": "Late thought"}],
        },
    ]

    rendered = serialize_output(output)

    assert rendered.count('type="reasoning"') == 1
    assert 'done="false"' in rendered
    assert rendered.index("Late thought") < rendered.index("Visible answer")
