# pyrunner-server
# Python presistent interpreter Service with Timeout and Memory Limits

This project provides an API to run Python code in an isolated subprocess with built-in time and memory limits. The application ensures that the Python code is executed within a 2-second time limit and a 100 MB memory limit, while handling errors appropriately. It uses FastAPI to expose an endpoint for executing code remotely and communicating with the interpreter.

## Features

- **Timeout Handling**: Limits each command to 2 seconds using Python's `signal` module.
- **Memory Limit**: Enforces a memory limit of 100 MB per command using `resource.setrlimit`.
- **Error Handling**: Returns detailed error messages for command timeouts, memory overages, and runtime errors.
- **Presistent Interpreter** sessions are presistent per user and they can use previously defined variables and so on
- **FastAPI Integration**: The service is built with FastAPI to handle HTTP requests and responses.
- **Session Management**: Supports managing multiple user sessions for isolated code execution.

## Requirements

- Python 3.x
- `FastAPI` for web server
- `Uvicorn` for ASGI server
- `Pydantic` for data validation

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/python-shell-code-execution.git
    cd python-shell-code-execution
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    Or install individual dependencies:

    ```bash
    pip install fastapi uvicorn pydantic
    ```

## Usage

### Running the API Server

To run the FastAPI server, use `uvicorn`:

```bash
uvicorn app:app --reload
