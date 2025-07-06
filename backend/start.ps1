# Set protobuf environment variable
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python"

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 