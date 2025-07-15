# Project Structure

## Directory Layout
```
extract_taxi_receipts/
├── extract_taxi_receipts/     # Core module package
│   ├── __init__.py           # Package exports
│   ├── core.py              # Main business logic
│   └── __pycache__/         # Python bytecode cache
├── img/                     # Sample receipt images
├── log/                     # Application logs
├── build/                   # PyInstaller build artifacts
├── dist/                    # Distribution files
├── venv/                    # Virtual environment
├── .kiro/                   # Kiro IDE configuration
│   └── steering/            # AI assistant guidance
├── main.py                  # CLI entry point
├── qt-test.py              # GUI application
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables (API keys)
└── README.md               # Documentation
```

## Code Organization

### Core Module (`extract_taxi_receipts/`)
- **Single Responsibility**: Contains only receipt extraction logic
- **Interface Exports**: Public API through `__init__.py`
- **Error Handling**: Custom `CoreError` exception class
- **Stateless Design**: No global state, pure functions

### Entry Points
- **CLI (`main.py`)**: Minimal wrapper for batch processing
- **GUI (`qt-test.py`)**: PyQt5 interface with threading
- **Separation of Concerns**: UI logic separate from business logic

### Configuration Files
- **`.env`**: OpenAI API key (never commit to git)
- **`requirements.txt`**: Pinned dependency versions
- **`.gitignore`**: Excludes build artifacts, logs, API keys

## Naming Conventions
- **Files**: Snake_case for Python files
- **Functions**: Snake_case following PEP 8
- **Classes**: PascalCase (e.g., `CoreError`)
- **Constants**: UPPER_SNAKE_CASE
- **Korean Content**: UTF-8 encoding throughout

## Data Flow
1. **Image Input**: Directory scanning or GUI selection
2. **Pairing**: Alphabetical sorting into front/back pairs
3. **Processing**: Core module handles OpenAI API calls
4. **Output**: CSV generation with timestamp naming
5. **Logging**: Process logs saved to `log/` directory

## Build Artifacts
- **`build/`**: PyInstaller temporary files
- **`dist/`**: Final executable output
- **`*.spec`**: PyInstaller configuration
- **Generated CSVs**: `receipts_YYYYMMDD_HHMM.csv` format