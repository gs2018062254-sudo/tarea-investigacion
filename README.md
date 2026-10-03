# SecureScan Demo

A simple Python Flask application created to demonstrate
source code security analysis using Bandit as part of a DevSecOps workflow.

## Technologies

- Python 3
- Flask - Web framework
- Bandit - Python source code security analyzer (SAST)
- GitHub Actions - CI/CD automation
- Gunicorn - Production WSGI server

## Project Structure

```
secure-scan-demo/
├── app.py
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── security-scan.yml
```

## Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the application

```bash
python app.py
```

The application will be available at: http://localhost:5000

## Security Scanning with Bandit

### Install Bandit

```bash
pip install bandit
```

### Run security scan

```bash
bandit -r . -f txt -o bandit-report.txt
```

Or for a concise output:

```bash
bandit -r .
```

## Automated Pipeline (GitHub Actions)

The repository includes a workflow in `.github/workflows/security-scan.yml` that:

1. Triggers on every push and pull request to the main branch
2. Sets up Python
3. Installs dependencies
4. Runs Bandit security analysis
5. Generates and uploads a report artifact
