# Service Analyzer

AI-powered service analysis tool that provides comprehensive analysis of services and products using artificial intelligence for data processing and report generation.

## Features

- Comprehensive service analysis (business, technical, and user aspects)
- AI-powered insights and recommendations
- Detailed markdown reports in Russian
- Support for both terminal preview and file output
- Rich terminal interface with progress indicators
- Support for known service names or raw text descriptions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/service-analyzer.git
cd service-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic usage with known service name:
```bash
python main.py "Spotify" --api-key "your-openai-api-key"
```

### Usage with service description:
```bash
python main.py "Новый сервис" --description "Платформа для создания и монетизации онлайн-курсов" --api-key "your-openai-api-key"
```

### Save report to file:
```bash
python main.py "Notion" --api-key "your-openai-api-key" --output "reports/notion_analysis.md"
```

### With optional URL:
```bash
python main.py "GitHub" --url "https://github.com" --api-key "your-openai-api-key"
```

For Windows users, you can use the provided batch file:
```bash
run_analysis.bat
```

### Command Line Options

- `name`: Service name (required)
- `--api-key`: OpenAI API key (required, can be set via environment variable)
- `--url`: Service URL (optional)
- `--description`: Service description or raw text (optional)
- `--output`: Path to save the report (optional, default: reports/analysis.md)
- `--no-preview`: Disable terminal preview (default: False)

## Examples

See [sample_outputs.md](sample_outputs.md) for detailed examples of the application's output, including:
- Analysis of known services (Spotify)
- Analysis based on service descriptions
- File output examples
- Error handling examples

## Report Sections

The generated markdown report includes the following sections:

### Business Analysis
- **Краткая история**: Year founded, important development milestones
- **Целевая аудитория**: Main user segments
- **Основные функции**: 2-4 key functionalities
- **Уникальные торговые преимущества**: Key differentiators from competitors
- **Бизнес-модель**: How the service makes money
- **Информация о технологическом стеке**: Hints about used technologies
- **Восприятие сильных сторон**: Positive aspects or outstanding features
- **Восприятие слабых сторон**: Mentioned disadvantages or limitations

### Technical Analysis
- Technology stack analysis
- Architecture and scalability
- Technical requirements and risks
- Security and performance aspects

### User Experience Analysis
- Key user scenarios
- UX issues and recommendations
- Interface requirements
- Success metrics

## Project Structure

```
service-analyzer/
├── analyzers/                 # Analysis modules
│   ├── __init__.py
│   ├── base_analyzer.py      # Base analyzer class
│   ├── business_analyzer.py  # Business analysis
│   ├── technical_analyzer.py # Technical analysis
│   └── user_analyzer.py      # User experience analysis
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── data/               # Test data
│   │   └── test_service.json
│   ├── test_base_analyzer.py
│   ├── test_business_analyzer.py
│   ├── test_technical_analyzer.py
│   └── test_user_analyzer.py
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── pytest.ini              # Pytest settings
├── .gitignore             # Git ignore rules
├── sample_outputs.md      # Example outputs
└── README.md              # This file
```

## Testing

The project includes a comprehensive test suite. To run the tests:

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

For test coverage report:
```bash
pytest --cov=analyzers
```

### Test Structure

- `tests/test_base_analyzer.py`: Tests for base analyzer functionality
- `tests/test_business_analyzer.py`: Tests for business analysis
- `tests/test_technical_analyzer.py`: Tests for technical analysis
- `tests/test_user_analyzer.py`: Tests for user experience analysis
- `tests/data/test_service.json`: Sample test data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 