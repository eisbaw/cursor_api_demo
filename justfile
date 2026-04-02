# Cursor AI CLI Justfile
# Run tasks with: just <task-name>

# Test the ask script with a simple greeting
test:
    ./ask "Hello! Please respond with: I am working perfectly!"

# Demo question through default model routing
demo:
    ./ask "Explain in exactly 2 sentences what quantum computing is"

# Demo with live streaming output
stream-demo:
    ./ask --stream "Write exactly two short sentences about HTTP/2 streaming."

# Test streaming decoder directly
test-decoder:
    python3 test_real_decoder.py

# Run all tests
test-all: test test-decoder demo

# Clean up generated files
clean:
    rm -f *.pyc
    rm -rf __pycache__
    rm -f response_*.txt

# Show usage help
help:
    @echo "Available commands:"
    @echo "  test       - Basic functionality test"
    @echo "  demo       - End-to-end demo prompt"
    @echo "  stream-demo - End-to-end demo with live streaming output"
    @echo "  test-decoder - Decoder unit-style protobuf frame test"
    @echo "  test-all   - Run all tests"
    @echo "  clean      - Clean up generated files"