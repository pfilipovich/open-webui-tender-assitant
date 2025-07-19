"""
A simple calculator tool for mathematical operations.
"""

def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract two numbers."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def calculate(expression: str) -> str:
    """
    Calculate a mathematical expression.
    
    Args:
        expression: A mathematical expression as a string
        
    Returns:
        The result of the calculation as a string
    """
    try:
        # Simple expression evaluation (in production, use a safer alternative)
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"