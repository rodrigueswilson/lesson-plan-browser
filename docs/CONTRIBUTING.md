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

### Changes to the shared API (lesson-api)

When adding or changing methods in `shared/lesson-api` that may be used by the tablet app, ensure either a **local-DB path** or a **safe default** in standalone mode (so the tablet never depends on HTTP for that method). See [docs/guides/TABLET_STANDALONE_DB.md](guides/TABLET_STANDALONE_DB.md) for the contract and audit list.

### Dependency hygiene (automatic + your part)

- **Dependabot** (GitHub): Opens PRs weekly to bump dependencies (see `.github/dependabot.yml`). Review and merge those PRs to stay updated.
- **pip-audit (CI)**: Runs on every push/PR that touches `requirements.txt` (see `.github/workflows/pip-audit.yml`). The build fails if a known CVE is reported (one exception is documented in the workflow until FastAPI supports a newer Starlette).
- **Your part**: Merge Dependabot PRs when you’re ready; keep `requirements.txt` with pinned versions where possible. To check locally: `pip install pip-audit && pip-audit -r requirements.txt`.

### Running the Backend

```bash
# From project root
python -m uvicorn backend.api:app --reload --port 8000

# Or use the convenience script (from project root)
start-backend.bat  # Windows
.\start-app-with-logs.ps1  # PowerShell: backend + frontend with logs
```

Other batch and PowerShell scripts that were in the root have been archived; see [docs/archive/ROOT_ARCHIVE_INDEX.md](archive/ROOT_ARCHIVE_INDEX.md) for locations.

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running the Frontend

```bash
cd frontend
npm run tauri dev
```

### Running Tests

Use these **canonical commands** (from project root) so everyone and CI use the same gate.

**CI-parity slice (before each commit)** — same surface as the SQLite GitHub Actions step *Run unit-marked critical path tests*: all tests marked `@pytest.mark.unit` (see `pytest.ini` and [docs/dev/verification_and_llm_ops.md](dev/verification_and_llm_ops.md)):

```bash
python -m pytest tests/ -m unit -q
```

**Full suite (before merge or PR)** — entire test suite (several minutes; `pytest.ini` applies `--timeout=120` per test):

```bash
python -m pytest tests/ -q
```

Run from the **project root**. For refactors, use the test command from the plan when refactoring a specific file; otherwise use the **CI-parity** command above. Green-slice options (`-m "not e2e"`, optional ignores) are summarized in [docs/dev/test_suite_status.md](dev/test_suite_status.md). Before merging to `master`, run the full suite.

**Other useful commands:**

```bash
# Run a specific test file
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov=tools -q

# Override timeout (e.g. disable or increase)
python -m pytest tests/ -q --timeout=0
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

### Pre-commit hooks

The project uses [pre-commit](https://pre-commit.com/) to run code style, lint, and security checks before each commit. Contributors are expected to have hooks pass before pushing.

**Install (once per clone):**

```bash
pre-commit install
```

**Run on all files (e.g. before pushing or in CI):**

```bash
pre-commit run --all-files
```

Hooks include Black, flake8, isort, Bandit, mypy, JSON/Jinja2 schema checks, and markdown lint. Install pre-commit with `pip install pre-commit` if needed.

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
│   ├── docx_parser/      # DOCX parsing (package)
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

### Feature development workflow (safe workflow with master as default)

Keep `master` stable and do all new work on branches:

1. **Start from an up-to-date default branch**
   ```bash
   git checkout master
   git pull origin master
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/short-description
   ```
   Use `fix/...`, `docs/...`, or `refactor/...` for non-feature work.

3. **Develop and test locally**
   - Make small, logical commits.
   - Run tests before pushing: `python -m pytest tests/ -q` (or the quick subset from the Testing section).
   - Optionally run `pre-commit run --all-files` to catch style issues.

4. **Push the branch and open a Pull Request**
   ```bash
   git push -u origin feature/short-description
   ```
   Open a PR **into `master`** (not into develop unless you use that as a staging branch). CI runs automatically on the PR and must pass before merge.

5. **Merge when ready**
   After review and green CI, merge the PR into `master`. Then delete the feature branch (GitHub can do this after merge), and pull the updated `master` locally:
   ```bash
   git checkout master
   git pull origin master
   ```

This way `master` always reflects tested, merged work; broken or half-done code stays on the feature branch until the PR is approved and CI passes.

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

1. **Create a branch** from `master` (see "Feature development workflow" above)
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
