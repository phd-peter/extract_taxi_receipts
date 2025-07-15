# Technology Stack

## Core Dependencies
- **Python 3.8+**: Primary runtime
- **OpenAI API**: GPT-4 Vision for image analysis
- **pandas**: Data manipulation and CSV export
- **python-dotenv**: Environment variable management

## GUI Framework
- **PyQt5/PySide6**: Desktop application interface
- **PyInstaller**: Executable packaging for distribution

## Architecture Pattern
- **Modular Core**: Shared business logic in `extract_taxi_receipts.core`
- **Interface Separation**: CLI (`main.py`) and GUI (`qt-test.py`) as thin wrappers
- **Error Handling**: Custom `CoreError` exceptions for consistent error management

## API Integration
- **OpenAI GPT-4o**: Vision model for receipt analysis
- **Function Calling**: Structured data extraction using OpenAI tools
- **Base64 Encoding**: Image preprocessing for API calls

## Common Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
# Create .env file with OPENAI_API_KEY
```

### Running the Application
```bash
# CLI mode
python main.py [image_directory]

# GUI mode
python qt-test.py
```

### Building Executable
```bash
# Create standalone executable
pyinstaller qt-test.spec
```

### Testing
```bash
# Run with sample images
python main.py ./img
```

## File Processing
- **Supported Formats**: .jpg, .jpeg, .png
- **Pairing Logic**: Alphabetical sorting for front/back matching
- **Output Format**: UTF-8 CSV with BOM for Excel compatibility