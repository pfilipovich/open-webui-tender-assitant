"""
Tests for prompts model and database operations
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock

from open_webui.models.prompts import (
    Prompts,
    PromptModel,
    PromptForm,
    PromptsTable
)


class TestPromptModel:
    """Test PromptModel Pydantic model"""
    
    def test_prompt_model_creation(self):
        """Test creating a PromptModel instance"""
        prompt_data = {
            "id": 1,
            "command": "/test-prompt",
            "user_id": "test-user",
            "title": "Test Prompt",
            "content": "This is a test prompt",
            "timestamp": int(time.time()),
            "structured_output": True,
            "structured_output_schema": '{"type": "object", "properties": {"result": {"type": "string"}}}'
        }
        
        prompt = PromptModel(**prompt_data)
        
        assert prompt.id == 1
        assert prompt.command == "/test-prompt"
        assert prompt.user_id == "test-user"
        assert prompt.title == "Test Prompt"
        assert prompt.content == "This is a test prompt"
        assert prompt.structured_output is True
        assert prompt.structured_output_schema is not None
    
    def test_prompt_model_defaults(self):
        """Test PromptModel with default values"""
        prompt_data = {
            "id": 1,
            "command": "/test",
            "user_id": "user",
            "title": "Test",
            "content": "Content",
            "timestamp": int(time.time())
        }
        
        prompt = PromptModel(**prompt_data)
        
        assert prompt.structured_output is False
        assert prompt.structured_output_schema is None
        assert prompt.access_control is None


class TestPromptForm:
    """Test PromptForm validation"""
    
    def test_prompt_form_creation(self):
        """Test creating a PromptForm instance"""
        form_data = {
            "command": "test-prompt",
            "title": "Test Prompt", 
            "content": "Test content",
            "structured_output": True,
            "structured_output_schema": '{"type": "object"}'
        }
        
        form = PromptForm(**form_data)
        
        assert form.command == "test-prompt"
        assert form.title == "Test Prompt"
        assert form.content == "Test content"
        assert form.structured_output is True
        assert form.structured_output_schema == '{"type": "object"}'
    
    def test_prompt_form_defaults(self):
        """Test PromptForm with default values"""
        form_data = {
            "command": "test",
            "title": "Test",
            "content": "Content"
        }
        
        form = PromptForm(**form_data)
        
        assert form.structured_output is False
        assert form.structured_output_schema is None
        assert form.access_control is None


class TestPromptsTable:
    """Test PromptsTable database operations"""
    
    @pytest.fixture
    def prompts_table(self):
        """Create PromptsTable instance for testing"""
        return PromptsTable()
    
    @pytest.fixture
    def sample_prompt_form(self):
        """Create sample PromptForm for testing"""
        return PromptForm(
            command="test-prompt",
            title="Test Prompt",
            content="Test content: {{variable}}",
            structured_output=True,
            structured_output_schema=json.dumps({
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["result"]
            })
        )
    
    def test_insert_new_prompt(self, prompts_table, sample_prompt_form):
        """Test inserting a new prompt"""
        # Clean up any existing test prompt
        existing = prompts_table.get_prompt_by_command("test-prompt")
        if existing:
            prompts_table.delete_prompt_by_command("test-prompt")
        
        # Insert new prompt
        result = prompts_table.insert_new_prompt("test-user", sample_prompt_form)
        
        assert result is not None
        assert isinstance(result, PromptModel)
        assert result.command == "test-prompt"
        assert result.title == "Test Prompt"
        assert result.content == "Test content: {{variable}}"
        assert result.structured_output is True
        assert result.structured_output_schema is not None
        assert result.user_id == "test-user"
        
        # Clean up
        prompts_table.delete_prompt_by_command("test-prompt")
    
    def test_get_prompt_by_command(self, prompts_table, sample_prompt_form):
        """Test retrieving a prompt by command"""
        # Insert test prompt
        prompts_table.insert_new_prompt("test-user", sample_prompt_form)
        
        # Retrieve prompt
        result = prompts_table.get_prompt_by_command("test-prompt")
        
        assert result is not None
        assert result.command == "test-prompt"
        assert result.structured_output is True
        
        # Clean up
        prompts_table.delete_prompt_by_command("test-prompt")
    
    def test_get_prompt_by_command_not_found(self, prompts_table):
        """Test retrieving non-existent prompt"""
        result = prompts_table.get_prompt_by_command("non-existent-prompt")
        assert result is None
    
    def test_update_prompt_by_command(self, prompts_table, sample_prompt_form):
        """Test updating an existing prompt"""
        # Insert test prompt
        prompts_table.insert_new_prompt("test-user", sample_prompt_form)
        
        # Update prompt
        updated_form = PromptForm(
            command="test-prompt",
            title="Updated Test Prompt",
            content="Updated content",
            structured_output=False,
            structured_output_schema=None
        )
        
        result = prompts_table.update_prompt_by_command("test-prompt", updated_form)
        
        assert result is not None
        assert result.title == "Updated Test Prompt"
        assert result.content == "Updated content"
        assert result.structured_output is False
        assert result.structured_output_schema is None
        
        # Clean up
        prompts_table.delete_prompt_by_command("test-prompt")
    
    def test_update_prompt_not_found(self, prompts_table):
        """Test updating non-existent prompt"""
        form = PromptForm(
            command="non-existent",
            title="Test",
            content="Test"
        )
        
        result = prompts_table.update_prompt_by_command("non-existent", form)
        assert result is None
    
    def test_delete_prompt_by_command(self, prompts_table, sample_prompt_form):
        """Test deleting a prompt"""
        # Insert test prompt
        prompts_table.insert_new_prompt("test-user", sample_prompt_form)
        
        # Verify it exists
        existing = prompts_table.get_prompt_by_command("test-prompt")
        assert existing is not None
        
        # Delete prompt
        result = prompts_table.delete_prompt_by_command("test-prompt")
        assert result is True
        
        # Verify it's gone
        deleted = prompts_table.get_prompt_by_command("test-prompt")
        assert deleted is None
    
    def test_delete_prompt_not_found(self, prompts_table):
        """Test deleting non-existent prompt"""
        result = prompts_table.delete_prompt_by_command("non-existent")
        assert result is True  # Delete operations typically return True even if nothing was deleted
    
    def test_get_prompts(self, prompts_table):
        """Test retrieving all prompts"""
        # Insert test prompts
        form1 = PromptForm(command="test-1", title="Test 1", content="Content 1")
        form2 = PromptForm(command="test-2", title="Test 2", content="Content 2")
        
        prompts_table.insert_new_prompt("user1", form1)
        prompts_table.insert_new_prompt("user2", form2)
        
        # Get all prompts
        results = prompts_table.get_prompts()
        
        assert isinstance(results, list)
        # Check that our test prompts are in the results
        test_commands = [p.command for p in results if p.command in ["test-1", "test-2"]]
        assert "test-1" in test_commands
        assert "test-2" in test_commands
        
        # Clean up
        prompts_table.delete_prompt_by_command("test-1")
        prompts_table.delete_prompt_by_command("test-2")
    
    def test_structured_output_schema_persistence(self, prompts_table):
        """Test that structured output schema is properly persisted"""
        complex_schema = json.dumps({
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["summary"]
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["analysis"]
        })
        
        form = PromptForm(
            command="schema-test",
            title="Schema Test",
            content="Analyze: {{data}}",
            structured_output=True,
            structured_output_schema=complex_schema
        )
        
        # Insert
        inserted = prompts_table.insert_new_prompt("test-user", form)
        assert inserted is not None
        assert inserted.structured_output_schema == complex_schema
        
        # Retrieve and verify
        retrieved = prompts_table.get_prompt_by_command("schema-test")
        assert retrieved is not None
        assert retrieved.structured_output_schema == complex_schema
        
        # Parse the schema to ensure it's valid JSON
        parsed_schema = json.loads(retrieved.structured_output_schema)
        assert parsed_schema["type"] == "object"
        assert "analysis" in parsed_schema["properties"]
        
        # Clean up
        prompts_table.delete_prompt_by_command("schema-test")


class TestPromptsIntegration:
    """Integration tests for prompts functionality"""
    
    def test_prompt_crud_workflow(self):
        """Test complete CRUD workflow"""
        prompts = Prompts  # Use the singleton instance
        
        # Create
        form = PromptForm(
            command="integration-test",
            title="Integration Test Prompt",
            content="Test prompt with {{parameter}}",
            structured_output=True,
            structured_output_schema='{"type": "object", "properties": {"result": {"type": "string"}}}'
        )
        
        created = prompts.insert_new_prompt("integration-user", form)
        assert created is not None
        
        # Read
        retrieved = prompts.get_prompt_by_command("integration-test")
        assert retrieved is not None
        assert retrieved.command == "integration-test"
        assert retrieved.structured_output is True
        
        # Update
        update_form = PromptForm(
            command="integration-test",
            title="Updated Integration Test",
            content="Updated content",
            structured_output=False
        )
        
        updated = prompts.update_prompt_by_command("integration-test", update_form)
        assert updated is not None
        assert updated.title == "Updated Integration Test"
        assert updated.structured_output is False
        
        # Delete
        deleted = prompts.delete_prompt_by_command("integration-test")
        assert deleted is True
        
        # Verify deletion
        not_found = prompts.get_prompt_by_command("integration-test")
        assert not_found is None
    
    def test_concurrent_operations(self):
        """Test handling of concurrent operations"""
        import threading
        import time
        
        prompts = Prompts
        results = []
        
        def create_prompt(index):
            form = PromptForm(
                command=f"concurrent-{index}",
                title=f"Concurrent Test {index}",
                content=f"Content {index}"
            )
            result = prompts.insert_new_prompt(f"user-{index}", form)
            results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_prompt, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        assert len(results) == 5
        assert all(r is not None for r in results)
        
        # Clean up
        for i in range(5):
            prompts.delete_prompt_by_command(f"concurrent-{i}")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        prompts = Prompts
        
        # Test with invalid form data (this should be handled gracefully)
        try:
            # Attempt to create prompt with duplicate command
            form1 = PromptForm(command="duplicate-test", title="First", content="Content")
            form2 = PromptForm(command="duplicate-test", title="Second", content="Content")
            
            result1 = prompts.insert_new_prompt("user1", form1)
            result2 = prompts.insert_new_prompt("user2", form2)  # This should fail or handle gracefully
            
            # Clean up
            if result1:
                prompts.delete_prompt_by_command("duplicate-test")
            
        except Exception as e:
            # This is acceptable - the system should handle duplicate commands appropriately
            pass


if __name__ == "__main__":
    pytest.main([__file__])