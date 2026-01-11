.PHONY: format lint type-check test install-dev

# Format code
format:
	black app tests
	isort app tests

# Lint code
lint:
	flake8 app tests
	pylint app

# Type checking
type-check:
	mypy app --ignore-missing-imports

# Run all checks
check: format lint type-check

# Install development dependencies
install-dev:
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

# Clean cache
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
