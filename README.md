# ![Juice Shop Logo](https://raw.githubusercontent.com/juice-shop/juice-shop/master/frontend/src/assets/public/images/JuiceShop_Logo_100px.png) OWASP Juice Shop

[![OWASP Flagship](https://img.shields.io/badge/owasp-flagship%20project-48A646.svg)](https://owasp.org/projects/#sec-flagships)
[![GitHub release](https://img.shields.io/github/release/juice-shop/juice-shop.svg)](https://github.com/juice-shop/juice-shop/releases/latest)
[![Twitter Follow](https://img.shields.io/twitter/follow/owasp_juiceshop.svg?style=social&label=Follow)](https://twitter.com/owasp_juiceshop)
[![Subreddit subscribers](https://img.shields.io/reddit/subreddit-subscribers/owasp_juiceshop?style=social)](https://reddit.com/r/owasp_juiceshop)

![CI/CD Pipeline](https://github.com/juice-shop/juice-shop/workflows/CI/CD%20Pipeline/badge.svg?branch=master)
[![Test Coverage](https://api.codeclimate.com/v1/badges/6206c8f3972bcc97a033/test_coverage)](https://codeclimate.com/github/juice-shop/juice-shop/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/6206c8f3972bcc97a033/maintainability)](https://codeclimate.com/github/juice-shop/juice-shop/maintainability)
[![Code Climate technical debt](https://img.shields.io/codeclimate/tech-debt/juice-shop/juice-shop)](https://codeclimate.com/github/juice-shop/juice-shop/trends/technical_debt)
[![Cypress tests](https://img.shields.io/endpoint?url=https://dashboard.cypress.io/badge/simple/3hrkhu/master&style=flat&logo=cypress)](https://dashboard.cypress.io/projects/3hrkhu/runs)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/223/badge)](https://bestpractices.coreinfrastructure.org/projects/223)
![GitHub stars](https://img.shields.io/github/stars/juice-shop/juice-shop.svg?label=GitHub%20%E2%98%85&style=flat)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](CODE_OF_CONDUCT.md)

> [The most trustworthy online shop out there.](https://twitter.com/dschadow/status/706781693504589824)
> ([@dschadow](https://github.com/dschadow)) —
> [The best juice shop on the whole internet!](https://twitter.com/shehackspurple/status/907335357775085568)
> ([@shehackspurple](https://twitter.com/shehackspurple)) —
> [Actually the most bug-free vulnerable application in existence!](https://youtu.be/TXAztSpYpvE?t=26m35s)
> ([@vanderaj](https://twitter.com/vanderaj)) —
> [First you 😂😂then you 😢](https://twitter.com/kramse/status/1073168529405472768)
> ([@kramse](https://twitter.com/kramse)) —
> [But this doesn't have anything to do with juice.](https://twitter.com/coderPatros/status/1199268774626488320)
> ([@coderPatros' wife](https://twitter.com/coderPatros))

OWASP Juice Shop is probably the most modern and sophisticated insecure web application! It can be used in security
trainings, awareness demos, CTFs and as a guinea pig for security tools! Juice Shop encompasses vulnerabilities from the
entire
[OWASP Top Ten](https://owasp.org/www-project-top-ten) along with many other security flaws found in real-world
applications!

![Juice Shop Screenshot Slideshow](screenshots/slideshow.gif)

For a detailed introduction, full list of features and architecture overview please visit the official project page:
<https://owasp-juice.shop>

## Table of contents

- [CI Pipeline](#ci-pipeline)
- [Vulnerability Management: DefectDojo](#vulnerability-management-defectdojo)
  - [Software Composition Analysis — Retire.js](#software-composition-analysis--retirejs)
  - [Challenges Using SCA](#challenges-using-sca)
- [Setup](#setup)
    - [From Sources](#from-sources)
    - [Packaged Distributions](#packaged-distributions)
    - [Docker Container](#docker-container)
    - [Vagrant](#vagrant)
    - [Amazon EC2 Instance](#amazon-ec2-instance)
    - [Azure Container Instance](#azure-container-instance)
    - [Google Compute Engine Instance](#google-compute-engine-instance)
    - [Heroku](#heroku)
    - [Gitpod](#gitpod)
- [Demo](#demo)
- [Documentation](#documentation)
    - [Node.js version compatibility](#nodejs-version-compatibility)
    - [Troubleshooting](#troubleshooting)
    - [Official companion guide](#official-companion-guide)
- [Contributing](#contributing)
- [References](#references)
- [Merchandise](#merchandise)
- [Donations](#donations)
- [Contributors](#contributors)
- [Licensing](#licensing)

## CI Pipeline

This project implements a **DevSecOps CI pipeline** using [GitHub Actions](https://github.com/features/actions), integrating automated security controls directly into the software delivery lifecycle. The pipeline is triggered on every `git push` and orchestrates eight jobs across two execution stages:

- **Stage 1 — Parallel security scanning and test execution:** `create_cache`, `yarn_test`, `gitleaks`, `njsscan`, `semgrep`, and `retire` run concurrently, maximising feedback speed. The `retire` job performs **Software Composition Analysis (SCA)**, scanning all third-party dependencies for known CVEs.
- **Stage 2 — Gated delivery and automated reporting:** `upload_reports` automatically imports scan artefacts into DefectDojo via REST API; `build_image` builds and pushes the Docker image to the registry. Both run in parallel once Stage 1 completes.

---

### Pipeline Security Coverage

This pipeline enforces a **three-layer security model** at every code push, covering the full attack surface of a Node.js web application — from developer credentials to application logic to third-party supply chain risk. Each layer is implemented as an independent CI job using a purpose-built tool, ensuring that a failure or finding in one layer does not suppress the output of another.

---

#### Layer 1 — Hardcoded Secret Detection (Gitleaks)

**Tool:** [Gitleaks](https://github.com/gitleaks/gitleaks) | **Job:** `gitleaks` | **Output:** `gitleaks.json`

Secrets committed to source code — API keys, JWT signing secrets, database passwords, access tokens — represent one of the most critical and irreversible security failures in software development. Once pushed to a remote repository, a hardcoded secret is permanently embedded in git history and must be treated as compromised, regardless of subsequent deletion from the codebase.

The `gitleaks` job addresses this at two points in the delivery lifecycle:

**1. Pre-commit (developer workstation):**
A Gitleaks pre-commit hook is installed at `.git/hooks/pre-commit` and executes before every `git commit`. It scans the staged changeset for secret patterns — including generic API keys, private keys, AWS credentials, GitHub tokens, and JWT secrets — and blocks the commit with a non-zero exit code if any are detected. This enforces a **shift-left** control: secrets are caught before they ever reach the remote repository.

```bash
# .git/hooks/pre-commit
gitleaks detect --source . --verbose
```

**2. CI pipeline (full history scan):**
The `gitleaks` CI job runs against the full git history (`fetch-depth: 0`) using the official `zricethezav/gitleaks:latest` Docker image. This catches any secrets that bypassed the pre-commit hook — committed without the hook installed, pushed from a fork, or present in historical commits before the hook was introduced. The full-history scan is the definitive control; the pre-commit hook is the fast-feedback layer.

```
Scan scope:   Full git history (all branches, all commits)
Output:       gitleaks.json — rule ID, file path, line number, commit SHA, entropy score
Severity:     All findings are HIGH — CWE-798 (Use of Hard-coded Credentials)
Action:       continue-on-error: true — findings are reported but do not block delivery
```

**What was found:** The Gitleaks scan detected **9 active findings** in this repository — all High severity, all mapped to CWE-798. Findings include JWT signing secrets in `lib/insecurity.ts`, generic API keys in `data/static/users.yml`, and password literals in `routes/login.ts`. These are intentionally present in OWASP Juice Shop as part of its deliberate vulnerability design, and serve to validate that the scanner is working correctly against a known-vulnerable target.

---

#### Layer 2 — Application Code Security (SAST: njsscan + Semgrep)

**Tools:** [njsscan](https://github.com/ajinabraham/njsscan) + [Semgrep](https://semgrep.dev) | **Jobs:** `njsscan`, `semgrep` | **Outputs:** `results.sarif`, `semgrep.json`

Static Application Security Testing (SAST) analyses application source code without executing it, identifying insecure coding patterns, dangerous API usage, and vulnerability classes such as injection, path traversal, and authentication weaknesses. Two complementary SAST tools run in parallel to maximise rule coverage:

**njsscan — Node.js-specific SAST:**

njsscan uses a semantic grep-based engine purpose-built for Node.js and JavaScript applications. It understands Express.js routing patterns, security-sensitive APIs, and common misconfigurations in Node.js server code. Output is produced in SARIF format and uploaded to **GitHub Security Code Scanning**, making findings visible directly in the repository's Security tab alongside Dependabot alerts.

```
Scan scope:   All JavaScript/TypeScript source files in the repository
Rule engine:  Semantic grep (Node.js-aware patterns)
Output:       results.sarif → GitHub Code Scanning + njsscan.sarif pipeline artifact
Coverage:     XSS, SSRF, path traversal, insecure crypto, command injection, JWT misuse
```

**Semgrep — Multi-rule static analysis:**

Semgrep applies the `p/javascript` community ruleset — a curated set of 100+ rules covering OWASP Top 10 vulnerability classes across JavaScript and TypeScript. Rules fire on abstract syntax tree (AST) patterns rather than text matching, reducing false positives and catching vulnerabilities that span multiple lines or use indirect variable assignment.

```
Scan scope:   All JavaScript/TypeScript source files in the repository
Rule engine:  AST pattern matching (p/javascript ruleset)
Output:       semgrep.json pipeline artifact → imported into DefectDojo
Coverage:     SQL injection, open redirect, SSRF, SSTI, JWT token revocation,
              path traversal, directory listing, insecure file serving
```

**What was found:** Semgrep detected **22–23 active findings** per run, including a confirmed **CWE-89 SQL Injection** in `data/static/codefixes/dbSchemaChallenge_3.ts` (raw string concatenation into a Sequelize query — since remediated), and **17 Medium severity** Express.js misconfigurations spanning SSRF, open redirect, path traversal, insecure template rendering (SSTI precondition), and JWT tokens accepted without revocation checks. njsscan produced 0 findings, reflecting its tighter Node.js-specific rule scope against this codebase.

---

#### Layer 3 — Dependency Security / Supply Chain Risk (SCA: Retire.js)

**Tool:** [Retire.js](https://retirejs.github.io/retire.js/) | **Job:** `retire` | **Output:** `retire.json`

Modern Node.js applications depend on hundreds of third-party packages — and the security of the application is only as strong as the security of every package in its dependency tree. **Software Composition Analysis (SCA)** scans these packages against databases of known vulnerabilities, surfacing CVEs that exist not in the application's own code but in the libraries it relies on.

The `retire` job installs Retire.js globally and scans the full project directory, matching every JavaScript file and installed package against the Retire.js vulnerability database. This includes not just direct dependencies listed in `package.json`, but also **transitive dependencies** — packages that direct dependencies depend upon — which are often the source of undetected risk.

```
Scan scope:   All node_modules — direct and transitive dependencies
Database:     Retire.js curated CVE/vulnerability database (community-maintained)
Output:       retire.json — component name, version, CVE identifiers, CWE, affected range
Severity:     High and Medium findings across Lodash, jQuery, underscore.js
Action:       continue-on-error: true — findings reported but do not block delivery
```

**What was found:** Retire.js detected **23 findings** — dominated by High severity **Prototype Pollution** and **Command Injection** vulnerabilities in `lodash 2.4.2`, and a High severity **Arbitrary Code Injection** (CWE-94) in `underscore.js 1.7.0` via the `template` function (CVE-2021-23358). Medium severity findings include multiple `jQuery 2.1.x` vulnerabilities covering XSS via `parseHTML()`, CORS execution, and regex-based XSS in `htmlPrefilter`. None of these packages are imported directly by this application — all are transitive dependencies pulled in by other packages, illustrating the depth of supply chain exposure in a real-world Node.js project.

---

#### End-to-End: From Scan to Vulnerability Management

All findings from all three layers are automatically imported into **DefectDojo** on every pipeline run by the `upload_reports` job. DefectDojo provides a centralised vulnerability register with CWE taxonomy mapping, severity-based prioritisation, remediation tracking, and engagement-scoped reporting — converting raw CI scan output into an auditable, actionable risk register without any manual intervention.

```
Gitleaks  → gitleaks.json  → DefectDojo scan_type: "Gitleaks Scan"
njsscan   → njsscan.sarif  → DefectDojo scan_type: "SARIF"
Semgrep   → semgrep.json   → DefectDojo scan_type: "Semgrep JSON Report"
Retire.js → retire.json    → DefectDojo scan_type: "Retire.js Scan"

Engagement: juice-shop / release version 1.1
Total active findings: 148 | High: 68 | Medium: 79 | Low: 1
```

The `build_image` job is gated behind all scan jobs (`needs: [yarn_test, gitleaks, njsscan, semgrep]`), ensuring no Docker image is produced until the full security scan suite has completed. The Docker image is published to Docker Hub only when all upstream gates pass.

---

### Pipeline Architecture

```mermaid
flowchart TD
    DEV(["Developer Workstation"])

    DEV -->|"git commit"| HOOK["Pre-Commit Hook\n.git/hooks/pre-commit\ngitleaks detect --source /path --verbose"]
    HOOK -->|"Secrets detected — exit 1"| BLK(["Commit Blocked"])
    HOOK -->|"No secrets found"| PUSH(["git push → GitHub Actions"])

    PUSH --> CC
    PUSH --> GL
    PUSH --> NJ
    PUSH --> SG
    PUSH --> RT

    subgraph S1["Stage 1 — Parallel Security Scanning & Test Execution"]
        CC["create_cache\nnode:18-bullseye\nInstall & cache node_modules / .yarn\nCache key: yarn.lock hash"]
        CC --> YT["yarn_test\nnode:18-bullseye\nRun unit test suite"]
        GL["gitleaks\nzricethezav/gitleaks:latest\nSecret detection across full git history\ncontinue-on-error: true"]
        NJ["njsscan\najinabraham/njsscan-action@master\nNode.js SAST · SARIF output"]
        SG["semgrep\nsemgrep/semgrep · ruleset: p/javascript\nMulti-rule static analysis\ncontinue-on-error: true"]
        RT["retire\nnode:18-bullseye\nnpm install -g retire\nSCA · retire.json output\ncontinue-on-error: true"]
    end

    GL -->|"gitleaks.json · if: always()"| ART
    NJ -->|"results.sarif · if: always()"| ART
    NJ -->|"codeql-action/upload-sarif"| GCS(["GitHub Code Scanning"])
    SG -->|"semgrep.json · if: always()"| ART
    RT -->|"retire.json · if: always()"| ART

    ART[("GitHub Actions Artifact Store\n─────────────────────────────\ngitleaks-report  ~2.17 KB\nnjsscan.sarif    ~422 B\nsemgrep.json     ~8.48 KB\nretire.json      SCA findings")]

    ART --> UR
    GL --> UR
    NJ --> UR
    SG --> UR
    RT --> UR

    YT --> BI
    GL --> BI
    NJ --> BI
    SG --> BI

    subgraph S2["Stage 2 — Automated Reporting & Delivery"]
        UR["upload_reports\npython:3\nneeds: gitleaks · njsscan · semgrep · retire\ndownload-artifact × 4\nupload-report.py × 4"]
        BI["build_image\ndocker:24 + DinD\nneeds: yarn_test · gitleaks · njsscan · semgrep\ndocker build → docker push"]
    end

    UR -->|"POST /api/v2/import-scan/\nAuthorization: Token DEFECTDOJO_API_KEY\nengagement: 4 · active: true · verified: true"| DD
    BI -->|"docker push"| DH

    DD[("DefectDojo\ndemo.defectdojo.org\n─────────────────────────────\nEngagement ID 4 · release version 1.1\n148 Active Findings\nHigh: 68 · Medium: 79 · Low: 1")]
    DH[("Docker Hub\n─────────────────────────────\nndubuisip/demo-app:juice-shop-1.2")]
```

Pipeline run #70 (`security-composition-analysis` branch) — **Status: Success | Duration: 9m 7s | Artifacts: 4**. `gitleaks`, `semgrep`, and `retire` exit with non-zero codes as expected (secrets, SAST findings, and vulnerable dependencies detected), but `continue-on-error: true` ensures `upload_reports` and `build_image` proceed unblocked.

![CI Pipeline Run #70 — retire job added](screenshots/ci-retire-pipeline.png)

### Job Reference

| Job | Container / Action | Trigger Condition | Output |
|---|---|---|---|
| `create_cache` | `node:18-bullseye` | On every push | Cached `node_modules` / `.yarn` keyed to `yarn.lock` hash |
| `yarn_test` | `node:18-bullseye` | `needs: create_cache` | Test pass/fail result |
| `gitleaks` | `zricethezav/gitleaks:latest` | On every push (`continue-on-error: true`) | `gitleaks.json` uploaded as pipeline artifact |
| `njsscan` | `ajinabraham/njsscan-action@master` | On every push | `results.sarif` uploaded to GitHub Code Scanning + `njsscan.sarif` artifact |
| `semgrep` | `semgrep/semgrep` | On every push (`continue-on-error: true`) | `semgrep.json` uploaded as pipeline artifact |
| `retire` | `node:18-bullseye` | On every push (`continue-on-error: true`) | `retire.json` uploaded as pipeline artifact — SCA findings for all third-party dependencies |
| `upload_reports` | `python:3` | `needs: [gitleaks, njsscan, semgrep, retire]` | `gitleaks.json`, `njsscan.sarif`, `semgrep.json`, `retire.json` imported into DefectDojo via REST API |
| `build_image` | `docker:24` (DinD) | `needs: [yarn_test, gitleaks, njsscan, semgrep]` | `ndubuisip/demo-app:juice-shop-1.2` pushed to Docker Hub |

---

### Scan Report Artefacts

All four security scanning jobs are configured to persist their output reports as downloadable pipeline artefacts using `actions/upload-artifact@v4`. Reports are uploaded unconditionally via `if: always()`, ensuring they are retained regardless of whether the scan job passes or fails. This enables offline triage, integration with external vulnerability management platforms, and audit trail preservation beyond the GitHub Actions log retention window.

**Artefacts produced per pipeline run:**

| Artefact Name | Source Job | Format | Size | Description |
|---|---|---|---|---|
| `gitleaks-report` | `gitleaks` | JSON | ~2.17 KB | Full secret detection output including rule ID, file, line, commit, and entropy per finding |
| `njsscan.sarif` | `njsscan` | SARIF | ~422 Bytes | Node.js SAST findings in SARIF format, compatible with GitHub Code Scanning and external tooling |
| `semgrep.json` | `semgrep` | JSON | ~8.48 KB | Multi-language static analysis findings including rule metadata, severity, and affected code location |
| `retire.json` | `retire` | JSON | varies | SCA findings — all third-party dependencies scanned against Retire.js vulnerability database, with CVE identifiers, affected versions, and CWE classifications per finding |

Artefacts are accessible from the **GitHub Actions run summary → Artifacts** section and are available for download for the duration of the configured retention period.

---

### Vulnerability Management: DefectDojo

Scan artefacts produced by Gitleaks, Semgrep, njsscan, and Retire.js are automatically imported into **DefectDojo** — an open-source vulnerability management platform — on every pipeline run via a dedicated `upload_reports` CI job. This eliminates manual report handling, providing a centralised, deduplicated, and auditable vulnerability register that is updated continuously with every code push.

#### Accessing DefectDojo

**Demo Server**

Try out the demo instance at [demo.defectdojo.org](https://demo.defectdojo.org/).

Log in with: `admin / 1Defectdojo@demo#appsec`

> **Note:** The demo instance is publicly accessible and is regularly reset. Do not store sensitive or production data in the demo environment.

**Self-Hosted Quick Start**

To run DefectDojo locally using Docker:

```sh
git clone https://github.com/DefectDojo/django-DefectDojo
cd django-DefectDojo

# Build the containers
docker-compose build

# Start the stack
docker-compose up

# Retrieve the auto-generated admin password (initializer can take up to 3 minutes)
docker-compose logs initializer | grep "Admin password:"
```

Navigate to **http://localhost:8080** and log in with `admin` and the password retrieved from the initializer logs.

---

#### Automated Report Upload — `upload_reports` Job

The `upload_reports` job runs in a `python:3` container and executes only after `gitleaks`, `njsscan`, `semgrep`, and `retire` have all completed (`needs: [gitleaks, njsscan, semgrep, retire]`). It downloads the four scan artefacts from the GitHub Actions artefact store and imports each one into DefectDojo via the REST API.

**Job sequence:**

```
gitleaks ──┐
njsscan  ──┼──► upload_reports (python:3)
semgrep  ──┤         │
retire   ──┘         ├── download gitleaks-report   → gitleaks.json
                     ├── download njsscan.sarif     → njsscan.sarif
                     ├── download semgrep.json      → semgrep.json
                     ├── download retire.json       → retire.json
                     ├── pip install requests
                     ├── python3 upload-report.py gitleaks.json
                     ├── python3 upload-report.py njsscan.sarif
                     ├── python3 upload-report.py semgrep.json
                     └── python3 upload-report.py retire.json
                                  │
                                  └──► POST /api/v2/import-scan/ → DefectDojo
```

**Authentication:** The API key is stored as a GitHub repository variable (`vars.DEFECTDOJO_API_KEY`) and injected into the job environment as `DEFECTDOJO_API_KEY`. It is never hard-coded in the workflow or the upload script.

#### `upload-report.py` — Script Breakdown

The `upload-report.py` script accepts a single filename argument (`sys.argv[1]`) and maps it to the corresponding DefectDojo `scan_type` before posting to the import API:

| Input File | DefectDojo `scan_type` |
|---|---|
| `gitleaks.json` | `Gitleaks Scan` |
| `njsscan.sarif` | `SARIF` |
| `semgrep.json` | `Semgrep JSON Report` |
| `retire.json` | `Retire.js Scan` |

**API call configuration:**

```python
url  = 'https://demo.defectdojo.org/api/v2/import-scan/'

data = {
    'active':           True,
    'verified':         True,
    'scan_type':        scan_type,      # mapped from filename
    'minimum_severity': 'Low',
    'engagement':       4               # targets engagement ID 4
}
```

- `active: True` — findings are immediately marked active in the risk register
- `verified: True` — findings are pre-marked as verified, bypassing manual triage for known scanner output
- `minimum_severity: 'Low'` — all severity levels are ingested; no findings are filtered at import
- `engagement: 4` — all reports are imported into a pre-configured DefectDojo engagement, scoping findings to the correct product and release window
- A HTTP `201 Created` response confirms successful import; any other status code prints the response body for debugging

#### Engagement Findings Summary

Following a successful pipeline run, all four scan reports are imported into engagement ID 4 — **release version 1.1** — on the **juice-shop** product in DefectDojo. The engagement is scoped to a 7-day CI/CD window (15th–22nd May) and accumulates findings across multiple pipeline runs triggered by successive commits on the `security-composition-analysis` branch.

All findings are immediately marked **active and verified**, consistent with `active: True` and `verified: True` set in `upload-report.py`. With the addition of Retire.js SCA, the engagement now surfaces **148 active findings** across 13 tests from multiple pipeline runs:

| Title / Type | Date | Total Findings | Active (Verified / Fixable) | Mitigated | Duplicates |
|---|---|---|---|---|---|
| Gitleaks Scan | May 15, 2026 | 9 | 9 (9 / 0) | 0 | 0 |
| Gitleaks Scan | May 15, 2026 | 9 | 9 (9 / 0) | 0 | 0 |
| Gitleaks Scan | May 15, 2026 | 9 | 9 (9 / 0) | 0 | 0 |
| Gitleaks Scan | May 15, 2026 | 9 | 9 (9 / 0) | 0 | 0 |
| Retire.js Scan | May 15, 2026 | 23 | 23 (23 / 0) | 0 | 0 |
| Semgrep JSON Report | May 15, 2026 | 22 | 22 (22 / 0) | 0 | 0 |
| Semgrep JSON Report | May 15, 2026 | 22 | 22 (22 / 0) | 0 | 0 |
| Semgrep JSON Report | May 15, 2026 | 22 | 22 (22 / 0) | 0 | 0 |
| Semgrep JSON Report | May 15, 2026 | 23 | 23 (23 / 0) | 0 | 0 |
| nodejsscan Scan (SARIF) | May 15, 2026 | 0 | 0 (0 / 0) | 0 | 0 |

**Engagement total: 148 active findings | Critical: 0 | High: 68 | Medium: 79 | Low: 1**

> **Note on duplicate test entries:** Each pipeline run creates a new test record within the same engagement. Multiple commits on the same branch produce multiple Gitleaks Scan and Semgrep JSON Report entries. DefectDojo deduplication operates at the finding level within a test, not across tests — this is a known SCA/SAST integration challenge covered in the [Challenges using SCA](#challenges-using-sca) section below.

![DefectDojo Engagement — release version 1.1 — 148 findings](screenshots/defectdojo-engagement-retire.png)

---

#### Open Findings — CWE-798: Hardcoded Credentials (Gitleaks)

The Gitleaks import surfaced **9 active findings** within this engagement, all classified **High severity** and mapped to **CWE-798 — Use of Hard-coded Credentials**. These findings correspond to generic API keys and JWT tokens embedded directly in source files and git history — including `data/static/users.yml`, `lib/insecurity.ts`, and `routes/login.ts`.

> **CWE-798** — *Use of Hard-coded Credentials:* The software contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.

**Risk:** Hard-coded credentials in version-controlled code represent an irrecoverable secret exposure once pushed to any remote. Rotation alone is insufficient without a full git history rewrite (e.g., `git filter-repo`) to expunge the secret from all historical commits.

**Recommended remediation:**
- Migrate all secrets to environment variables or a secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager)
- Rotate all exposed keys and JWT signing secrets immediately
- Rewrite git history to purge secrets from prior commits
- Enforce gitleaks pre-commit hooks across all developer workstations to prevent recurrence

---

#### Critical Finding — CWE-89: SQL Injection (Semgrep)

Semgrep identified a **CWE-89 SQL Injection** vulnerability at **Finding ID 115**, rated **High severity**, located at `routes/search.ts` line 23.

| Field | Value |
|---|---|
| Finding ID | 115 |
| CWE | CWE-89 — Improper Neutralisation of Special Elements in SQL Commands |
| Severity | High |
| Scanner | Semgrep JSON Report |
| File | `routes/search.ts` |
| Line | 23 |
| Rule | `javascript.sequelize.security.audit.sequelize-injection-express` |

> **CWE-89** — *Improper Neutralization of Special Elements used in an SQL Command ("SQL Injection"):* The software constructs all or part of an SQL command using externally-influenced input from an upstream component, but does not neutralise or incorrectly neutralises special elements that could modify the intended SQL command when it is sent to a downstream component.

**Root cause:** The `routes/search.ts` handler passes unsanitised Express request parameters directly into a Sequelize ORM query without parameterisation — allowing an attacker to manipulate the SQL query structure, extract arbitrary data, or bypass authentication controls.

**Recommended remediation:**
- Replace raw string interpolation with Sequelize parameterised queries (`where: { col: req.query.val }`) or prepared statements
- Apply input validation and allowlisting at the route handler level
- Enforce Semgrep's `p/javascript` ruleset in CI as a mandatory blocking gate (remove `continue-on-error: true`) once the baseline findings are remediated

---

#### Remediation Applied — CWE-89 SQL Injection Fix

Following the Semgrep scan, the SQL injection vulnerability was investigated in DefectDojo. **Finding ID 148** — flagged by the `javascript.sequelize.security.audit.sequelize-injection-express.express-sequelize-injection` rule — confirmed the root cause: a Sequelize query in `data/static/codefixes/dbSchemaChallenge_3.ts` at line 11 was constructing SQL using direct string concatenation of the user-supplied `criteria` parameter.

| Field | Value |
|---|---|
| Finding ID | 148 |
| CWE | CWE-89 — Improper Neutralisation of Special Elements in SQL Commands |
| Severity | High |
| Status | Active, Verified |
| Scanner | Semgrep JSON Report |
| File | `data/static/codefixes/dbSchemaChallenge_3.ts` |
| Line | 11 |
| Rule | `javascript.sequelize.security.audit.sequelize-injection-express.express-sequelize-injection` |
| Similar Findings | 62 |

> **Semgrep description:** *Detected a Sequelize statement that is tainted by user-input. This could lead to SQL injection if the variable is user-controlled and is not properly sanitised. In order to prevent SQL injection, it is recommended to use parameterised queries or prepared statements.*

![DefectDojo — Finding 148 SQL Injection Detail](screenshots/defectdojo-sqli-finding.png)

**Vulnerable code — before fix:**

The query directly interpolated the `criteria` variable into the SQL string using string concatenation, allowing an attacker to inject arbitrary SQL through the search input:

```typescript
models.sequelize.query(
  "SELECT * FROM Products WHERE ((name LIKE '%" + criteria + "%' OR description LIKE '%" + criteria + "%') AND deletedAt IS NULL) ORDER BY name"
)
```

**Fixed code — after remediation:**

The string concatenation was replaced with a Sequelize named replacement parameter (`:searchQuery`). The `criteria` value is bound through the `replacements` object and never interpolated directly into the SQL string, eliminating the injection vector:

```typescript
models.sequelize.query(
  "SELECT * FROM Products WHERE ((name LIKE :searchQuery OR description LIKE :searchQuery) AND deletedAt IS NULL) ORDER BY name",
  {
    replacements: { searchQuery: '%' + criteria + '%' },
    type: models.Sequelize.QueryTypes.SELECT
  }
)
```

**Why this fix is effective:** Sequelize's `replacements` mechanism passes the bound value through the database driver's parameterisation layer. The SQL statement is compiled and sent to the database engine separately from the user-supplied value — the engine treats the replacement as a literal data value and not executable SQL, regardless of its content.

**Pipeline re-run post-fix:** After committing the remediation, the CI pipeline executed a second import into the DefectDojo engagement. The updated engagement view (6 tests across 2 pipeline runs) reflects the reduction — the second Semgrep JSON Report import recorded **22 active findings**, down from 23 on the initial run, confirming the patched finding was no longer detected by the rule.

| Run | Scan Type | Total Findings | Active |
|---|---|---|---|
| Run 1 (pre-fix) | Gitleaks Scan | 9 | 9 (9/0) |
| Run 1 (pre-fix) | Semgrep JSON Report | 23 | 23 (23/0) |
| Run 1 (pre-fix) | nodejsscan Scan (SARIF) | 0 | 0 (0/0) |
| Run 2 (post-fix) | Gitleaks Scan | 9 | 9 (9/0) |
| Run 2 (post-fix) | Semgrep JSON Report | 22 | 22 (22/0) |
| Run 2 (post-fix) | nodejsscan Scan (SARIF) | 0 | 0 (0/0) |

**Engagement total after both runs: 63 active findings | Critical: 0 | High: 29 | Medium: 34 | Low: 0**

![DefectDojo — Engagement Post-Fix Re-Run](screenshots/defectdojo-engagement-post-fix.png)

---

#### Medium Severity Findings — Express.js Security Misconfigurations (Semgrep)

Beyond the critical SQL Injection finding, Semgrep's `p/javascript` ruleset flagged **17 Medium severity** findings across the Express.js application layer. All findings originate from the **Semgrep JSON Report** import.

These findings represent a class of application-layer misconfigurations commonly exploited in Express.js APIs — each mapped to a specific Semgrep rule and line reference in the codebase:

| Semgrep Rule | Vulnerability Class | Affected Lines |
|---|---|---|
| `javascript.express.security.audit.express-res-sendfile` | Insecure file serving via `res.sendFile()` without root restriction | 73 |
| `javascript.express.security.audit.express-path-join-resolve` | Path traversal via unsanitised `path.join()` / `path.resolve()` | 22 |
| `javascript.express.security.audit.express-check-directory-listings` | Directory listing exposure | 548 |
| `javascript.express.security.audit.express-ssrf` | Server-Side Request Forgery (SSRF) in Express route handlers | 918 |
| `javascript.express.security.express-insecure-template-usage` | Insecure template rendering (potential SSTI) | 1336 |
| `javascript.express.security.audit.express-open-redirect` | Open redirect via unvalidated user-supplied URL | 601 |
| `javascript.express.security.audit.express-jwt-not-revoked` | JWT tokens accepted without revocation check | 522 |

**Key observations:**
- Multiple rules fire across repeated code patterns (e.g., `express-res-sendfile` and `express-path-join-resolve` appear at the same lines across several route files), indicating systemic misuse of Express primitives rather than isolated incidents.
- `express-jwt-not-revoked` at line 522 indicates that issued JWT tokens remain valid indefinitely — there is no server-side token blacklist or revocation mechanism, which is a known authentication bypass risk.
- `express-ssrf` at line 918 suggests that user-controlled input influences outbound HTTP requests, potentially enabling attackers to proxy requests to internal services or cloud metadata endpoints.
- `express-insecure-template-usage` at line 1336 indicates user-controlled data is rendered via a template engine without sanitisation — a prerequisite condition for Server-Side Template Injection (SSTI).

---

#### Software Composition Analysis — Retire.js

The `retire` job integrates **Retire.js** into the CI pipeline as a dedicated **Software Composition Analysis (SCA)** tool. Unlike SAST tools (njsscan, semgrep) that analyse custom application code, SCA focuses entirely on **third-party dependencies** — scanning every package in `node_modules` against Retire.js's curated database of known vulnerabilities indexed by CVE identifier.

**How the job runs:**

```yaml
retire:
  runs-on: ubuntu-latest
  continue-on-error: true
  container: node:18-bullseye
  steps:
    - uses: actions/checkout@v4
    - uses: actions/cache@v4          # restore cached node_modules
    - run: npm install -g retire
    - run: retire --path . --outputformat json --outputpath retire.json
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: retire.json
        path: retire.json
```

Retire.js scans the project directory recursively, matching all JavaScript files and installed packages against its vulnerability signatures. The `--outputformat json` flag produces structured output suitable for automated ingestion into DefectDojo.

#### Retire.js Findings — SCA Results

The Retire.js scan surfaced **23 findings** across the dependency tree, dominated by **High severity** vulnerabilities in widely-used packages present as transitive dependencies:

**Representative High severity findings:**

| Vulnerability | Package | Version | CVE | CWE |
|---|---|---|---|---|
| Prototype Pollution | `lodash` | 2.4.2 | multiple | CWE-1035 |
| Command Injection | `lodash` | 2.4.2 | multiple | CWE-1035 |
| Arbitrary Code Injection via template function | `underscore.js` | 1.7.0 | CVE-2021-23358 | CWE-94 |

**Representative Medium severity findings:**

| Vulnerability | Package | Version | CVE | CWE |
|---|---|---|---|---|
| Prototype Pollution | `lodash` | 2.4.2 (various) | multiple | CWE-1035 |
| `parseHTML()` Executes Scripts in Event Handlers | `jquery` | 2.1.x | multiple | CWE-1035 |
| 3rd Party CORS Request May Execute | `jquery` | 2.1.0 | multiple | CWE-1035 |
| `jQuery.before 3.4.0` used in Drupal, Backdrop CMS | `jquery` | 2.1.x | multiple | CWE-1035 |
| Regex in `jQuery.htmlPrefilter` May Introduce XSS | `jquery` | 2.1.x | multiple | CWE-1035 |

**Key finding — underscore.js 1.7.0 (CVE-2021-23358 / CWE-94):**

Finding ID 263 is a representative Retire.js result showing the depth of transitive dependency risk. The vulnerable file is `node_modules/fast.js/dist/bench.js` — a file not written by this project, in a dependency of a dependency. `underscore.js 1.7.0` (vulnerable: `>=1.3.2 <1.12.1`) is bundled by `fast.js` and exposes an **Arbitrary Code Injection** vector via its `template` function (CWE-94 — Code Injection).

| Field | Value |
|---|---|
| Finding ID | 263 |
| Severity | High |
| Component | `underscore.js` 1.7.0 |
| Location | `node_modules/fast.js/dist/bench.js` |
| CVE | CVE-2021-23358 |
| CWE | CWE-94 — Improper Control of Generation of Code |
| GHSA | GHSA-cf4h-3jhx-xvhq |
| Vulnerable range | `>=1.3.2 <1.12.1` |
| Scanner | Retire.js Scan |

> **CWE-94** — *Improper Control of Generation of Code ("Code Injection"): The software constructs all or part of a code segment using externally-influenced input from an upstream component, but it does not neutralise or incorrectly neutralises special elements that could modify the syntax or behaviour of the intended code segment.*

**Recommended remediation:**
- Update `lodash` to `>=4.17.21` where it appears as a direct or transitive dependency
- Update `jquery` to `>=3.5.0`
- Upgrade `fast.js` to a version that bundles `underscore.js >=1.12.1`, or replace with a maintained alternative
- Run `npm audit fix` or `yarn upgrade` to pull in patched versions of transitive dependencies
- Pin dependency version ranges in `package.json` to prevent silent upgrades to vulnerable versions

![DefectDojo — Retire.js findings list (Lodash, jQuery, underscore.js)](screenshots/defectdojo-retire-findings-list.png)

![DefectDojo — Finding 263 underscore.js CWE-94 detail](screenshots/defectdojo-retire-finding-263.png)

---

#### Challenges Using SCA

Integrating Software Composition Analysis into a CI pipeline using Retire.js and DefectDojo exposed several practical challenges that are common across SCA implementations:

**1. Transitive dependency noise**

The majority of Retire.js findings originate from **transitive dependencies** — packages that the application does not import directly but which are pulled in by direct dependencies. `lodash 2.4.2` and `underscore.js 1.7.0` are not in `package.json`; they are bundled by other packages. This makes remediation indirect: the fix requires upgrading the parent package, which may introduce breaking changes, or waiting for the upstream maintainer to patch their bundled dependency.

**2. False positives from benchmark and test files**

The `underscore.js` finding at `node_modules/fast.js/dist/bench.js` is a benchmark file — code that is never executed in production and exists purely for performance testing of the `fast.js` library. Retire.js cannot distinguish between production bundle files and development/test/benchmark artefacts within `node_modules`, producing findings for files that pose no runtime risk to deployed users. Without suppression rules or path-based exclusions, the noise obscures genuinely exploitable vulnerabilities.

**3. No EPSS score or exploit availability data**

Retire.js reports CVE identifiers and CWE classifications, but provides no **EPSS (Exploit Prediction Scoring System)** percentile or evidence of active exploitation. As seen in the DefectDojo findings view, the EPSS Score and EPSS Percentile columns show `N.A.` for all Retire.js findings. This makes it difficult to prioritise — a critical CVE with no known exploit may be less urgent than a medium CVE that is actively weaponised in the wild.

**4. Duplicate findings across pipeline runs**

Because `upload_reports` posts to DefectDojo's `/api/v2/import-scan/` endpoint on every push, each pipeline run creates a new **test record** within the same engagement. DefectDojo's deduplication engine merges identical findings *within* a test but not across tests from separate runs. After multiple commits on the `security-composition-analysis` branch, the engagement accumulated 13 test entries (4 × Gitleaks, 4 × Semgrep, 4 × Retire.js, 1 × nodejsscan), inflating the total finding count from the true 23 unique SCA findings to a cumulative 148. Mitigation strategies include using DefectDojo's `reimport-scan` endpoint instead of `import-scan` for subsequent runs, or scoping each engagement to a single pipeline run.

**5. Retire.js database coverage gaps**

Retire.js's vulnerability database is community-maintained and focused on JavaScript packages. Vulnerabilities that have not yet been indexed (zero-days, newly disclosed CVEs with no Retire.js entry) will not be detected. Complementing Retire.js with `npm audit` or a commercial SCA tool (e.g., Snyk, Dependabot) improves coverage, particularly for the npm ecosystem's own advisory database.

**6. Version range ambiguity**

Retire.js matches packages by name and version against ranges such as `>=1.3.2 <1.12.1`. When multiple versions of the same package exist in the dependency tree (common in large projects), each version is evaluated independently. A project may appear partially patched — one consumer of `lodash` upgraded, another still on a vulnerable version — producing repeated findings for the same CVE across different paths in `node_modules`.

**7. CI gate configuration**

`continue-on-error: true` is set on the `retire` job to prevent SCA findings from blocking the pipeline. This is a pragmatic decision when introducing SCA for the first time against a project with an established vulnerability baseline. However, it means the pipeline reports overall success even when high-severity dependency vulnerabilities are present. A mature SCA gate would enforce a severity threshold (e.g., fail on Critical or weaponised High CVEs) once the baseline is triaged and suppressed.

---

#### DefectDojo Integration Value

| Capability | Benefit |
|---|---|
| **Centralised risk register** | All findings from Gitleaks, Semgrep, and njsscan consolidated in a single auditable dashboard |
| **CWE classification** | Automatic mapping to MITRE CWE taxonomy enables prioritisation by vulnerability class |
| **Deduplication** | Repeated findings across scan runs are merged, reducing alert fatigue |
| **Remediation tracking** | Findings can be assigned, dated, and closed with evidence — supporting compliance workflows |
| **Engagement scoping** | Findings are bounded to a release window, providing a point-in-time security posture snapshot for each delivery |

---


### Security Architecture Summary

| Principle | Implementation |
|---|---|
| **Shift Left** | Pre-commit hook and parallel CI scans intercept vulnerabilities before code reaches production |
| **Defence in Depth** | Four independent security tools (`gitleaks`, `njsscan`, `semgrep`, `retire`) cover distinct vulnerability classes: secrets, SAST, multi-rule static analysis, and SCA |
| **Software Composition Analysis** | `retire` scans all third-party dependencies against the Retire.js CVE database on every push, surfacing known vulnerabilities in the full dependency tree including transitive packages |
| **Gated Delivery** | `build_image` is blocked until all scan and test jobs complete (`needs: [yarn_test, gitleaks, njsscan, semgrep]`) |
| **Automated Reporting** | `upload_reports` pushes all four scan artefacts to DefectDojo on every run, eliminating manual import and ensuring findings are immediately visible in the risk register |
| **Audit Trail** | SARIF reports from `njsscan` are uploaded to GitHub Security Code Scanning; all four reports are preserved as pipeline artefacts and imported into DefectDojo |
| **Reproducibility** | All jobs execute in isolated, purpose-built containers, eliminating environment drift across pipeline runs |
| **Build Efficiency** | Dependency caching in `create_cache` keyed to `yarn.lock` eliminates redundant installs across downstream jobs |

---

## Setup

> You can find some less common installation variations in
> [the _Running OWASP Juice Shop_ documentation](https://pwning.owasp-juice.shop/part1/running.html).

### From Sources

![GitHub repo size](https://img.shields.io/github/repo-size/juice-shop/juice-shop.svg)

1. Install [node.js](#nodejs-version-compatibility)
2. Run `git clone https://github.com/juice-shop/juice-shop.git --depth 1` (or
   clone [your own fork](https://github.com/juice-shop/juice-shop/fork)
   of the repository)
3. Go into the cloned folder with `cd juice-shop`
4. Run `npm install` (only has to be done before first start or when you change the source code)
5. Run `npm start`
6. Browse to <http://localhost:3000>

### Packaged Distributions

[![GitHub release](https://img.shields.io/github/downloads/juice-shop/juice-shop/total.svg)](https://github.com/juice-shop/juice-shop/releases/latest)
[![SourceForge](https://img.shields.io/sourceforge/dm/juice-shop?label=sourceforge%20downloads)](https://sourceforge.net/projects/juice-shop/)
[![SourceForge](https://img.shields.io/sourceforge/dt/juice-shop?label=sourceforge%20downloads)](https://sourceforge.net/projects/juice-shop/)

1. Install a 64bit [node.js](#nodejs-version-compatibility) on your Windows, MacOS or Linux machine
2. Download `juice-shop-<version>_<node-version>_<os>_x64.zip` (or
   `.tgz`) attached to
   [latest release](https://github.com/juice-shop/juice-shop/releases/latest)
3. Unpack and `cd` into the unpacked folder
4. Run `npm start`
5. Browse to <http://localhost:3000>

> Each packaged distribution includes some binaries for `sqlite3` and
> `libxmljs` bound to the OS and node.js version which `npm install` was
> executed on.

### Docker Container

[![Docker Pulls](https://img.shields.io/docker/pulls/bkimminich/juice-shop.svg)](https://hub.docker.com/r/bkimminich/juice-shop)
![Docker Stars](https://img.shields.io/docker/stars/bkimminich/juice-shop.svg)
[![](https://images.microbadger.com/badges/image/bkimminich/juice-shop.svg)](https://microbadger.com/images/bkimminich/juice-shop
"Get your own image badge on microbadger.com")
[![](https://images.microbadger.com/badges/version/bkimminich/juice-shop.svg)](https://microbadger.com/images/bkimminich/juice-shop
"Get your own version badge on microbadger.com")

1. Install [Docker](https://www.docker.com)
2. Run `docker pull bkimminich/juice-shop`
3. Run `docker run --rm -p 3000:3000 bkimminich/juice-shop`
4. Browse to <http://localhost:3000> (on macOS and Windows browse to
   <http://192.168.99.100:3000> if you are using docker-machine instead of the native docker installation)

### Vagrant

1. Install [Vagrant](https://www.vagrantup.com/downloads.html) and
   [Virtualbox](https://www.virtualbox.org/wiki/Downloads)
2. Run `git clone https://github.com/juice-shop/juice-shop.git` (or
   clone [your own fork](https://github.com/juice-shop/juice-shop/fork)
   of the repository)
3. Run `cd vagrant && vagrant up`
4. Browse to [192.168.56.110](http://192.168.56.110)

### Amazon EC2 Instance

1. In the _EC2_ sidenav select _Instances_ and click _Launch Instance_
2. In _Step 1: Choose an Amazon Machine Image (AMI)_ choose an _Amazon Linux AMI_ or _Amazon Linux 2 AMI_
3. In _Step 3: Configure Instance Details_ unfold _Advanced Details_ and copy the script below into _User Data_
4. In _Step 6: Configure Security Group_ add a _Rule_ that opens port 80 for HTTP
5. Launch your instance
6. Browse to your instance's public DNS

```
#!/bin/bash
yum update -y
yum install -y docker
service docker start
docker pull bkimminich/juice-shop
docker run -d -p 80:3000 bkimminich/juice-shop
```

### Azure Container Instance

1. Open and login (via `az login`) to your
   [Azure CLI](https://azure.github.io/projects/clis/) **or** login to the [Azure Portal](https://portal.azure.com),
   open the _CloudShell_
   and then choose _Bash_ (not PowerShell).
2. Create a resource group by running `az group create --name <group name> --location <location name, e.g. "centralus">`
3. Create a new container by
   running `az container create --resource-group <group name> --name <container name> --image bkimminich/juice-shop --dns-name-label <dns name label> --ports 3000 --ip-address public`
4. Your container will be available at `http://<dns name label>.<location name>.azurecontainer.io:3000`

### Google Compute Engine Instance

1. Login to the Google Cloud Console and
   [open Cloud Shell](https://console.cloud.google.com/home/dashboard?cloudshell=true).
2. Launch a new GCE instance based on the juice-shop container. Take note of the `EXTERNAL_IP` provided in the output.

```
gcloud compute instances create-with-container owasp-juice-shop-app --container-image bkimminich/juice-shop
```

3. Create a firewall rule that allows inbound traffic to port 3000

```
gcloud compute firewall-rules create juice-rule --allow tcp:3000
```

4. Your container is now running and available at
   `http://<EXTERNAL_IP>:3000/`

### Heroku

1. [Sign up to Heroku](https://signup.heroku.com/) and
   [log in to your account](https://id.heroku.com/login)
2. Click the button below and follow the instructions

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

If you have forked the Juice Shop repository on GitHub, the _Deploy to
Heroku_ button will deploy your forked version of the application.

### Gitpod 

1. Login to [gitpod.io](https://gitpod.io) and use <https://gitpod.io/#https://github.com/juice-shop/juice-shop/> to start a new workspace. If you want to spin up a forked repository, your URL needs to be adjusted accordingly.

2. After the Gitpod workspace is loaded, Gitpod tasks is still running to install `npm install`  and launch the website. Despite Gitpod showing your workspace state already as _Running_, you need to wait until the installation process is done, before the website becomes accessable. The _Open Preview Window (Internal Browser)_, will open automatically and refresh itself automatically when the server has started.

3. Your Juice Shop instance is now also available at `https://3000-<GITPOD_WORKSPACE_ID>.<GITPOD_HOSTING_ZONE>.gitpod.io`.

## Demo

Feel free to have a look at the latest version of OWASP Juice Shop:
<http://demo.owasp-juice.shop>

> This is a deployment-test and sneak-peek instance only! You are __not
> supposed__ to use this instance for your own hacking endeavours! No
> guaranteed uptime! Guaranteed stern looks if you break it!

## Documentation

### Node.js version compatibility

![GitHub package.json dynamic](https://img.shields.io/github/package-json/cpu/bkimminich/juice-shop)
![GitHub package.json dynamic](https://img.shields.io/github/package-json/os/bkimminich/juice-shop)

OWASP Juice Shop officially supports the following versions of
[node.js](http://nodejs.org) in line with the official
[node.js LTS schedule](https://github.com/nodejs/LTS) as close as possible. Docker images and packaged distributions are
offered accordingly.

| node.js | Supported            | Tested             | [Packaged Distributions](#packaged-distributions) | [Docker images](#docker-container) from `master` | [Docker images](#docker-container) from `develop` |
|:--------|:---------------------|:-------------------|:--------------------------------------------------|:-------------------------------------------------|:--------------------------------------------------|
| 20.x    | :x:                  | :x:                |                                                   |                                                  |                                                   |
| 19.x    | (:heavy_check_mark:) | :heavy_check_mark: |                                                   |                                                  |                                                   |
| 18.x    | :heavy_check_mark:   | :heavy_check_mark: | Windows (`x64`), MacOS (`x64`), Linux (`x64`)     | `latest` (`linux/amd64`, `linux/arm64`)          | `snapshot` (`linux/amd64`, `linux/arm64`)         |
| 17.x    | (:heavy_check_mark:) | :x:                |                                                   |                                                  |                                                   |
| 16.x    | :heavy_check_mark:   | :heavy_check_mark: | Windows (`x64`), MacOS (`x64`), Linux (`x64`)     |                                                  |                                                   |
| 15.x    | (:heavy_check_mark:) | :x:                |                                                   |                                                  |                                                   |
| 14.x    | :heavy_check_mark:   | :heavy_check_mark: | Windows (`x64`), MacOS (`x64`), Linux (`x64`)     |                                                  | `                                                 |
| <14.x   | :x:                  | :x:                |                                                   |                                                  |                                                   |

Juice Shop is automatically tested _only on the latest `.x` minor version_ of each node.js version mentioned above!
There is no guarantee that older minor node.js releases will always work with Juice Shop!
Please make sure you stay up to date with your chosen version.

### Troubleshooting

[![Gitter](http://img.shields.io/badge/gitter-join%20chat-1dce73.svg)](https://gitter.im/bkimminich/juice-shop)

If you need help with the application setup please check our
[our existing _Troubleshooting_](https://pwning.owasp-juice.shop/appendix/troubleshooting.html)
guide. If this does not solve your issue please post your specific problem or question in the
[Gitter Chat](https://gitter.im/bkimminich/juice-shop) where community members can best try to help you.

:stop_sign: **Please avoid opening GitHub issues for support requests or questions!**

### Official companion guide

[![Write Goodreads Review](https://img.shields.io/badge/goodreads-write%20review-49557240.svg)](https://www.goodreads.com/review/edit/49557240)

OWASP Juice Shop comes with an official companion guide eBook. It will give you a complete overview of all
vulnerabilities found in the application including hints how to spot and exploit them. In the appendix you will even
find complete step-by-step solutions to every challenge. Extensive documentation of
[custom re-branding](https://pwning.owasp-juice.shop/part1/customization.html),
[CTF-support](https://pwning.owasp-juice.shop/part1/ctf.html),
[trainer's guide](https://pwning.owasp-juice.shop/appendix/trainers.html)
and much more is also included.

[Pwning OWASP Juice Shop](https://leanpub.com/juice-shop) is published under
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)
and is available **for free** in PDF, Kindle and ePub format on LeanPub. You can also
[browse the full content online](https://pwning.owasp-juice.shop)!

[![Pwning OWASP Juice Shop Cover](https://raw.githubusercontent.com/bkimminich/pwning-juice-shop/master/cover_small.jpg)](https://leanpub.com/juice-shop)

## Contributing

[![GitHub contributors](https://img.shields.io/github/contributors/bkimminich/juice-shop.svg)](https://github.com/bkimminich/juice-shop/graphs/contributors)
[![JavaScript Style Guide](https://img.shields.io/badge/code%20style-standard-brightgreen.svg)](http://standardjs.com/)
[![Crowdin](https://d322cqt584bo4o.cloudfront.net/owasp-juice-shop/localized.svg)](https://crowdin.com/project/owasp-juice-shop)
![GitHub issues by-label](https://img.shields.io/github/issues/bkimminich/juice-shop/help%20wanted.svg)
![GitHub issues by-label](https://img.shields.io/github/issues/bkimminich/juice-shop/good%20first%20issue.svg)

We are always happy to get new contributors on board! Please check
[CONTRIBUTING.md](CONTRIBUTING.md) to learn how to
[contribute to our codebase](CONTRIBUTING.md#code-contributions) or the
[translation into different languages](CONTRIBUTING.md#i18n-contributions)!

## References

Did you write a blog post, magazine article or do a podcast about or mentioning OWASP Juice Shop? Or maybe you held or
joined a conference talk or meetup session, a hacking workshop or public training where this project was mentioned?

Add it to our ever-growing list of [REFERENCES.md](REFERENCES.md) by forking and opening a Pull Request!

## Merchandise

* On [Spreadshirt.com](http://shop.spreadshirt.com/juiceshop) and
  [Spreadshirt.de](http://shop.spreadshirt.de/juiceshop) you can get some swag (Shirts, Hoodies, Mugs) with the official
  OWASP Juice Shop logo
* On
  [StickerYou.com](https://www.stickeryou.com/products/owasp-juice-shop/794)
  you can get variants of the OWASP Juice Shop logo as single stickers to decorate your laptop with. They can also print
  magnets, iron-ons, sticker sheets and temporary tattoos.

The most honorable way to get some stickers is to
[contribute to the project](https://pwning.owasp-juice.shop/part3/contribution.html)
by fixing an issue, finding a serious bug or submitting a good idea for a new challenge!

We're also happy to supply you with stickers if you organize a meetup or conference talk where you use or talk about or
hack the OWASP Juice Shop! Just
[contact the mailing list](mailto:owasp_juice_shop_project@lists.owasp.org)
or [the project leader](mailto:bjoern.kimminich@owasp.org) to discuss your plans!

## Donations

[![](https://img.shields.io/badge/support-owasp%20juice%20shop-blue)](https://owasp.org/donate/?reponame=www-project-juice-shop&title=OWASP+Juice+Shop)

The OWASP Foundation gratefully accepts donations via Stripe. Projects such as Juice Shop can then request reimbursement
for expenses from the Foundation. If you'd like to express your support of the Juice Shop project, please make sure to
tick the "Publicly list me as a supporter of OWASP Juice Shop" checkbox on the donation form. You can find our more
about donations and how they are used here:

<https://pwning.owasp-juice.shop/part3/donations.html>

## Contributors

The OWASP Juice Shop core project team are:

- [Björn Kimminich](https://github.com/bkimminich) aka `bkimminich`
  ([Project Leader](https://www.owasp.org/index.php/Projects/Project_Leader_Responsibilities))
  [![Keybase PGP](https://img.shields.io/keybase/pgp/bkimminich)](https://keybase.io/bkimminich)
- [Jannik Hollenbach](https://github.com/J12934) aka `J12934`
- [Timo Pagel](https://github.com/wurstbrot) aka `wurstbrot`
- [Shubham Palriwala](https://github.com/ShubhamPalriwala) aka `ShubhamPalriwala`

For a list of all contributors to the OWASP Juice Shop please visit our
[HALL_OF_FAME.md](HALL_OF_FAME.md).

## Licensing

[![license](https://img.shields.io/github/license/bkimminich/juice-shop.svg)](LICENSE)

This program is free software: you can redistribute it and/or modify it under the terms of the [MIT license](LICENSE).
OWASP Juice Shop and any contributions are Copyright © by Bjoern Kimminich & the OWASP Juice Shop contributors
2014-2023.

![Juice Shop Logo](https://raw.githubusercontent.com/bkimminich/juice-shop/master/frontend/src/assets/public/images/JuiceShop_Logo_400px.png)
