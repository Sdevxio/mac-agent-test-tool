# FileService

A gRPC-based file service for macOS that provides file operations and transfer capabilities.

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Generate gRPC code:
```bash
python -m grpc_tools.protoc \
    --proto_path=proto \
    --python_out=src/fileservice \
    --grpc_python_out=src/fileservice \
    proto/file_service.proto
```

## Project Structure

- `proto/`: Protocol buffer definitions
- `src/fileservice/`: Main package source code
  - `server/`: Server implementation
  - `client/`: Client library code
- `tests/`: Test files

## Running Tests

```bash
pytest tests/
```