"""
Tests for checklists model and database operations
"""
import pytest
import json
import time
import uuid
from unittest.mock import patch, MagicMock

from open_webui.models.checklists import (
    Checklists,
    ChecklistModel,
    ChecklistForm,
    ChecklistItemModel,
    ChecklistsTable
)
from open_webui.models.prompts import Prompts, PromptForm


class TestChecklistModel:
    """Test ChecklistModel Pydantic model"""
    
    def test_checklist_model_creation(self):
        """Test creating a ChecklistModel instance"""
        checklist_data = {
            "id": str(uuid.uuid4()),
            "command": "test-checklist",
            "user_id": "test-user",
            "title": "Test Checklist",
            "description": "A test checklist",
            "timestamp": int(time.time()),
            "items": []
        }
        
        checklist = ChecklistModel(**checklist_data)
        
        assert checklist.command == "test-checklist"
        assert checklist.user_id == "test-user"
        assert checklist.title == "Test Checklist"
        assert checklist.description == "A test checklist"
        assert isinstance(checklist.items, list)
    
    def test_checklist_model_with_items(self):
        """Test ChecklistModel with items"""
        item_data = {
            "id": str(uuid.uuid4()),
            "checklist_id": "checklist-1",
            "prompt_command": "test-prompt",
            "order_index": 1,
            "settings": {"option": "value"}
        }
        
        checklist_data = {
            "id": "checklist-1",
            "command": "test-with-items",
            "user_id": "test-user",
            "title": "Test with Items",
            "timestamp": int(time.time()),
            "items": [ChecklistItemModel(**item_data)]
        }
        
        checklist = ChecklistModel(**checklist_data)
        
        assert len(checklist.items) == 1
        assert checklist.items[0].prompt_command == "test-prompt"
        assert checklist.items[0].order_index == 1


class TestChecklistForm:
    """Test ChecklistForm validation"""
    
    def test_checklist_form_creation(self):
        """Test creating a ChecklistForm instance"""
        form_data = {
            "command": "test-form",
            "title": "Test Form",
            "description": "Test description",
            "items": [
                {"prompt_command": "prompt-1", "order_index": 1, "settings": {}},
                {"prompt_command": "prompt-2", "order_index": 2, "settings": {}}
            ]
        }
        
        form = ChecklistForm(**form_data)
        
        assert form.command == "test-form"
        assert form.title == "Test Form"
        assert form.description == "Test description"
        assert len(form.items) == 2
        assert form.items[0]["prompt_command"] == "prompt-1"
    
    def test_checklist_form_defaults(self):
        """Test ChecklistForm with default values"""
        form_data = {
            "command": "test",
            "title": "Test"
        }
        
        form = ChecklistForm(**form_data)
        
        assert form.description is None
        assert form.access_control is None
        assert isinstance(form.items, list)
        assert len(form.items) == 0


class TestChecklistsTable:
    """Test ChecklistsTable database operations"""
    
    @pytest.fixture
    def checklists_table(self):
        """Create ChecklistsTable instance for testing"""
        return ChecklistsTable()
    
    @pytest.fixture
    def sample_prompts(self):
        """Create sample prompts for checklist testing"""
        prompts = []
        
        # Create structured output prompt
        structured_form = PromptForm(
            command="test-structured",
            title="Test Structured Prompt",
            content="Analyze: {{data}}",
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
        
        # Create regular prompt
        regular_form = PromptForm(
            command="test-regular",
            title="Test Regular Prompt", 
            content="Summarize: {{text}}"
        )
        
        # Insert prompts
        structured_prompt = Prompts.insert_new_prompt("test-user", structured_form)
        regular_prompt = Prompts.insert_new_prompt("test-user", regular_form)
        
        prompts = [structured_prompt, regular_prompt]
        return prompts
    
    @pytest.fixture
    def sample_checklist_form(self):
        """Create sample ChecklistForm for testing"""
        return ChecklistForm(
            command="test-checklist",
            title="Test Checklist",
            description="A test checklist with mixed prompt types",
            items=[
                {"prompt_command": "test-structured", "order_index": 1, "settings": {}},
                {"prompt_command": "test-regular", "order_index": 2, "settings": {"priority": "high"}}
            ]
        )
    
    def test_insert_new_checklist(self, checklists_table, sample_prompts, sample_checklist_form):
        """Test inserting a new checklist"""
        # Clean up any existing test checklist
        existing = checklists_table.get_checklist_by_command("test-checklist")
        if existing:
            checklists_table.delete_checklist_by_command("test-checklist")
        
        # Insert new checklist
        result = checklists_table.insert_new_checklist("test-user", sample_checklist_form)
        
        assert result is not None
        assert isinstance(result, ChecklistModel)
        assert result.command == "test-checklist"
        assert result.title == "Test Checklist"
        assert result.description == "A test checklist with mixed prompt types"
        assert len(result.items) == 2
        assert result.user_id == "test-user"
        
        # Verify items are properly ordered
        sorted_items = sorted(result.items, key=lambda x: x.order_index)
        assert sorted_items[0].prompt_command == "test-structured"
        assert sorted_items[1].prompt_command == "test-regular"
        
        # Clean up
        checklists_table.delete_checklist_by_command("test-checklist")
        for prompt in sample_prompts:
            if prompt:
                Prompts.delete_prompt_by_command(prompt.command)
    
    def test_get_checklist_by_command(self, checklists_table, sample_prompts, sample_checklist_form):
        """Test retrieving a checklist by command"""
        # Insert test checklist
        checklists_table.insert_new_checklist("test-user", sample_checklist_form)
        
        # Retrieve checklist
        result = checklists_table.get_checklist_by_command("test-checklist")
        
        assert result is not None
        assert result.command == "test-checklist"
        assert len(result.items) == 2
        
        # Clean up
        checklists_table.delete_checklist_by_command("test-checklist")
        for prompt in sample_prompts:
            if prompt:
                Prompts.delete_prompt_by_command(prompt.command)
    
    def test_get_checklist_by_command_not_found(self, checklists_table):
        """Test retrieving non-existent checklist"""
        result = checklists_table.get_checklist_by_command("non-existent-checklist")
        assert result is None
    
    def test_update_checklist_by_command(self, checklists_table, sample_prompts, sample_checklist_form):
        """Test updating an existing checklist"""
        # Insert test checklist
        checklists_table.insert_new_checklist("test-user", sample_checklist_form)
        
        # Update checklist
        updated_form = ChecklistForm(
            command="test-checklist",
            title="Updated Test Checklist",
            description="Updated description",
            items=[
                {"prompt_command": "test-regular", "order_index": 1, "settings": {"new": "setting"}}
            ]
        )
        
        result = checklists_table.update_checklist_by_command("test-checklist", updated_form)
        
        assert result is not None
        assert result.title == "Updated Test Checklist"
        assert result.description == "Updated description"
        assert len(result.items) == 1
        assert result.items[0].prompt_command == "test-regular"
        assert result.items[0].settings == {"new": "setting"}
        
        # Clean up
        checklists_table.delete_checklist_by_command("test-checklist")
        for prompt in sample_prompts:
            if prompt:
                Prompts.delete_prompt_by_command(prompt.command)
    
    def test_delete_checklist_by_command(self, checklists_table, sample_prompts, sample_checklist_form):
        """Test deleting a checklist"""
        # Insert test checklist
        checklists_table.insert_new_checklist("test-user", sample_checklist_form)
        
        # Verify it exists
        existing = checklists_table.get_checklist_by_command("test-checklist")
        assert existing is not None
        
        # Delete checklist
        result = checklists_table.delete_checklist_by_command("test-checklist")
        assert result is True
        
        # Verify it's gone
        deleted = checklists_table.get_checklist_by_command("test-checklist")
        assert deleted is None
        
        # Clean up prompts
        for prompt in sample_prompts:
            if prompt:
                Prompts.delete_prompt_by_command(prompt.command)
    
    def test_get_checklists(self, checklists_table):
        """Test retrieving all checklists"""
        # Insert test checklists
        form1 = ChecklistForm(command="test-list-1", title="Test 1", items=[])
        form2 = ChecklistForm(command="test-list-2", title="Test 2", items=[])
        
        checklists_table.insert_new_checklist("user1", form1)
        checklists_table.insert_new_checklist("user2", form2)
        
        # Get all checklists
        results = checklists_table.get_checklists()
        
        assert isinstance(results, list)
        # Check that our test checklists are in the results
        test_commands = [c.command for c in results if c.command in ["test-list-1", "test-list-2"]]
        assert "test-list-1" in test_commands
        assert "test-list-2" in test_commands
        
        # Clean up
        checklists_table.delete_checklist_by_command("test-list-1")
        checklists_table.delete_checklist_by_command("test-list-2")
    
    def test_complex_items_workflow(self, checklists_table, sample_prompts):
        """Test checklist with complex item configurations"""
        complex_form = ChecklistForm(
            command="complex-checklist",
            title="Complex Checklist",
            description="Checklist with various item configurations",
            items=[
                {
                    "prompt_command": "test-structured",
                    "order_index": 1,
                    "settings": {
                        "timeout": 30,
                        "retry_count": 3,
                        "custom_variables": {"priority": "high", "category": "analysis"}
                    }
                },
                {
                    "prompt_command": "test-regular",
                    "order_index": 2,
                    "settings": {
                        "output_format": "markdown",
                        "max_length": 500
                    }
                }
            ]
        )
        
        # Insert checklist
        result = checklists_table.insert_new_checklist("test-user", complex_form)
        
        assert result is not None
        assert len(result.items) == 2
        
        # Verify complex settings are preserved
        structured_item = next(item for item in result.items if item.prompt_command == "test-structured")
        assert structured_item.settings["timeout"] == 30
        assert structured_item.settings["custom_variables"]["priority"] == "high"
        
        regular_item = next(item for item in result.items if item.prompt_command == "test-regular")
        assert regular_item.settings["output_format"] == "markdown"
        assert regular_item.settings["max_length"] == 500
        
        # Clean up
        checklists_table.delete_checklist_by_command("complex-checklist")
        for prompt in sample_prompts:
            if prompt:
                Prompts.delete_prompt_by_command(prompt.command)


class TestChecklistsIntegration:
    """Integration tests for checklists functionality"""
    
    def test_checklist_with_structured_prompts_integration(self):
        """Test checklist integration with structured output prompts"""
        checklists = Checklists  # Use the singleton instance
        
        # Create structured prompts
        analysis_schema = json.dumps({
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["summary", "sentiment"]
        })
        
        task_schema = json.dumps({
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "completed": {"type": "boolean"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["task", "completed"]
        })
        
        # Create prompts
        analysis_form = PromptForm(
            command="integration-analysis",
            title="Integration Analysis",
            content="Analyze this text: {{text}}",
            structured_output=True,
            structured_output_schema=analysis_schema
        )
        
        task_form = PromptForm(
            command="integration-task",
            title="Integration Task",
            content="Create a task for: {{description}}",
            structured_output=True,
            structured_output_schema=task_schema
        )
        
        # Insert prompts
        analysis_prompt = Prompts.insert_new_prompt("integration-user", analysis_form)
        task_prompt = Prompts.insert_new_prompt("integration-user", task_form)
        
        # Create checklist
        checklist_form = ChecklistForm(
            command="integration-checklist",
            title="Integration Checklist",
            description="Checklist with structured output prompts",
            items=[
                {"prompt_command": "integration-analysis", "order_index": 1, "settings": {}},
                {"prompt_command": "integration-task", "order_index": 2, "settings": {}}
            ]
        )
        
        # Insert checklist
        checklist = checklists.insert_new_checklist("integration-user", checklist_form)
        
        assert checklist is not None
        assert len(checklist.items) == 2
        
        # Verify integration - check that prompts referenced in checklist have structured output
        for item in checklist.items:
            prompt = Prompts.get_prompt_by_command(item.prompt_command)
            assert prompt is not None
            assert prompt.structured_output is True
            assert prompt.structured_output_schema is not None
        
        # Clean up
        checklists.delete_checklist_by_command("integration-checklist")
        Prompts.delete_prompt_by_command("integration-analysis")
        Prompts.delete_prompt_by_command("integration-task")
    
    def test_checklist_crud_workflow(self):
        """Test complete CRUD workflow for checklists"""
        checklists = Checklists
        
        # Create
        form = ChecklistForm(
            command="crud-test",
            title="CRUD Test Checklist",
            description="Testing CRUD operations",
            items=[
                {"prompt_command": "test-prompt", "order_index": 1, "settings": {}}
            ]
        )
        
        created = checklists.insert_new_checklist("crud-user", form)
        assert created is not None
        
        # Read
        retrieved = checklists.get_checklist_by_command("crud-test")
        assert retrieved is not None
        assert retrieved.command == "crud-test"
        
        # Update
        update_form = ChecklistForm(
            command="crud-test",
            title="Updated CRUD Test",
            description="Updated description",
            items=[
                {"prompt_command": "test-prompt", "order_index": 1, "settings": {"updated": True}},
                {"prompt_command": "new-prompt", "order_index": 2, "settings": {}}
            ]
        )
        
        updated = checklists.update_checklist_by_command("crud-test", update_form)
        assert updated is not None
        assert updated.title == "Updated CRUD Test"
        assert len(updated.items) == 2
        
        # Delete
        deleted = checklists.delete_checklist_by_command("crud-test")
        assert deleted is True
        
        # Verify deletion
        not_found = checklists.get_checklist_by_command("crud-test")
        assert not_found is None
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        checklists = Checklists
        
        # Test with invalid form data
        try:
            # Attempt to create checklist with duplicate command
            form1 = ChecklistForm(command="duplicate-checklist", title="First", items=[])
            form2 = ChecklistForm(command="duplicate-checklist", title="Second", items=[])
            
            result1 = checklists.insert_new_checklist("user1", form1)
            result2 = checklists.insert_new_checklist("user2", form2)  # This should fail or handle gracefully
            
            # Clean up
            if result1:
                checklists.delete_checklist_by_command("duplicate-checklist")
            
        except Exception as e:
            # This is acceptable - the system should handle duplicate commands appropriately
            pass


if __name__ == "__main__":
    pytest.main([__file__])