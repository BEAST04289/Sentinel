# Contributing to Sentinel

First off, thank you for considering contributing to Sentinel! 🎉

This project is built by a 1st Year BTech CSE student learning AI/ML by building real systems. Contributions from the community help make this project better and provide learning opportunities for everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)

---

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Please report unacceptable behavior.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- 4GB RAM minimum
- (Optional) NVIDIA GPU for faster embeddings

### Fork the Repository

1. Fork the repo on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/sentinel.git
   cd sentinel
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/sentinel.git
   ```

---

## 💻 Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black ruff mypy
```

### 3. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys (optional)
```

### 4. Verify Installation

```bash
# Run the server
python main.py

# In another terminal, test the API
curl http://localhost:8000/health
```

---

## 📁 Project Structure

Understanding the codebase:

```
sentinel/
├── main.py                 # FastAPI application (start here!)
│
├── data/                   # DATA FABRIC LAYER
│   ├── embeddings.py       # Embedding service (sentence-transformers)
│   ├── vector_store.py     # Hybrid ChromaDB + FAISS
│   ├── document_processor.py  # PDF parsing + chunking
│   └── pipeline.py         # Ingestion metrics
│
├── agents/                 # AGENTIC BRAIN LAYER
│   ├── state.py            # LangGraph state definitions
│   ├── watchdog.py         # Monitoring agent
│   ├── analyst.py          # Analysis agent (GPT-4)
│   └── graph.py            # Agent orchestration
│
├── mock_data/              # Demo data for testing
│   └── mock_filings.py     # 5 realistic SEC filings
│
├── ui/                     # Frontend
│   └── dashboard.html      # Premium glassmorphism UI
│
└── tests/                  # Test suite
    └── test_sentinel.py    # Unit + integration tests
```

---

## ✏️ Making Changes

### 1. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Branch Naming Convention

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/add-rss-ingestion` |
| Bug Fix | `fix/description` | `fix/embedding-cache-bug` |
| Docs | `docs/description` | `docs/update-readme` |
| Refactor | `refactor/description` | `refactor/vector-store` |

### 3. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]
```

Examples:
```
feat(embeddings): add support for nomic model
fix(pipeline): resolve memory leak in chunking
docs(readme): add performance benchmarks
refactor(vector_store): simplify query logic
```

---

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Code builds without errors: `python main.py`
- [ ] Tests pass: `pytest tests/`
- [ ] Code is formatted: `black .`
- [ ] Linting passes: `ruff check .`
- [ ] Documentation updated (if needed)

### 2. PR Template

When opening a PR, include:

```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
[Describe tests you ran]

## Checklist
- [ ] My code follows the project style
- [ ] I have added tests
- [ ] I have updated documentation
- [ ] My changes don't break existing functionality
```

### 3. Review Process

1. A maintainer will review your PR
2. Address any feedback
3. Once approved, your PR will be merged!

---

## 🎨 Style Guidelines

### Python Style

We use:
- **Black** for formatting (line length: 88)
- **Ruff** for linting
- **Type hints** for function signatures

```python
# ✅ Good
async def process_document(
    content: bytes,
    filename: str,
    source: str = "upload"
) -> List[ProcessedChunk]:
    """Process document with full NLP pipeline."""
    ...

# ❌ Bad
def process_document(content, filename, source="upload"):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_salience(text: str) -> float:
    """
    Calculate risk salience score for text.
    
    Args:
        text: Input document text
        
    Returns:
        Salience score between 0.0 and 1.0
        
    Example:
        >>> calculate_salience("lawsuit filed")
        0.4
    """
```

### HTML/CSS Style

- Use 4 spaces for indentation
- Use CSS custom properties (variables)
- Keep component styles modular

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific test file
pytest tests/test_sentinel.py

# Verbose output
pytest tests/ -v
```

### Writing Tests

```python
import pytest
from data.document_processor import calculate_salience

def test_salience_high_risk():
    """Test that lawsuit keyword triggers high salience."""
    text = "Company faces class action lawsuit"
    salience = calculate_salience(text)
    assert salience >= 0.4

@pytest.mark.asyncio
async def test_document_processing():
    """Test full document processing pipeline."""
    content = b"NVIDIA announces earnings miss"
    chunks = await process_document(content, "test.txt")
    assert len(chunks) > 0
```

---

## 🐛 Reporting Bugs

Use GitHub Issues with this template:

```markdown
## Bug Description
[Clear description of the bug]

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [e.g., Windows 11]
- Python: [e.g., 3.11.5]
- Browser: [e.g., Chrome 120]

## Screenshots
[If applicable]
```

---

## 💡 Feature Requests

Before requesting a feature:
1. Check existing issues
2. Consider if it fits the project scope

Use this template:
```markdown
## Feature Description
[What feature do you want?]

## Use Case
[Why do you need this?]

## Proposed Solution
[How might this work?]

## Alternatives Considered
[Other approaches you thought of]
```

---

## 🏆 Recognition

Contributors will be:
- Added to the Contributors section in README
- Credited in release notes
- Part of making financial risk monitoring accessible!

---

## ❓ Questions?

- Open a GitHub Discussion
- Comment on relevant issues

---

Thank you for contributing! 🙏

*Built with ❤️ by the Sentinel community*
