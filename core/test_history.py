import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from core.history import SanitizingHistoryConverter


def _make_tool_call(name: str, call_id: str = "call_1", args: dict | None = None) -> dict:
    return {"name": name, "id": call_id, "args": args or {}}


LONG_NAME = "x" * 201
SHORT_NAME = "band_send_message"


class TestSanitizingHistoryConverterPassthrough:
    def test_clean_history_passes_through(self):
        converter = SanitizingHistoryConverter("test-agent")
        messages = [
            HumanMessage(content="[user]: Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="[user]: What is GDPR?"),
            AIMessage(
                content="",
                tool_calls=[_make_tool_call(SHORT_NAME, "call_1")],
            ),
            ToolMessage(content="result", tool_call_id="call_1"),
            AIMessage(content="GDPR is a regulation."),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 6
        assert result[1].content == "Hi there"
        assert result[3].tool_calls[0]["name"] == SHORT_NAME
        assert result[4].tool_call_id == "call_1"

    def test_empty_history(self):
        converter = SanitizingHistoryConverter()
        assert converter.convert([]) == []
        assert converter._sanitize([]) == []


class TestSanitizingHistoryConverterStripsOversized:
    def test_strips_oversized_tool_call_name(self):
        converter = SanitizingHistoryConverter("test-agent")
        messages = [
            HumanMessage(content="[user]: Hello"),
            AIMessage(
                content="",
                tool_calls=[_make_tool_call(LONG_NAME, "call_bad")],
            ),
            ToolMessage(content="result", tool_call_id="call_bad"),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)

    def test_strips_multiple_oversized_calls(self):
        converter = SanitizingHistoryConverter()
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    _make_tool_call(LONG_NAME, "call_1"),
                    _make_tool_call("a" * 300, "call_2"),
                ],
            ),
            ToolMessage(content="r1", tool_call_id="call_1"),
            ToolMessage(content="r2", tool_call_id="call_2"),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 0

    def test_mixed_good_and_bad_tool_calls(self):
        converter = SanitizingHistoryConverter()
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    _make_tool_call(SHORT_NAME, "call_good"),
                    _make_tool_call(LONG_NAME, "call_bad"),
                ],
            ),
            ToolMessage(content="good result", tool_call_id="call_good"),
            ToolMessage(content="bad result", tool_call_id="call_bad"),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 2
        assert isinstance(result[0], AIMessage)
        assert len(result[0].tool_calls) == 1
        assert result[0].tool_calls[0]["name"] == SHORT_NAME
        assert isinstance(result[1], ToolMessage)
        assert result[1].tool_call_id == "call_good"

    def test_preserves_content_when_stripping_tool_calls(self):
        converter = SanitizingHistoryConverter()
        messages = [
            AIMessage(
                content="I used a tool",
                tool_calls=[_make_tool_call(LONG_NAME, "call_bad")],
            ),
            ToolMessage(content="result", tool_call_id="call_bad"),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "I used a tool"
        assert result[0].tool_calls == []

    def test_exactly_200_chars_is_allowed(self):
        converter = SanitizingHistoryConverter()
        name_200 = "x" * 200
        messages = [
            AIMessage(
                content="",
                tool_calls=[_make_tool_call(name_200, "call_ok")],
            ),
            ToolMessage(content="result", tool_call_id="call_ok"),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 2
        assert result[0].tool_calls[0]["name"] == name_200

    def test_exactly_201_chars_is_stripped(self):
        converter = SanitizingHistoryConverter()
        name_201 = "x" * 201
        messages = [
            AIMessage(
                content="",
                tool_calls=[_make_tool_call(name_201, "call_bad")],
            ),
            ToolMessage(content="result", tool_call_id="call_bad"),
        ]
        result = converter._sanitize(messages)
        assert len(result) == 0


class TestSanitizingHistoryConverterConvert:
    def test_convert_delegates_to_parent(self):
        converter = SanitizingHistoryConverter("test-agent")
        raw = [
            {
                "message_type": "text",
                "role": "user",
                "sender_name": "alice",
                "content": "Hello",
            }
        ]
        result = converter.convert(raw)
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert "alice" in result[0].content

    def test_convert_and_sanitize_combined(self):
        converter = SanitizingHistoryConverter("test-agent")
        raw_tool_call = (
            '{"name": "' + LONG_NAME + '", "args": {"content": "test"}, "tool_call_id": "bad_id"}'
        )
        raw_tool_result = (
            '{"name": "' + LONG_NAME + '", "output": "done", "tool_call_id": "bad_id"}'
        )
        raw = [
            {
                "message_type": "text",
                "role": "user",
                "sender_name": "bob",
                "content": "Parse this",
            },
            {
                "message_type": "tool_call",
                "content": raw_tool_call,
                "role": "assistant",
                "sender_name": "other-agent",
            },
            {
                "message_type": "tool_result",
                "content": raw_tool_result,
                "role": "assistant",
                "sender_name": "other-agent",
            },
        ]
        result = converter.convert(raw)
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
