"""
Tests for schema validation utilities
"""
import pytest
import json
from open_webui.utils.schema_validation import (
    validate_json_schema,
    convert_to_openai_schema,
    validate_response_against_schema,
    get_schema_examples,
    SchemaValidationError
)


class TestSchemaValidation:
    """Test schema validation functions"""
    
    def test_validate_valid_json_schema(self):
        """Test validation of valid JSON schema"""
        valid_schema = '{"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]}'
        is_valid, error, parsed = validate_json_schema(valid_schema)
        
        assert is_valid is True
        assert error is None
        assert parsed is not None
        assert parsed["type"] == "object"
        assert "result" in parsed["properties"]
    
    def test_validate_invalid_json_syntax(self):
        """Test validation with invalid JSON syntax"""
        invalid_json = '{"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]'  # Missing closing brace
        is_valid, error, parsed = validate_json_schema(invalid_json)
        
        assert is_valid is False
        assert error is not None
        assert "Invalid JSON" in error
        assert parsed is None
    
    def test_validate_invalid_schema_structure(self):
        """Test validation with invalid schema structure"""
        invalid_schema = '{"properties": {"result": {"type": "string"}}}'  # Missing type field
        is_valid, error, parsed = validate_json_schema(invalid_schema)
        
        assert is_valid is False
        assert error is not None
        assert "must have a 'type' field" in error
        assert parsed is None
    
    def test_validate_non_object_schema(self):
        """Test validation with non-object schema"""
        invalid_schema = '"string"'  # String instead of object
        is_valid, error, parsed = validate_json_schema(invalid_schema)
        
        assert is_valid is False
        assert error is not None
        assert "Schema must be a JSON object" in error
        assert parsed is None
    
    def test_convert_to_openai_schema(self):
        """Test conversion to OpenAI schema format"""
        schema = {
            "type": "object",
            "description": "Test schema",
            "properties": {
                "result": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["result"]
        }
        
        openai_schema = convert_to_openai_schema(schema, "test_response")
        
        assert openai_schema["name"] == "test_response"
        assert openai_schema["description"] == "Test schema"
        assert openai_schema["schema"] == schema
        assert openai_schema["strict"] is True
    
    def test_convert_to_openai_schema_default_name(self):
        """Test conversion with default name"""
        schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        
        openai_schema = convert_to_openai_schema(schema)
        
        assert openai_schema["name"] == "response"
        assert openai_schema["description"] == "Structured response"
    
    def test_validate_response_against_schema_valid(self):
        """Test response validation with valid JSON"""
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["result"]
        }
        response = '{"result": "success", "confidence": 0.95}'
        
        is_valid, error = validate_response_against_schema(response, schema)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_response_against_schema_invalid_json(self):
        """Test response validation with invalid JSON"""
        schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        response = '{"result": "success"'  # Missing closing brace
        
        is_valid, error = validate_response_against_schema(response, schema)
        
        assert is_valid is False
        assert error is not None
        assert "Invalid JSON response" in error
    
    def test_validate_response_against_schema_missing_required(self):
        """Test response validation with missing required field"""
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["result", "confidence"]
        }
        response = '{"result": "success"}'  # Missing confidence
        
        is_valid, error = validate_response_against_schema(response, schema)
        
        assert is_valid is False
        assert error is not None
        assert "doesn't match schema" in error
    
    def test_validate_response_against_schema_wrong_type(self):
        """Test response validation with wrong data type"""
        schema = {
            "type": "object",
            "properties": {"confidence": {"type": "number"}},
            "required": ["confidence"]
        }
        response = '{"confidence": "high"}'  # String instead of number
        
        is_valid, error = validate_response_against_schema(response, schema)
        
        assert is_valid is False
        assert error is not None
        assert "doesn't match schema" in error
    
    def test_get_schema_examples(self):
        """Test schema examples retrieval"""
        examples = get_schema_examples()
        
        assert isinstance(examples, dict)
        assert len(examples) > 0
        assert "simple_object" in examples
        assert "checklist_item" in examples
        assert "analysis_result" in examples
        
        # Validate that examples are valid JSON
        for name, schema_str in examples.items():
            parsed = json.loads(schema_str)
            assert isinstance(parsed, dict)
            assert "type" in parsed
    
    def test_schema_examples_validation(self):
        """Test that all provided examples are valid schemas"""
        examples = get_schema_examples()
        
        for name, schema_str in examples.items():
            is_valid, error, parsed = validate_json_schema(schema_str)
            assert is_valid is True, f"Example '{name}' has invalid schema: {error}"
            assert parsed is not None
    
    def test_complex_nested_schema(self):
        """Test validation of complex nested schema"""
        complex_schema = json.dumps({
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "details": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {"type": "string"},
                                    "score": {"type": "number", "minimum": 0, "maximum": 10}
                                },
                                "required": ["category", "score"]
                            }
                        }
                    },
                    "required": ["summary", "details"]
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": True
                }
            },
            "required": ["analysis"]
        })
        
        is_valid, error, parsed = validate_json_schema(complex_schema)
        
        assert is_valid is True
        assert error is None
        assert parsed is not None
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Empty string
        is_valid, error, parsed = validate_json_schema("")
        assert is_valid is False
        assert error is not None
        
        # None input
        with pytest.raises(AttributeError):
            validate_json_schema(None)
        
        # Very large schema (performance test)
        large_schema = {
            "type": "object",
            "properties": {f"field_{i}": {"type": "string"} for i in range(1000)},
            "required": [f"field_{i}" for i in range(100)]
        }
        large_schema_str = json.dumps(large_schema)
        
        is_valid, error, parsed = validate_json_schema(large_schema_str)
        assert is_valid is True
        assert error is None


class TestSchemaValidationIntegration:
    """Integration tests for schema validation with other components"""
    
    def test_openai_integration_workflow(self):
        """Test complete workflow from schema to OpenAI format"""
        # Create schema
        schema_str = json.dumps({
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "completed": {"type": "boolean"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["task", "completed"]
        })
        
        # Validate schema
        is_valid, error, parsed_schema = validate_json_schema(schema_str)
        assert is_valid is True
        
        # Convert to OpenAI format
        openai_schema = convert_to_openai_schema(parsed_schema, "task_item")
        
        assert openai_schema["name"] == "task_item"
        assert openai_schema["strict"] is True
        assert openai_schema["schema"] == parsed_schema
        
        # Test valid response
        valid_response = '{"task": "Write tests", "completed": false, "priority": "high"}'
        is_response_valid, response_error = validate_response_against_schema(valid_response, parsed_schema)
        assert is_response_valid is True
        
        # Test invalid response
        invalid_response = '{"task": "Write tests", "completed": false, "priority": "critical"}'  # Invalid enum
        is_response_valid, response_error = validate_response_against_schema(invalid_response, parsed_schema)
        assert is_response_valid is False
    
    def test_performance_large_schema(self):
        """Test performance with large schemas"""
        import time
        
        # Create large schema
        large_schema = {
            "type": "object",
            "properties": {
                f"category_{i}": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                } for i in range(100)
            }
        }
        schema_str = json.dumps(large_schema)
        
        # Time the validation
        start_time = time.time()
        is_valid, error, parsed = validate_json_schema(schema_str)
        end_time = time.time()
        
        assert is_valid is True
        assert (end_time - start_time) < 1.0  # Should complete within 1 second


if __name__ == "__main__":
    pytest.main([__file__])