# SignalMUSE AI Python Style Guide

## Code Formatting
- Use [Black](https://black.readthedocs.io/en/stable/) for automatic code formatting.
  - Format all code before committing: `black .`

## General Guidelines
- Follow [PEP8](https://peps.python.org/pep-0008/) for code style.
- Use 4 spaces per indentation level.
- Limit lines to 88 characters (Black default).
- Use type hints for all function signatures and variables where possible.
- Write docstrings for all public modules, classes, and functions.
- Use descriptive variable and function names.
- Avoid global variables.

## Imports
- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Use absolute imports where possible.

## Testing
- Place all tests in the `tests/` directory.
- Use `pytest` for writing and running tests.

## Example Docstring
```python
def example_function(param1: int, param2: str) -> bool:
    """
    Brief description of the function.

    Args:
        param1 (int): Description of param1.
        param2 (str): Description of param2.

    Returns:
        bool: Description of return value.
    """
    pass
``` 