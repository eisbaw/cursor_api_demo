# Cursor AI CLI Justfile
# Run tasks with: just <task-name>

# Test the ask script with a simple greeting
test:
    ./ask "Hello! Please respond with: I am working perfectly!"

# Demo quantum computing explanation with Claude Sonnet 4
demo:
    ./ask -m claude-4-sonnet "Explain in exactly 2 sentences what quantum computing is"

# Test with a more complex coding question
code-demo:
    ./ask -m claude-4-sonnet "Write a Python function to check if a string is a palindrome, with comments"

# Test streaming decoder directly
test-decoder:
    python3 test_real_decoder.py

# Show available models (requires session)
models:
    python3 test_available_models.py

# Run all tests
test-all: test-decoder demo code-demo

# Clean up generated files
clean:
    rm -f *.pyc
    rm -rf __pycache__
    rm -f response_*.txt

# Show usage help
help:
    @echo "Available commands:"
    @echo "  test       - Basic functionality test"
    @echo "  demo       - Quantum computing demo with Claude Sonnet 4"
    @echo "  code-demo  - Coding example with Claude Sonnet 4"
    @echo "  models     - Show available models"
    @echo "  test-all   - Run all tests"
    @echo "  clean      - Clean up generated files"