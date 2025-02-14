# Contract Lifecycle Management System

## Installation

1. **Ensure Python 3.12+ is installed**

```sh
python --version
```

2. Install uv (if not installed)

```sh
pipx install uv
```

3. Set up virtual environment

```sh
uv venv .venv
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate     # On Windows
```

4. Install dependencies

```sh
uv sync
```

## Running the Project

1. Set up your environment variables:

```sh
DEEPSEEK_API_KEY=your_api_key_here
```

2. Run the project:

```sh
python app.py
```
