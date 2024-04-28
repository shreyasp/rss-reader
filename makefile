test:
	APP_MODE=test pytest --junitxml=junit/test-results.xml --cov=. --cov-report=xml --cov-report=html

run-dev:
	APP_MODE='dev' uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level=debug