"""
Schema validation utilities for structured output prompts
"""
import json
import jsonschema
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, ValidationError


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors"""
    pass


def validate_json_schema(schema_str: str) -> Tuple[bool, Optional[str], Optional[Dict[Any, Any]]]:
    """
    Validate a JSON schema string
    
    Args:
        schema_str: JSON schema as string
        
    Returns:
        Tuple of (is_valid, error_message, parsed_schema)
    """
    try:
        # Parse JSON
        schema = json.loads(schema_str)
        
        # Validate it's a proper JSON schema
        jsonschema.validators.validator_for(schema).check_schema(schema)
        
        # Additional validation for OpenAI compatibility
        if not isinstance(schema, dict):
            return False, "Schema must be a JSON object", None
            
        if "type" not in schema:
            return False, "Schema must have a 'type' field", None
            
        return True, None, schema
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}", None
    except jsonschema.exceptions.SchemaError as e:
        return False, f"Invalid JSON Schema: {str(e)}", None
    except Exception as e:
        return False, f"Schema validation error: {str(e)}", None


def convert_to_openai_schema(schema: Dict[Any, Any], name: str = "response") -> Dict[str, Any]:
    """
    Convert a JSON schema to OpenAI structured output format
    
    Args:
        schema: Parsed JSON schema dictionary
        name: Name for the schema (default: "response")
        
    Returns:
        Dictionary formatted for OpenAI structured output API
    """
    # Clean the schema for OpenAI compatibility
    cleaned_schema = _clean_schema_for_openai(schema.copy())
    
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "description": schema.get("description", "Structured response"),
            "schema": cleaned_schema,
            "strict": False  # Use non-strict mode for better compatibility
        }
    }


def _clean_schema_for_openai(schema: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Clean a JSON schema to make it compatible with OpenAI's structured output
    
    Args:
        schema: Original JSON schema
        
    Returns:
        Cleaned schema compatible with OpenAI
    """
    # Remove problematic fields that might cause issues
    problematic_fields = ["$schema", "definitions", "additionalProperties"]
    
    for field in problematic_fields:
        if field in schema:
            del schema[field]
    
    # Recursively clean nested objects
    if "properties" in schema and isinstance(schema["properties"], dict):
        for prop_name, prop_schema in schema["properties"].items():
            if isinstance(prop_schema, dict):
                schema["properties"][prop_name] = _clean_schema_for_openai(prop_schema)
    
    # Clean array items
    if "items" in schema and isinstance(schema["items"], dict):
        schema["items"] = _clean_schema_for_openai(schema["items"])
    
    return schema


def validate_response_against_schema(response_str: str, schema: Dict[Any, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a JSON response against a schema
    
    Args:
        response_str: JSON response as string
        schema: JSON schema dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        response = json.loads(response_str)
        jsonschema.validate(response, schema)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON response: {str(e)}"
    except jsonschema.exceptions.ValidationError as e:
        return False, f"Response doesn't match schema: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def get_schema_examples() -> Dict[str, str]:
    """
    Get example schemas for common use cases
    
    Returns:
        Dictionary of example name to schema string
    """
    return {
        "simple_object": json.dumps({
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["result"]
        }, indent=2),
        
        "checklist_item": json.dumps({
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "completed": {"type": "boolean"},
                "notes": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["task", "completed"]
        }, indent=2),
        
        "analysis_result": json.dumps({
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "score": {"type": "integer", "minimum": 1, "maximum": 10},
                "recommendations": {
                    "type": "array", 
                    "items": {"type": "string"}
                }
            },
            "required": ["summary", "score"]
        }, indent=2)
    }