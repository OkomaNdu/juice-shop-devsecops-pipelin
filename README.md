<h1 align="center">Juice Shop &mdash; DevSecOps CI/CD Pipeline</h1>

<p align="center">
  <em>An end-to-end, production-style CI/CD pipeline that builds, security-scans, and ships
  the OWASP Juice Shop vulnerable application from GitHub to a live AWS EC2 instance on every commit.</em>
</p>

<p align="center">
  <img alt="AWS"             src="https://img.shields.io/badge/AWS-EC2%20%7C%20ECR%20%7C%20IAM-FF9900?logo=amazonaws&logoColor=white">
  <img alt="GitHub Actions"  src="https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white">
  <img alt="Docker"          src="https://img.shields.io/badge/Docker-Multi--stage%20Build-2496ED?logo=docker&logoColor=white">
  <img alt="Ubuntu"          src="https://img.shields.io/badge/Ubuntu%2026.04-Self--hosted%20Runner-E95420?logo=ubuntu&logoColor=white">
  <img alt="Node.js"         src="https://img.shields.io/badge/Node.js-18.x-339933?logo=nodedotjs&logoColor=white">
  <br>
  <img alt="gitleaks"        src="https://img.shields.io/badge/gitleaks-Secrets%20Scanning-red">
  <img alt="njsscan"         src="https://img.shields.io/badge/njsscan-SAST%20%28Node.js%29-blueviolet">
  <img alt="semgrep"         src="https://img.shields.io/badge/semgrep-SAST-1B66CD?logo=semgrep&logoColor=white">
  <img alt="retire.js"       src="https://img.shields.io/badge/retire.js-SCA-orange">
  <img alt="DefectDojo"      src="https://img.shields.io/badge/DefectDojo-Vulnerability%20Mgmt-d62728">
</p>

---

## Overview

This repository delivers a fully automated DevSecOps pipeline for the
[OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) application.
Every push to GitHub triggers an 8-stage workflow that runs unit tests,
executes five independent security gates (secrets, two SAST engines, and a
software-composition scan), builds a Docker image on a self-hosted runner,
publishes it to a private Amazon ECR registry, and performs a zero-touch
SSH-based rolling deployment to a target EC2 instance.

The pipeline is engineered around three production-grade concerns:

- **Speed** &mdash; registry-based Docker layer caching, a shared `yarn`
  cache, and a self-hosted runner cut end-to-end execution time from
  **15&nbsp;m&nbsp;7&nbsp;s** to **4&nbsp;m&nbsp;44&nbsp;s** on re-runs
  (≈&nbsp;70&nbsp;% reduction; the `build_image` stage alone drops from
  10&nbsp;m&nbsp;44&nbsp;s → 8&nbsp;s).
- **Security** &mdash; five scanners run in parallel; each uploads its raw
  report as a workflow artifact and is configurable as either *blocking* or
  *report-only*, ready to be forwarded into DefectDojo for centralised
  triage.
- **Reproducibility** &mdash; every image is dual-tagged with its commit
  SHA and `:latest`, giving an auditable, rollback-ready history in ECR.

## Architecture

```text
                 ┌──────────────┐       ┌─────────────────────────────────────────┐
                 │  Developer   │       │           GitHub Actions (8 jobs)       │
                 │   git push   │──────►│                                         │
                 └──────────────┘       │  create_cache ──► yarn_test             │
                                        │              │──► gitleaks  (secrets)   │
                                        │              │──► njsscan   (SAST)      │
                                        │              │──► semgrep   (SAST)      │
                                        │              │──► retire    (SCA)       │
                                        │              ▼                          │
                                        │      ┌─────────────────────┐            │
                                        │      │    build_image      │            │
                                        │      │  (self-hosted EC2)  │            │
                                        │      └─────────┬───────────┘            │
                                        └────────────────┼────────────────────────┘
                                                         │ docker push :sha + :latest
                                                         ▼
                                              ┌──────────────────────┐
                                              │  Amazon ECR (priv.)  │
                                              │ juice-shop repository│
                                              └──────────┬───────────┘
                                                         │ docker pull :latest (SSH)
                                                         ▼
                                              ┌──────────────────────┐
                                              │   juice-app-server   │
                                              │  Ubuntu 26.04 / EC2  │
                                              │   :3000 → browser    │
                                              └──────────────────────┘
```

## At a Glance

| Capability                 | Implementation                                                                                            |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| **Pipeline orchestration** | GitHub Actions, 8 jobs, fan-out / fan-in DAG, dual `ubuntu-latest` + self-hosted runner topology          |
| **Secrets scanning**       | `gitleaks` against full git history (`fetch-depth: 0`)                                                    |
| **SAST**                   | `njsscan` (Node-specific, SARIF → GitHub Code Scanning) + `semgrep` (`p/javascript` ruleset)              |
| **Dependency scanning**    | `retire.js` against `node_modules`                                                                        |
| **Test execution**         | `yarn test` (Juice Shop unit suite) gated before image build                                              |
| **Image registry**         | Private Amazon ECR repository, dual-tagged `:${{ github.sha }}` + `:latest`                               |
| **Caching strategy**       | (1) `actions/cache` for `node_modules` / `.yarn` keyed on `yarn.lock`, (2) registry-based Docker BuildKit |
| **Deployment**             | SSH-driven `docker pull` → `docker rm` → `docker run` on a `t2.micro` Ubuntu EC2 host                     |
| **Infrastructure**         | 2 × Ubuntu 26.04 EC2 instances (app + self-hosted runner), least-privilege Security Groups                |
| **Secrets management**     | GitHub Actions repository secrets for AWS keys + SSH private key; no plaintext credentials in the repo    |

## Live Deployment

Once the pipeline succeeds, the application is served from a containerised
distroless Node.js image on a dedicated EC2 instance:

> :globe_with_meridians: **`http://3.17.39.163:3000/`**

![Juice Shop catalog served from the EC2 application host on port 3000](screenshots/juice-shop-running.png)

## Repository Layout

```text
.
├── .github/workflows/ci.yml      ← 8-stage CI/CD pipeline definition
├── Dockerfile                    ← Multi-stage build, distroless runtime
├── screenshots/                  ← Pipeline run + deployment evidence
├── frontend/                     ← Juice Shop Angular UI (upstream)
├── routes/, models/, lib/        ← Juice Shop Node.js backend (upstream)
└── README.md                     ← Project documentation (this file)
```

## Table of Contents

**DevSecOps Pipeline**

- [CI Pipeline](#ci-pipeline)
  - [Pipeline Jobs](#pipeline-jobs)
  - [Building and Pushing the Image to AWS ECR](#building-and-pushing-the-image-to-aws-ecr)
- [Release Deployment](#release-deployment)
  - [Provisioning the Application EC2 Instance (`juice-app-server`)](#provisioning-the-application-ec2-instance-juice-app-server)
  - [Installing Docker and the AWS CLI](#installing-docker-and-the-aws-cli)
  - [Authenticating to Amazon ECR](#authenticating-to-amazon-ecr)
  - [Verifying the Deployed Container](#verifying-the-deployed-container)
- [Self-Hosted GitHub Actions Runner](#self-hosted-github-actions-runner)
  - [Provisioning the Runner EC2 Instance (`self-hosted-runner`)](#provisioning-the-runner-ec2-instance-self-hosted-runner)
  - [Registering the Runner with GitHub](#registering-the-runner-with-github)
  - [Installing Build Tooling on the Runner](#installing-build-tooling-on-the-runner)
  - [Running the Runner as a Service](#running-the-runner-as-a-service)
  - [Runner Image Cache & Disk Hygiene](#runner-image-cache--disk-hygiene)

**About the Application Under Test**

- [OWASP Juice Shop](#owasp-juice-shop)
- [Setup](#setup) · [Demo](#demo) · [Documentation](#documentation)
- [Contributing](#contributing) · [References](#references) · [Licensing](#licensing)

---

## CI Pipeline

The pipeline is defined in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) and triggers on
every `push`. It is organised as a fan-out of independent quality and
security gates after a shared dependency-cache stage, followed by a
sequential build-and-release fan-in:

```text
                 ┌─► yarn_test ─┐
                 ├─► gitleaks ──┤
 create_cache ──►┼─► njsscan ───┼──► build_image ──► deploy_image
                 ├─► semgrep ───┤
                 └─► retire ────┘
```

### Pipeline Jobs

Each job runs in its own container (or on the self-hosted runner for
`build_image`) so failures are isolated and tool versions are pinned.

| Job             | Runner                                   | Purpose                                                                                                              | Failure policy                                       |
|-----------------|------------------------------------------|----------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `create_cache`  | `ubuntu-latest` (`node:18-bullseye`)     | Restores or hydrates the `node_modules` + `.yarn` cache keyed by `yarn.lock` so downstream jobs skip a full install. | Blocks pipeline on failure                           |
| `yarn_test`     | `ubuntu-latest` (`node:18-bullseye`)     | Installs deps (cache hit) and runs `yarn test` &mdash; the Juice Shop unit suite.                                    | Blocks `build_image`                                 |
| `gitleaks`      | `ubuntu-latest` (`zricethezav/gitleaks`) | Scans the full git history (`fetch-depth: 0`) for committed secrets; uploads `gitleaks.json` artifact.               | `continue-on-error: true` &mdash; reported, non-blocking |
| `njsscan`       | `ubuntu-latest`                          | Node.js-specific SAST via `ajinabraham/njsscan-action`; uploads SARIF to GitHub code scanning and as an artifact.    | Blocks `build_image` on warnings                     |
| `semgrep`       | `ubuntu-latest` (`semgrep/semgrep`)      | Generic SAST using the `p/javascript` ruleset; uploads `semgrep.json`.                                               | `continue-on-error: true`                            |
| `retire`        | `ubuntu-latest` (`node:18-bullseye`)     | `retire.js` scan for known-vulnerable JavaScript dependencies; uploads `retire.json`.                                | `continue-on-error: true`                            |
| `build_image`   | `self-hosted, juice-shop`                | Builds the Docker image and pushes both `:${{ github.sha }}` and `:latest` to ECR.                                   | Blocks `deploy_image`                                |
| `deploy_image`  | `ubuntu-latest` (`debian:bullseye-slim`) | SSHes into the application EC2 host, pulls the new `:latest` tag and recreates the `juice-shop` container.           | Final stage                                          |

The recent successful runs
([`#103`](https://github.com/OkomaNdu/juice-shop-devsecops-pipelin/actions/runs/26548881468),
[`#104`](https://github.com/OkomaNdu/juice-shop-devsecops-pipelin/actions/runs/26549793818))
show the expected steady-state behaviour: `gitleaks`, `semgrep`, and
`retire` report findings (visible in the Annotations panel) but
`continue-on-error: true` keeps them from blocking the release, while
`yarn_test` and `njsscan` must pass for `build_image` to start.

![CI run #103 — full pipeline, 15m 7s end-to-end](screenshots/release-pipeline-run.png)

The re-run (`#104`) demonstrates the value of the registry-based build
cache enabled in commit `d3b03ba` &mdash; total duration drops from
**15&nbsp;m&nbsp;7&nbsp;s → 4&nbsp;m&nbsp;44&nbsp;s**, with `build_image`
falling from `10m 44s` to `8s` because every Docker layer hits cache:

![CI run #104 — re-run benefits from registry build cache, 4m 44s end-to-end](screenshots/release-pipeline-run-1.png)

#### Caching Strategy

`create_cache` exists so the downstream Node.js jobs (`yarn_test`,
`retire`, and any future Node-based gate) share a single hydrated
`node_modules` / `.yarn` directory keyed by `hashFiles('yarn.lock')`.
The cache key rolls automatically whenever `yarn.lock` changes, and the
`if: steps.cache-restore.outputs.cache-hit != 'true'` guard ensures the
`yarn install` only runs on a real miss.

#### Scan Reports as Artifacts

Every security gate uploads its raw report as a workflow artifact
(`gitleaks-report`, `njsscan.sarif`, `semgrep.json`, `retire.json`).
The commented-out `upload_reports` job in `ci.yml` is the hook for
forwarding those artifacts into DefectDojo for centralised triage
&mdash; enable it once the `DEFECTDOJO_API_KEY` repository variable
is set.

### Building and Pushing the Image to AWS ECR

`build_image` runs on the
[self-hosted runner](#self-hosted-github-actions-runner) because the
Juice Shop Docker build is heavier than what GitHub-hosted runners can
comfortably accommodate. The steps:

1. Check out the source.
2. Resolve the ECR image name from the `AWS_ACCOUNT_ID` and
   `AWS_DEFAULT_REGION` repository variables:
   `${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/juice-shop`.
3. Authenticate Docker to ECR via
   `aws ecr get-login-password | docker login --username AWS --password-stdin …`.
4. Build the image tagged with both the commit SHA (immutable,
   auditable) and `latest` (the tag the application host pulls).
5. Push both tags to ECR.

The SHA tag pins a known-good build for rollback; `:latest` is the
moving pointer the `deploy_image` stage consumes.

The deployment stage and the bootstrap of the application host are
documented in [Release Deployment](#release-deployment) below.

---

## Release Deployment

The release stage of the pipeline (`build_image` → `deploy_image` in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)) builds the Juice
Shop Docker image on a self-hosted runner, pushes it to Amazon ECR
(`991776826356.dkr.ecr.us-east-2.amazonaws.com/juice-shop`), and SSHs
into a dedicated EC2 application server to pull the new `:latest` tag
and recreate the running container.

This section documents the one-time bootstrap performed on the target
EC2 host so that the pipeline's `deploy_image` job has everything it
needs to land a release.

### Provisioning the Application EC2 Instance (`juice-app-server`)

A `t2.micro` Ubuntu 26.04 LTS EC2 instance named **`juice-app-server`**
was created in `us-east-2`. The Security Group exposes:

| Port | Source      | Purpose                         |
|------|-------------|---------------------------------|
| 22   | Admin IP    | SSH bootstrap & pipeline deploy |
| 3000 | `0.0.0.0/0` | Juice Shop HTTP                 |

Connect to the instance from the workstation using the downloaded key
pair:

```bash
chmod 400 ~/Downloads/app-server-key.pem
ssh -i ~/Downloads/app-server-key.pem ubuntu@<EC2_PUBLIC_IP>
```

> The same public IP must be set as `SERVER_IP` in
> [`.github/workflows/ci.yml`](.github/workflows/ci.yml) so that the
> `deploy_image` job can reach it.

### Installing Docker and the AWS CLI

The deploy job assumes Docker is running on the target host and that the
`ubuntu` user can talk to the Docker daemon without `sudo`:

```bash
sudo apt update
sudo apt install -y docker.io awscli
sudo usermod -aG docker ubuntu
# log out and back in so the new group membership takes effect
exit
```

After re-connecting, confirm `docker ps` works without `sudo`. If it
still returns `permission denied while trying to connect to the docker
API`, the SSH session was started before the group change was applied;
a fresh `ssh` login resolves it.

### Authenticating to Amazon ECR

The host must be able to pull from the private ECR repository. Export
short-lived credentials for a least-privileged IAM principal that has
`ecr:GetAuthorizationToken` and
`ecr:BatchGetImage` / `ecr:GetDownloadUrlForLayer` on the `juice-shop`
repository, then perform a Docker login:

```bash
export AWS_ACCESS_KEY_ID=<REDACTED>
export AWS_SECRET_ACCESS_KEY=<REDACTED>
export AWS_DEFAULT_REGION=us-east-2

aws ecr get-login-password \
  | docker login \
      --username AWS \
      --password-stdin 991776826356.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
```

> :warning: **Do not commit access keys.** For production use, prefer an
> EC2 instance profile (IAM role attached to the instance) so the host
> obtains short-lived credentials from the EC2 metadata service and no
> static secrets ever land on disk. The pipeline itself uses the
> `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` GitHub Actions secrets.

### Verifying the Deployed Container

Once the pipeline's `deploy_image` job has completed at least once, the
host runs a container named `juice-shop` published on port 3000.

> :warning: **Open port 3000 inbound on the application Security Group.**
> The container publishes on `3000`, but the default Security Group only
> allows SSH (22). Without an explicit inbound rule for TCP `3000` from
> `0.0.0.0/0` (or a narrower CIDR), `docker ps` will show the container
> as `Up` but browser requests will simply time out. This was the first
> issue caught during initial verification.

```bash
ubuntu@ip-172-31-40-185:~$ docker ps
CONTAINER ID   IMAGE                                                            COMMAND                  STATUS              PORTS                                         NAMES
66707acebacc   991776826356.dkr.ecr.us-east-2.amazonaws.com/juice-shop:latest   "/nodejs/bin/node /j…"   Up About a minute   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp   juice-shop
```

The application is reachable from any browser at
`http://<EC2_PUBLIC_IP>:3000/` and serves the standard Juice Shop
product catalog:

![Juice Shop catalog served from the EC2 application host on port 3000](screenshots/juice-shop-running.png)

---

## Self-Hosted GitHub Actions Runner

The `build_image` job targets `runs-on: [self-hosted, juice-shop]`
because the Docker build for Juice Shop exceeds the disk and memory
available on GitHub-hosted runners. A dedicated EC2 instance is
registered as a self-hosted runner against the
[`OkomaNdu/juice-shop-devsecops-pipelin`](https://github.com/OkomaNdu/juice-shop-devsecops-pipelin)
repository to execute that job.

### Provisioning the Runner EC2 Instance (`self-hosted-runner`)

An Ubuntu 26.04 LTS EC2 instance named **`self-hosted-runner`** was
created with a 20 GiB root volume in `us-east-2`. Only port `22` from
the admin IP is required inbound &mdash; the runner reaches GitHub via
outbound HTTPS, so no inbound HTTP rules are needed.

```bash
chmod 400 ~/Downloads/github-runner-key.pem
ssh -i ~/Downloads/github-runner-key.pem ubuntu@<RUNNER_PUBLIC_IP>
```

### Registering the Runner with GitHub

Generate a runner registration token from
**Settings → Actions → Runners → New self-hosted runner** in the
repository, then on the EC2 host:

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.334.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.334.0/actions-runner-linux-x64-2.334.0.tar.gz
echo "048024cd2c848eb6f14d5646d56c13a4def2ae7ee3ad12122bee960c56f3d271  actions-runner-linux-x64-2.334.0.tar.gz" \
  | shasum -a 256 -c
tar xzf ./actions-runner-linux-x64-2.334.0.tar.gz

./config.sh \
  --url https://github.com/OkomaNdu/juice-shop-devsecops-pipelin \
  --token <REGISTRATION_TOKEN>
```

During interactive setup, the following values were used so the
`build_image` job's `runs-on` selector matches:

| Prompt            | Value                |
|-------------------|----------------------|
| Runner group      | `Default` (Enter)    |
| Runner name       | `ubuntu-selfhost`    |
| Additional labels | `aws,ec2,juice-shop` |
| Work folder       | `_work` (Enter)      |

> Registration tokens are short-lived (≈1 hour) and single-use. Do not
> store the value used here &mdash; generate a fresh one whenever a
> runner needs to be (re-)registered.

### Installing Build Tooling on the Runner

The runner needs Docker (to build and push the image) and the AWS CLI
(to authenticate to ECR before pushing):

```bash
sudo apt update
sudo apt install -y docker.io awscli
sudo usermod -aG docker ubuntu
```

Log out and back in so that the `ubuntu` user picks up the `docker`
group membership; otherwise the runner's `docker build` step will fail
with `permission denied while trying to connect to the docker API`.

### Running the Runner as a Service

So the runner survives reboots and runs detached from the interactive
shell, install it as a `systemd` service from inside the
`actions-runner` directory:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

Once the service is `active (running)`, the runner appears as **Idle**
in the GitHub Actions UI and will pick up any job whose `runs-on`
labels are a subset of `self-hosted, Linux, X64, aws, ec2, juice-shop`.

### Runner Image Cache & Disk Hygiene

Because `build_image` runs locally, the runner accumulates Docker
layers across every pipeline execution. After a few runs the host
holds the BuildKit builder image, the build-stage base image, the
final distroless runtime base, and one tagged Juice Shop image per
commit SHA plus `:latest`:

```bash
ubuntu@ip-172-31-15-38:~$ docker images
IMAGE                                                                                              ID             DISK USAGE   CONTENT SIZE
991776826356.dkr.ecr.us-east-2.amazonaws.com/juice-shop:bccc03e3a2e96be594c28f2d16f78dbe0aeea1fa   4e923996bb72   969MB        198MB
991776826356.dkr.ecr.us-east-2.amazonaws.com/juice-shop:d3b03bad7358d5deef60f84ac81e27526aa0a6b9   838137cc8187   969MB        198MB
991776826356.dkr.ecr.us-east-2.amazonaws.com/juice-shop:latest                                     838137cc8187   969MB        198MB
gcr.io/distroless/nodejs:18                                                                        b534f9b5528e   228MB        51.9MB
moby/buildkit:buildx-stable-1                                                                      0168606be231   355MB        111MB
node:18                                                                                            c6ae79e38498   1.58GB       411MB
```

This **caching is intentional and desirable** &mdash; keeping
`moby/buildkit:buildx-stable-1`, `node:18` and
`gcr.io/distroless/nodejs:18` warm on disk is exactly what produces
the `10m 44s → 8s` `build_image` speedup visible between runs `#103`
and `#104`. The cost is steady disk growth.

#### Reclaiming Space Without Invalidating the Build Cache

The 20 GiB root volume on `self-hosted-runner` is comfortable for
single-digit days of builds. When usage starts to creep up (`df -h /`
past ~70 %), prune *dangling* layers only &mdash; these are
intermediate layers no longer referenced by any tag and are pure
overhead. **Do not** run `docker system prune -a`; that would also
evict the BuildKit / Node base images and force the next pipeline run
back to a cold `10m+` build.

```bash
ubuntu@ip-172-31-15-38:~$ sudo docker image prune
WARNING! This will remove all dangling images.
Are you sure you want to continue? [y/N] y
Deleted Images:
untagged: sha256:0fa610c502c6...
...
Total reclaimed space: 1.467GB
```

After the prune the tagged images survive and the next `build_image`
job still hits cache:

```bash
ubuntu@ip-172-31-15-38:~$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/root        24G  7.1G   17G  31% /
```

> :information_source: **Two-tag retention is by design.** The pipeline
> tags every build with both `:${{ github.sha }}` and `:latest`. The
> SHA tag is a forensic record on the runner of exactly which commits
> were built locally, and is what allows rolling the application host
> back to a specific commit by re-pulling that tag directly from ECR.

---

## OWASP Juice Shop

> The remainder of this document is the upstream Juice Shop project
> documentation, retained for attribution and for context on the
> vulnerable application under test.

[![OWASP Flagship](https://img.shields.io/badge/owasp-flagship%20project-48A646.svg)](https://owasp.org/projects/#sec-flagships)
[![GitHub release](https://img.shields.io/github/release/juice-shop/juice-shop.svg)](https://github.com/juice-shop/juice-shop/releases/latest)
[![Twitter Follow](https://img.shields.io/twitter/follow/owasp_juiceshop.svg?style=social&label=Follow)](https://twitter.com/owasp_juiceshop)
[![Subreddit subscribers](https://img.shields.io/reddit/subreddit-subscribers/owasp_juiceshop?style=social)](https://reddit.com/r/owasp_juiceshop)

OWASP Juice Shop is probably the most modern and sophisticated insecure
web application! It can be used in security trainings, awareness demos,
CTFs and as a guinea pig for security tools! Juice Shop encompasses
vulnerabilities from the entire
[OWASP Top Ten](https://owasp.org/www-project-top-ten) along with many
other security flaws found in real-world applications.

![Juice Shop Screenshot Slideshow](screenshots/slideshow.gif)

For a detailed introduction, full list of features and architecture
overview please visit the official project page:
<https://owasp-juice.shop>

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

```bash
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

```bash
gcloud compute instances create-with-container owasp-juice-shop-app --container-image bkimminich/juice-shop
```

3. Create a firewall rule that allows inbound traffic to port 3000

```bash
gcloud compute firewall-rules create juice-rule --allow tcp:3000
```

4. Your container is now running and available at
   `http://<EXTERNAL_IP>:3000/`

### Heroku

1. [Sign up to Heroku](https://signup.heroku.com/) and
   [log in to your account](https://id.heroku.com/login)
2. Click the button below and follow the instructions

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Gitpod

1. Login to [gitpod.io](https://gitpod.io) and use <https://gitpod.io/#https://github.com/juice-shop/juice-shop/> to start a new workspace.
2. After the Gitpod workspace is loaded, Gitpod tasks is still running to install `npm install` and launch the website.
3. Your Juice Shop instance is now also available at `https://3000-<GITPOD_WORKSPACE_ID>.<GITPOD_HOSTING_ZONE>.gitpod.io`.

## Demo

Feel free to have a look at the latest version of OWASP Juice Shop:
<http://demo.owasp-juice.shop>

## Documentation

### Node.js version compatibility

OWASP Juice Shop officially supports the following versions of
[node.js](http://nodejs.org) in line with the official
[node.js LTS schedule](https://github.com/nodejs/LTS) as close as possible.

| node.js | Supported            | Tested             |
|:--------|:---------------------|:-------------------|
| 20.x    | :x:                  | :x:                |
| 19.x    | (:heavy_check_mark:) | :heavy_check_mark: |
| 18.x    | :heavy_check_mark:   | :heavy_check_mark: |
| 17.x    | (:heavy_check_mark:) | :x:                |
| 16.x    | :heavy_check_mark:   | :heavy_check_mark: |
| 15.x    | (:heavy_check_mark:) | :x:                |
| 14.x    | :heavy_check_mark:   | :heavy_check_mark: |
| <14.x   | :x:                  | :x:                |

### Troubleshooting

If you need help with the application setup please check the
[upstream _Troubleshooting_](https://pwning.owasp-juice.shop/appendix/troubleshooting.html)
guide or the [Gitter Chat](https://gitter.im/bkimminich/juice-shop).

### Official companion guide

[Pwning OWASP Juice Shop](https://leanpub.com/juice-shop) is published
under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)
and is available **for free** in PDF, Kindle and ePub format on
LeanPub. You can also
[browse the full content online](https://pwning.owasp-juice.shop).

## Contributing

Please check [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to
[contribute to the upstream Juice Shop codebase](CONTRIBUTING.md#code-contributions)
or the
[translation into different languages](CONTRIBUTING.md#i18n-contributions).

## References

See [REFERENCES.md](REFERENCES.md) for the upstream project's curated
list of conference talks, blog posts, and academic papers that cite
OWASP Juice Shop.

## Licensing

[![license](https://img.shields.io/github/license/bkimminich/juice-shop.svg)](LICENSE)

The upstream OWASP Juice Shop application is licensed under the
[MIT license](LICENSE). OWASP Juice Shop and any contributions are
Copyright © by Bjoern Kimminich & the OWASP Juice Shop contributors
2014-2023.

The DevSecOps pipeline configuration, infrastructure scripts, and
documentation added in this repository are released under the same
[MIT license](LICENSE).
