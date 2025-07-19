import pytest
from unittest.mock import Mock, patch

from open_webui.utils.misc import (
    deep_update,
    get_message_list,
    get_messages_content,
    get_last_user_message_item,
    get_content_from_message,
    get_last_user_message,
    get_last_assistant_message_item,
    get_last_assistant_message,
    get_system_message,
    remove_system_message,
    pop_system_message,
    prepend_to_first_user_message_content,
    add_or_update_system_message,
    add_or_update_user_message,
    append_or_update_assistant_message,
)


class TestMiscUtils:
    """Test suite for miscellaneous utilities"""

    def test_deep_update_simple(self):
        """Test deep update with simple dictionaries"""
        d = {"a": 1, "b": 2}
        u = {"b": 3, "c": 4}
        result = deep_update(d, u)
        
        assert result == {"a": 1, "b": 3, "c": 4}
        assert d == {"a": 1, "b": 3, "c": 4}  # Original dict is modified

    def test_deep_update_nested(self):
        """Test deep update with nested dictionaries"""
        d = {"a": {"x": 1, "y": 2}, "b": 3}
        u = {"a": {"y": 4, "z": 5}, "c": 6}
        result = deep_update(d, u)
        
        expected = {"a": {"x": 1, "y": 4, "z": 5}, "b": 3, "c": 6}
        assert result == expected

    def test_deep_update_empty_dict(self):
        """Test deep update with empty dictionary"""
        d = {}
        u = {"a": 1, "b": 2}
        result = deep_update(d, u)
        
        assert result == {"a": 1, "b": 2}

    def test_get_message_list_simple_chain(self):
        """Test message list reconstruction with simple chain"""
        messages = {
            "msg1": {"id": "msg1", "content": "Hello", "parentId": None},
            "msg2": {"id": "msg2", "content": "Hi", "parentId": "msg1"},
            "msg3": {"id": "msg3", "content": "How are you?", "parentId": "msg2"}
        }
        
        result = get_message_list(messages, "msg3")
        
        assert len(result) == 3
        assert result[0]["id"] == "msg1"
        assert result[1]["id"] == "msg2"
        assert result[2]["id"] == "msg3"

    def test_get_message_list_none_messages(self):
        """Test message list reconstruction with None messages"""
        result = get_message_list(None, "msg1")
        assert result == []

    def test_get_message_list_empty_messages(self):
        """Test message list reconstruction with empty messages"""
        result = get_message_list({}, "msg1")
        assert result == []

    def test_get_message_list_nonexistent_message(self):
        """Test message list reconstruction with nonexistent message ID"""
        messages = {"msg1": {"id": "msg1", "content": "Hello", "parentId": None}}
        result = get_message_list(messages, "nonexistent")
        assert result == []

    def test_get_messages_content(self):
        """Test getting messages content as string"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = get_messages_content(messages)
        expected = "USER: Hello\nASSISTANT: Hi there!\nUSER: How are you?"
        assert result == expected

    def test_get_last_user_message_item(self):
        """Test getting last user message item"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good!"}
        ]
        
        result = get_last_user_message_item(messages)
        assert result["content"] == "How are you?"

    def test_get_last_user_message_item_none(self):
        """Test getting last user message item when none exists"""
        messages = [
            {"role": "assistant", "content": "Hi there!"},
            {"role": "assistant", "content": "I'm good!"}
        ]
        
        result = get_last_user_message_item(messages)
        assert result is None

    def test_get_content_from_message_string(self):
        """Test getting content from message with string content"""
        message = {"content": "Hello world"}
        result = get_content_from_message(message)
        assert result == "Hello world"

    def test_get_content_from_message_list(self):
        """Test getting content from message with list content"""
        message = {
            "content": [
                {"type": "text", "text": "Hello world"},
                {"type": "image", "url": "image.jpg"}
            ]
        }
        result = get_content_from_message(message)
        assert result == "Hello world"

    def test_get_content_from_message_no_text(self):
        """Test getting content from message with no text content"""
        message = {
            "content": [
                {"type": "image", "url": "image.jpg"}
            ]
        }
        result = get_content_from_message(message)
        assert result is None

    def test_get_last_user_message(self):
        """Test getting last user message content"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = get_last_user_message(messages)
        assert result == "How are you?"

    def test_get_last_user_message_none(self):
        """Test getting last user message when none exists"""
        messages = [{"role": "assistant", "content": "Hi there!"}]
        
        result = get_last_user_message(messages)
        assert result is None

    def test_get_last_assistant_message_item(self):
        """Test getting last assistant message item"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good!"}
        ]
        
        result = get_last_assistant_message_item(messages)
        assert result["content"] == "I'm good!"

    def test_get_last_assistant_message(self):
        """Test getting last assistant message content"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good!"}
        ]
        
        result = get_last_assistant_message(messages)
        assert result == "I'm good!"

    def test_get_system_message(self):
        """Test getting system message"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = get_system_message(messages)
        assert result["content"] == "You are a helpful assistant"

    def test_get_system_message_none(self):
        """Test getting system message when none exists"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = get_system_message(messages)
        assert result is None

    def test_remove_system_message(self):
        """Test removing system message"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = remove_system_message(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_pop_system_message(self):
        """Test popping system message"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        system_msg, remaining = pop_system_message(messages)
        assert system_msg["content"] == "You are a helpful assistant"
        assert len(remaining) == 2
        assert remaining[0]["role"] == "user"

    def test_prepend_to_first_user_message_content_string(self):
        """Test prepending content to first user message with string content"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = prepend_to_first_user_message_content("Please help: ", messages)
        assert result[0]["content"] == "Please help: \nHello"
        assert result[2]["content"] == "How are you?"  # Second user message unchanged

    def test_prepend_to_first_user_message_content_list(self):
        """Test prepending content to first user message with list content"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "image", "url": "image.jpg"}
                ]
            },
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = prepend_to_first_user_message_content("Please help: ", messages)
        assert result[0]["content"][0]["text"] == "Please help: \nHello"

    def test_add_or_update_system_message_add(self):
        """Test adding system message when none exists"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = add_or_update_system_message("You are helpful", messages)
        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful"

    def test_add_or_update_system_message_update_prepend(self):
        """Test updating system message by prepending"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = add_or_update_system_message("Be concise. ", messages)
        assert result[0]["content"] == "Be concise. \nYou are helpful"

    def test_add_or_update_system_message_update_append(self):
        """Test updating system message by appending"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = add_or_update_system_message("Be concise.", messages, append=True)
        assert result[0]["content"] == "You are helpful\nBe concise."

    def test_add_or_update_user_message_add(self):
        """Test adding user message when last message is not user"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = add_or_update_user_message("How are you?", messages)
        assert len(result) == 3
        assert result[-1]["role"] == "user"
        assert result[-1]["content"] == "How are you?"

    def test_add_or_update_user_message_update(self):
        """Test updating user message when last message is user"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = add_or_update_user_message("Also, what's new?", messages)
        assert len(result) == 3
        assert result[-1]["content"] == "How are you?\nAlso, what's new?"

    def test_append_or_update_assistant_message_add(self):
        """Test adding assistant message when last message is not assistant"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = append_or_update_assistant_message("I'm good!", messages)
        assert len(result) == 4
        assert result[-1]["role"] == "assistant"
        assert result[-1]["content"] == "I'm good!"

    def test_append_or_update_assistant_message_update(self):
        """Test updating assistant message when last message is assistant"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        result = append_or_update_assistant_message("How can I help?", messages)
        assert len(result) == 2
        assert result[-1]["content"] == "Hi there!\nHow can I help?"

    def test_empty_messages_list(self):
        """Test functions with empty messages list"""
        messages = []
        
        assert get_last_user_message_item(messages) is None
        assert get_last_user_message(messages) is None
        assert get_last_assistant_message_item(messages) is None
        assert get_last_assistant_message(messages) is None
        assert get_system_message(messages) is None
        assert remove_system_message(messages) == []
        
        system_msg, remaining = pop_system_message(messages)
        assert system_msg is None
        assert remaining == []

    def test_message_content_edge_cases(self):
        """Test edge cases for message content extraction"""
        # Empty content
        message = {"content": ""}
        assert get_content_from_message(message) == ""
        
        # Missing content
        message = {}
        assert get_content_from_message(message) is None
        
        # Empty list content
        message = {"content": []}
        assert get_content_from_message(message) is None
        
        # List with no text items
        message = {"content": [{"type": "image", "url": "test.jpg"}]}
        assert get_content_from_message(message) is None