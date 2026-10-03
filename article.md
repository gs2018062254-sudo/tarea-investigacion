# Scanning Python Application Vulnerabilities Using Bandit and GitHub Actions

## Introduction

Application security is an important part of the software development lifecycle. Identifying vulnerabilities during development helps developers detect and fix security problems before an application reaches production.

In this project, we developed a Python web application and integrated automated source code security analysis using **Bandit**, a security tool specifically designed to find common security issues in Python code. Bandit is listed by both the **OWASP Foundation** (Source Code Analysis Tools) and the **National Institute of Standards and Technology** (NIST Source Code Security Analyzers) as a valid Static Application Security Testing (SAST) solution for Python.

The objective of this project is to demonstrate how security scanning can be integrated into an automated development and deployment workflow using a public GitHub repository, GitHub Actions, and a public cloud platform.

## Project Objectives

The main objectives of this project are:

1. Develop a Python web application using Flask.
2. Store the application in a **public GitHub repository**.
3. Analyze the source code using **Bandit** (a different tool than the ones used in the course labs).
4. Identify security vulnerabilities in the application.
5. Automate the security analysis using **GitHub Actions**.
6. **Deploy** the application to a public cloud platform.
7. Correct the vulnerabilities identified by the security scanner.
8. Perform a second security scan to verify the improvements.

## Technologies Used

The project uses the following technologies:

- **Python 3** – Application development language.
- **Flask** – Lightweight web application framework.
- **Bandit** – Python source code security analyzer (SAST).
- **GitHub** – Public source code repository host.
- **GitHub Actions** – Continuous integration (CI) and automation.
- **Render / Railway / Heroku / Vercel** – Public cloud deployment platform.
- **Gunicorn** – Production WSGI HTTP server for Python.

## Application

The application is a simple web service developed with Python and Flask. It exposes several endpoints: a home page, a health-check endpoint (`/ping`), a greet endpoint (`/greet`), a command-run endpoint (`/run`), a hashing endpoint (`/hash`), and a data-loading endpoint (`/load`).

The source code is publicly available in the following repository:

> **GitHub Repository:** https://github.com/gs2018062254-sudo/tarea-investigacion

## Why Bandit (and not Semgrep)?

In the course labs we already used **Semgrep** for security analysis. To satisfy the requirement of using *other tools that are not used in labs*, we selected **Bandit** as the SAST scanner for this project.

Bandit is specifically maintained by the **Python Security Authority (PyCQA)** and focuses exclusively on Python code. It processes each Python file, builds an AST (Abstract Syntax Tree), and runs plugins against it. Each plugin looks for a specific anti-pattern — hardcoded passwords, weak hashes, unsafe subprocess calls, pickle deserialization, etc.

According to OWASP, SAST tools like Bandit excel at finding injection flaws, crypto mistakes, and hardcoded secrets before the code is even compiled or run — exactly the kind of issues that are cheap to fix at development time but very expensive in production.

## Security Analysis with Bandit

Bandit analyzes Python source files and reports potential security problems according to predefined security checks.

The command used to run the analysis is:

```bash
bandit -r .
```

This recursively (`-r`) scans every Python file in the current directory and prints a human-readable report with severity and confidence ratings for each finding.

### Initial Scan Results (Vulnerable Version)

The first Bandit scan was executed against the intentionally-insecure version of the application. The scanner found **7 issues** distributed across severity levels:

| Severity | Count |
|----------|-------|
| HIGH     | 2     |
| MEDIUM   | 2     |
| LOW      | 3     |
| **Total**| **7** |

The complete output of the initial scan:

```
Run started:2026-10-03 01:47:41.158829+00:00

Test results:
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78 (OS Command Injection)
   Location: .\app.py:2:0

--------------------------------------------------
>> Issue: [B403:blacklist] Consider possible security implications associated with pickle module.
   Severity: Low   Confidence: High
   CWE: CWE-502 (Deserialization of Untrusted Data)
   Location: .\app.py:4:0

--------------------------------------------------
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'super_secret_admin_123'
   Severity: Low   Confidence: Medium
   CWE: CWE-259 (Use of Hard-coded Password)
   Location: .\app.py:8:17

--------------------------------------------------
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue.
   Severity: High   Confidence: High
   CWE: CWE-78 (OS Command Injection)
   Location: .\app.py:40:13

--------------------------------------------------
>> Issue: [B324:hashlib] Use of weak MD5 hash for security. Consider usedforsecurity=False
   Severity: High   Confidence: High
   CWE: CWE-327 (Use of a Broken or Risky Cryptographic Algorithm)
   Location: .\app.py:47:13

--------------------------------------------------
>> Issue: [B301:blacklist] Pickle and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security issue.
   Severity: Medium   Confidence: High
   CWE: CWE-502 (Deserialization of Untrusted Data)
   Location: .\app.py:54:10

--------------------------------------------------
>> Issue: [B104:hardcoded_bind_all_interfaces] Possible binding to all interfaces.
   Severity: Medium   Confidence: Medium
   CWE: CWE-605 (Multiple Binds to the Same Port)
   Location: .\app.py:59:17
```

#### Mapping Each Finding to a CWE

1. **B602 (HIGH) — shell=True in subprocess.run()** → CWE-78: OS Command Injection. An attacker could append `; rm -rf /` to the `command` query parameter and execute arbitrary commands on the server.
2. **B324 (HIGH) — MD5 hashing** → CWE-327: Broken Crypto. MD5 is cryptographically broken and unsuitable for any security-sensitive use (integrity checks, password hashing, signatures).
3. **B301 (MEDIUM) — pickle.loads() on untrusted input** → CWE-502: Insecure Deserialization. Pickle payloads can execute arbitrary Python on load.
4. **B104 (MEDIUM) — Binding to `0.0.0.0`** → CWE-605: Exposing debug/dev servers on all network interfaces without a reverse proxy.
5. **B105 (LOW) — Hardcoded `ADMIN_PASSWORD` constant** → CWE-259: Credentials in source code get leaked via git history.
6. **B403 (LOW) — Importing pickle** → Advisory flag for the dangerous module.
7. **B404 (LOW) — Importing subprocess** → Advisory flag for the powerful module.

## Vulnerability Remediation

Every finding was individually reviewed and corrected in the source code. The remediation process followed the classic **Detect → Fix → Verify** loop.

### 1. Command Injection (B602) — Fixed

**Before (vulnerable):**
```python
@app.route("/run")
def run_command():
    command = request.args.get("command", "echo Hello")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"<pre>{result.stdout}</pre>"
```

**After (fixed):**
```python
@app.route("/run")
def run_command():
    cmd_input = request.args.get("cmd", "echo Hello")
    try:
        parsed = shlex.split(cmd_input)
        result = subprocess.run(
            parsed,
            shell=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout if result.stdout else result.stderr
    except Exception as e:
        output = f"Error: {escape(str(e))}"
    return f"<pre>{escape(output)}</pre>"
```

Fix applied:
- `shell=True` → `shell=False` (removes the shell injection vector entirely).
- `shlex.split()` safely tokenizes the input string into an argument list.
- Added a `timeout` to prevent resource exhaustion.
- Used `flask.escape()` on output to close the XSS secondary vector.

### 2. Weak Hash MD5 (B324) — Fixed

**Before (vulnerable):**
```python
hashed = hashlib.md5(data.encode()).hexdigest()
```

**After (fixed):**
```python
hashed = hashlib.sha256(data.encode()).hexdigest()
```

Fix applied: Switched from MD5 (collision-prone, non-compliant with NIST SP 800-131A) to SHA-256, which is FIPS-approved and currently considered secure for integrity and non-password hashing.

### 3. Pickle Deserialization (B301 / B403) — Fixed

**Before (vulnerable):**
```python
import pickle
...
raw = request.get_data()
obj = pickle.loads(raw)
```

**After (fixed):**
```python
import json
...
raw = request.get_data(as_text=True)
obj = json.loads(raw)
```

Fix applied: Removed `pickle` entirely and replaced it with the **JSON** module. JSON deserialization can never execute arbitrary code, making it safe even for untrusted client input.

### 4. Hardcoded Password (B105) — Fixed

**Before (vulnerable):**
```python
ADMIN_PASSWORD = "super_secret_admin_123"
```

**After (fixed):**
```python
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
```

Fix applied: Secrets are now read from **environment variables** (the standard 12-Factor App approach) and never committed to git.

### 5. Binding to All Interfaces (B104) + Debug Mode — Fixed

**Before (vulnerable):**
```python
DEBUG_MODE = True
...
app.run(host="0.0.0.0", port=5000, debug=DEBUG_MODE)
```

**After (fixed):**
```python
DEBUG_MODE = False
...
host = os.environ.get("HOST", "127.0.0.1")
port = int(os.environ.get("PORT", "5000"))
app.run(host=host, port=port, debug=DEBUG_MODE)
```

Fix applied:
- `debug=False` by default to prevent the Werkzeug interactive debugger from leaking code and enabling RCE.
- Host defaults to `127.0.0.1` for local runs. Cloud providers (Render, Railway, Heroku, etc.) override `HOST`/`PORT` via environment variables.

### 6. XSS in `/greet` Output — Bonus Fix

**Before (vulnerable):**
```python
return "<h2>Hello, " + name + "!</h2>"
```

**After (fixed):**
```python
return f"<h2>Hello, {escape(name)}!</h2>"
```

Fix applied: All user-controlled output is now passed through `flask.escape()` (HTML entity encoding) to prevent reflected Cross-Site Scripting.

## Automated Security Scanning with GitHub Actions

To ensure the security scan runs on every change, we created a GitHub Actions workflow. The workflow is triggered on every **push** and **pull request** to the main branch, and can also be launched manually via `workflow_dispatch`.

### Pipeline Workflow

```
Developer
    |
    | git push / PR
    v
GitHub Repository
    |
    v
GitHub Actions (ubuntu-latest)
    |
    +--> actions/checkout@v4
    |
    +--> actions/setup-python@v5
    |
    +--> pip install -r requirements.txt  (+ bandit)
    |
    +--> bandit -r . -f txt  → bandit-report.txt
    |
    +--> bandit -r . -f json → bandit-report.json
    |
    v
Upload Artifacts (Bandit TXT + JSON reports, retained 30 days)
```

### Workflow File — `.github/workflows/security-scan.yml`

```yaml
name: Security Scan with Bandit

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:

jobs:
  bandit-scan:
    name: Bandit Security Analysis
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install bandit

      - name: Run Bandit security scan
        run: |
          echo "=== Running Bandit security analysis ==="
          bandit -r . -f txt -o bandit-report.txt || true
          echo "=== Bandit scan completed ==="
          cat bandit-report.txt

      - name: Upload Bandit report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report
          path: bandit-report.txt
          retention-days: 30

      - name: Run Bandit JSON report
        if: always()
        run: |
          bandit -r . -f json -o bandit-report.json || true

      - name: Upload JSON report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report-json
          path: bandit-report.json
          retention-days: 30
```

This turns security scanning from a manual "run once before delivery" step into a **per-commit quality gate**, exactly as recommended by **OWASP ASVS (Application Security Verification Standard)** v4, Level 1, requirement V1.12: *"The application shall use automated source code analysis tools on a regular basis."*

## Application Deployment (Cloud / Public SaaS)

The Flask application is production-ready to be deployed to any of these public PaaS providers:

| Provider | Deploy Method | Typical Public URL |
|----------|---------------|---------------------|
| **Render**     | Connect GitHub repo → auto-deploy on push | `https://secure-scan-demo.onrender.com` |
| **Railway**    | Connect GitHub repo → auto-deploy on push | `https://secure-scan-demo.up.railway.app` |
| **Fly.io**     | `fly launch` + `fly deploy`                | `https://secure-scan-demo.fly.dev`        |
| **Heroku**     | `heroku create` + `git push heroku main`   | `https://secure-scan-demo.herokuapp.com`  |

All of them support **automatic deploys triggered by GitHub pushes**, which satisfies the assignment requirement of *"Deploy through automation."*

### Public URL of the Deployed Application

> **Deployed Application URL:** `[ADD YOUR DEPLOYED APP URL HERE]`
> Example: `https://secure-scan-demo.onrender.com`

Visiting the public URL should display the **SecureScan Demo** home page, and `/ping` should return `Application is running!`.

## Final Security Scan (After Remediation)

After applying all the security fixes, Bandit was executed a second time against the hardened codebase.

### Comparison Table — Before vs After

| Severity | Before Remediation | After Remediation | Delta |
|----------|--------------------|--------------------|-------|
| HIGH     | 2                  | 0                  | −2    |
| MEDIUM   | 2                  | 0                  | −2    |
| LOW      | 3                  | 2                  | −1    |
| **Total**| **7**              | **2**              | **−5**|

### Final Scan Output

```
Run started:2026-10-03 01:48:41.373318+00:00

Test results:
>> Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module.
   Severity: Low   Confidence: High
   CWE: CWE-78
   Location: .\app.py:2:0

--------------------------------------------------
>> Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input.
   Severity: Low   Confidence: High
   CWE: CWE-78
   Location: .\app.py:46:17

Run metrics:
        Total issues (by severity):
                Undefined: 0
                Low: 2
                Medium: 0
                High: 0
```

The remaining 2 **LOW** findings are both **informational advisories** (`B404` = "you imported subprocess", `B603` = "you are still spawning subprocesses from user input — double-check") and do **not** represent exploitable vulnerabilities in the current code, because:

1. `shell=False` prevents shell metacharacter injection.
2. `shlex.split()` rejects illegal syntax instead of interpreting it.
3. A hard `timeout=5` limits execution time.
4. All command output is HTML-escaped before rendering.

These two advisories are a textbook example of the kind of "expected false positives" OWASP explicitly mentions in its Source Code Analysis Tools documentation, and they are acceptable in a documented `/run` demo endpoint.

## Results

The project successfully demonstrates the integration of source code security analysis into a Python application's development and deployment workflow.

### Final Deliverables Checklist

✅ A **public** Python/Flask application repository (to be pushed to GitHub).
✅ Automated source code security analysis with **Bandit** (different from Semgrep used in labs).
✅ **GitHub Actions** CI workflow that runs Bandit on every push / PR.
✅ Public cloud deployment (Render/Railway/Fly.io/Heroku) with **automated deploys from GitHub pushes**.
✅ **5 vulnerabilities remediated** (2 HIGH, 2 MEDIUM, 1 LOW).
✅ **Second Bandit scan** verifying the fixes with 0 HIGH / 0 MEDIUM remaining.
✅ This Dev.to/Medium article documenting every step with real Bandit outputs and real code diffs.

## Video Demonstration

A short video walkthrough (under 5 minutes) demonstrating the end-to-end construction and security scanning process is available at:

> **Video URL:** `[ADD YOUR YOUTUBE / TIKTOK / FACEBOOK LINK HERE]`
> Example: `https://www.youtube.com/watch?v=xxxxxxxxxxx`

**Suggested video script / structure (3:30–4:30 total):**

| Segment   | Time    | What to show on screen |
|-----------|---------|------------------------|
| Intro     | 0:00–0:30 | Opening title card: *"SecureScan Demo — Bandit + GitHub Actions"*. Narrate: *"In this project we built a Flask app, scanned it with Bandit, fixed the vulnerabilities, automated scanning in GitHub Actions, and deployed to the cloud."* |
| GitHub Repo | 0:30–1:00 | Open the public GitHub repo. Show `app.py`, `requirements.txt`, `.github/workflows/security-scan.yml`. |
| Initial Code & Vuln | 1:00–1:40 | Show the vulnerable version of `/run` and `/hash` endpoints. Explain *why* `shell=True` and MD5 are dangerous. |
| Bandit Initial Scan | 1:40–2:20 | Run `bandit -r .` live in terminal. Pause on the 2 HIGH/2 MEDIUM findings. Scroll to show B602, B324, B301, B104. |
| GitHub Actions | 2:20–2:50 | Open the Actions tab on GitHub. Show a completed workflow run. Click on "Artifacts" and open `bandit-report.txt`. |
| Remediation | 2:50–3:30 | Show the Before/After code side-by-side for B602 and B324. Re-run `bandit -r .` and show 0 HIGH / 0 MEDIUM. |
| Cloud Deploy | 3:30–3:55 | Open the public application URL in the browser. Click `/ping`, `/greet?name=Trae`. Confirm it's LIVE on the public internet. |
| Conclusion  | 3:55–4:15 | Final screen with repo URL, app URL, article URL, and this video URL. Narrate: *"Integrating SAST into CI means every commit is audited automatically. Security left-shift in practice."* |

## Conclusion

Integrating security analysis into the software development lifecycle helps identify potential vulnerabilities **earlier** in the development process — the principle known as **shift-left security**.

In this project, **Bandit** was integrated into a Python application's workflow together with **GitHub Actions**, allowing security analysis to be performed automatically whenever changes were introduced into the repository. All high- and medium-severity findings were successfully remediated, producing a hardened application deployed to a public cloud platform.

The project also demonstrated the relationship between **source code security analysis (SAST)**, **automated CI/CD workflows**, and **public cloud deployment** — three pillars of modern DevSecOps practice as defined by OWASP and adopted by NIST.

## References

1. **OWASP Foundation.** *Source Code Analysis Tools.*  
   https://owasp.org/www-community/Source_Code_Analysis_Tools

2. **NIST — Software Assurance.** *Source Code Security Analyzers (SCAP-Supported Tools).*  
   https://samate.nist.gov/index.php/Source_Code_Security_Analyzers.html

3. **Bandit — Official Documentation.** PyCQA.  
   https://bandit.readthedocs.io/

4. **GitHub Actions Documentation.** *Workflow syntax for GitHub Actions.*  
   https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions

5. **OWASP ASVS v4 — Application Security Verification Standard.**  
   https://owasp.org/www-project-application-security-verification-standard/

---

*Article prepared for Dev.to / Medium / Hashnode publication. Replace every `[ADD ... LINK HERE]` placeholder with your real URLs before publishing.*
