# Contributing to Bilingual Weekly Plan Builder

Thank you for your interest in contributing! This guide will help you set up your development environment and understand our development workflow.

## Development Setup

### Prerequisites

- **Python 3.9+** with pip
- **Node.js 18+** with npm
- **Git** for version control
- **VS Code** (recommended) or your preferred IDE

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LP
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate (Windows)
   .venv\Scripts\activate
   
   # Activate (macOS/Linux)
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy example env file
   copy .env.example .env
   
   # Edit .env and add your API keys
   # OPENAI_API_KEY=your_key_here
   # ANTHROPIC_API_KEY=your_key_here
   ```

4. **Initialize database**
   ```bash
   python -c "from backend.database import Database; db = Database(); db.init_db()"
   ```

5. **Set up frontend** (if working on UI)
   ```bash
   cd frontend
   npm install
   ```

## Development Workflow

### Running the Backend

```bash
# From project root
python -m uvicorn backend.api:app --reload --port 8000

# Or use the convenience script
start-backend.bat  # Windows
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running the Frontend

```bash
cd frontend
npm run tauri dev
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest tests/ --cov=backend --cov=tools

# Run with verbose output
pytest tests/ -v
```

## Code Style

### Python

We follow **PEP 8** with some modifications:

- **Line length**: 100 characters (not 79)
- **Imports**: Grouped and sorted (stdlib, third-party, local)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all modules, classes, and functions

Example:
```python
from typing import List, Optional
from pathlib import Path

def process_lesson(
    lesson_data: dict,
    template_path: Path,
    output_dir: Optional[Path] = None
) -> dict:
    """Process a lesson plan with WIDA enhancements.
    
    Args:
        lesson_data: Parsed lesson plan data
        template_path: Path to DOCX template
        output_dir: Optional output directory
        
    Returns:
        Enhanced lesson plan data with WIDA strategies
        
    Raises:
        ValueError: If lesson_data is invalid
    """
    # Implementation here
    pass
```

### TypeScript/React

- **Formatting**: Prettier with default settings
- **Linting**: ESLint with React plugin
- **Naming**: camelCase for variables, PascalCase for components
- **Hooks**: Follow React Hooks rules

### Running Linters

```bash
# Python
flake8 backend/ tools/
black backend/ tools/ --check

# Format Python code
black backend/ tools/

# TypeScript
cd frontend
npm run lint
npm run format
```

## Project Structure

```
d:\LP/
├── backend/              # FastAPI backend
│   ├── api.py           # Main API endpoints
│   ├── database.py      # SQLite operations
│   ├── llm_service.py   # LLM integration
│   └── file_manager.py  # File organization
├── tools/               # Core processing
│   ├── docx_parser.py   # DOCX parsing
│   ├── docx_renderer.py # DOCX generation
│   ├── batch_processor.py # Weekly processing
│   └── json_merger.py   # JSON consolidation
├── tests/               # Test suite
│   ├── fixtures/        # Test data
│   └── test_*.py        # Test modules
├── frontend/            # Tauri + React
│   └── src/
│       ├── components/  # React components
│       └── store/       # State management
├── templates/           # Jinja2 templates
├── schemas/             # JSON schemas
├── strategies_pack_v2/  # Strategy database
└── docs/                # Documentation
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(parser): add support for multi-column tables
fix(renderer): correct slot ordering in weekly output
docs(readme): update installation instructions
```

### Pull Request Process

1. **Create a branch** from `main`
2. **Make your changes** with clear commits
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** to ensure nothing breaks
6. **Submit PR** with description of changes

## Testing Guidelines

### Test Coverage

- Aim for **80%+ coverage** on new code
- All public APIs must have tests
- Include edge cases and error scenarios

### Test Structure

```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Fixtures

Use pytest fixtures for common test data:

```python
@pytest.fixture
def sample_lesson():
    """Provide sample lesson data."""
    return {
        "subject": "Math",
        "grade_level": "3rd Grade",
        # ...
    }

def test_with_fixture(sample_lesson):
    result = process_lesson(sample_lesson)
    assert result["subject"] == "Math"
```

## Common Tasks

### Adding a New Strategy

1. Update `strategies_pack_v2/core/` or `specialized/`
2. Add strategy to `_index.json`
3. Update strategy dictionary in `docs/`
4. Add tests in `tests/test_strategies.py`

### Adding a New API Endpoint

1. Add endpoint to `backend/api.py`
2. Update OpenAPI docs (automatic via FastAPI)
3. Add integration test in `tests/test_api.py`
4. Update API documentation

### Modifying DOCX Templates

1. Edit Jinja2 templates in `templates/`
2. Test with `tools/docx_renderer.py`
3. Verify output formatting
4. Update template documentation

## Debugging

### Backend Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend Debugging

- Use browser DevTools (F12)
- Check Tauri console for Rust logs
- Use React DevTools extension

### Common Issues

See **[Troubleshooting Guide](guides/TROUBLESHOOTING_QUICK_REFERENCE.md)** for solutions to common problems.

## Documentation

### Updating Documentation

- Keep README.md current
- Update relevant guides in `docs/`
- Add examples for new features
- Update CHANGELOG.md

### Documentation Standards

- Use Markdown for all docs
- Include code examples
- Add screenshots for UI changes
- Keep language clear and concise

## Getting Help

- **Issues**: Check existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Tag maintainers in PRs

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console.log or debug statements
- [ ] Type hints added (Python)
- [ ] Error handling implemented
- [ ] Performance considered
- [ ] Security implications reviewed

## Release Process

1. Update version in `CHANGELOG.md`
2. Tag release: `git tag v1.x.x`
3. Build production bundle
4. Test deployment package
5. Create GitHub release
6. Update documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing!** Your efforts help improve bilingual education for multilingual learners.
