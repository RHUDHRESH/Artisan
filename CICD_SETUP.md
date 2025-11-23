# CI/CD Setup Guide

## Overview

The Artisan Hub project includes a comprehensive CI/CD pipeline using GitHub Actions for automated testing, security scanning, deployment, and dependency management.

## 📋 Table of Contents

- [Workflows](#workflows)
- [Required Secrets](#required-secrets)
- [Initial Setup](#initial-setup)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Workflow Details](#workflow-details)
- [Troubleshooting](#troubleshooting)

---

## 🔄 Workflows

The project includes 4 main GitHub Actions workflows:

### 1. **Continuous Integration** (`.github/workflows/ci.yml`)
- **Trigger**: Push to main/develop, Pull Requests
- **Jobs**:
  - Backend tests with Redis
  - Frontend tests and build
  - Code quality checks (flake8, black, mypy, pylint, ESLint)
  - Integration tests
  - Coverage reporting to Codecov

### 2. **Deployment** (`.github/workflows/deploy.yml`)
- **Trigger**: Push to main branch
- **Jobs**:
  - Deploy frontend to Vercel
  - Build and push backend Docker image to Google Container Registry
  - Deploy backend to Google Cloud Run
  - Smoke tests for production endpoints
  - Create GitHub release

### 3. **Docker Build & Publish** (`.github/workflows/docker.yml`)
- **Trigger**: Tags matching `v*.*.*`, manual workflow dispatch
- **Jobs**:
  - Multi-platform Docker builds (amd64, arm64)
  - Push to Google Container Registry and Docker Hub
  - Vulnerability scanning with Trivy
  - Docker Compose validation

### 4. **Security Scanning** (`.github/workflows/security.yml`)
- **Trigger**: Push to main/develop, Pull Requests, Weekly schedule
- **Jobs**:
  - CodeQL analysis (Python, JavaScript)
  - Python security (Safety, Bandit, pip-audit)
  - JavaScript security (npm audit)
  - Secret scanning with TruffleHog
  - Container security with Trivy
  - SAST with Semgrep
  - License compliance checking

### 5. **Dependency Updates** (`.github/dependabot.yml`)
- **Trigger**: Weekly automated checks
- **Updates**:
  - Python packages (pip)
  - Node packages (npm)
  - GitHub Actions
  - Docker base images

---

## 🔑 Required Secrets

Configure these secrets in your GitHub repository settings:

### Repository Settings → Secrets and Variables → Actions

| Secret Name | Description | Required For | How to Get |
|------------|-------------|--------------|------------|
| `GROQ_API_KEY` | GROQ API key for LLM inference | Testing, Deployment | [console.groq.com](https://console.groq.com) |
| `VERCEL_TOKEN` | Vercel deployment token | Frontend deployment | Vercel Settings → Tokens |
| `VERCEL_ORG_ID` | Vercel organization ID | Frontend deployment | `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | Vercel project ID | Frontend deployment | `.vercel/project.json` after `vercel link` |
| `GCP_PROJECT_ID` | Google Cloud project ID | Backend deployment | GCP Console |
| `GCP_SA_KEY` | Google Cloud service account key (JSON) | Backend deployment | See GCP setup below |
| `DOCKERHUB_USERNAME` | Docker Hub username | Docker publishing | Docker Hub account |
| `DOCKERHUB_TOKEN` | Docker Hub access token | Docker publishing | Docker Hub → Security |
| `CODECOV_TOKEN` | Codecov upload token (optional) | Coverage reporting | [codecov.io](https://codecov.io) |

---

## 🚀 Initial Setup

### Step 1: Fork/Clone Repository

```bash
git clone https://github.com/RHUDHRESH/Artisan.git
cd Artisan
```

### Step 2: Set Up Vercel

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Link your project:
   ```bash
   cd frontend
   vercel link
   ```

3. Get your project IDs:
   ```bash
   cat .vercel/project.json
   ```

   Copy `orgId` and `projectId` to GitHub secrets as `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`.

4. Generate Vercel token:
   - Go to [Vercel Account Settings → Tokens](https://vercel.com/account/tokens)
   - Create new token
   - Add to GitHub secrets as `VERCEL_TOKEN`

### Step 3: Set Up Google Cloud

1. Create a Google Cloud project:
   ```bash
   gcloud projects create artisan-hub-prod
   gcloud config set project artisan-hub-prod
   ```

2. Enable required APIs:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     containerregistry.googleapis.com \
     cloudbuild.googleapis.com
   ```

3. Create service account:
   ```bash
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions"
   ```

4. Grant permissions:
   ```bash
   PROJECT_ID=$(gcloud config get-value project)

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"
   ```

5. Create and download key:
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com
   ```

6. Add to GitHub secrets:
   - Copy entire contents of `key.json`
   - Add to GitHub secrets as `GCP_SA_KEY`
   - Add project ID as `GCP_PROJECT_ID`
   - **Delete `key.json` from your local machine**

### Step 4: Set Up Docker Hub (Optional)

1. Create Docker Hub account at [hub.docker.com](https://hub.docker.com)

2. Generate access token:
   - Docker Hub → Account Settings → Security → New Access Token

3. Add to GitHub secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: The access token

### Step 5: Set Up GROQ API

1. Get API key from [console.groq.com](https://console.groq.com)
2. Add to GitHub secrets as `GROQ_API_KEY`

### Step 6: Configure Codecov (Optional)

1. Go to [codecov.io](https://codecov.io) and sign in with GitHub
2. Add your repository
3. Copy the upload token
4. Add to GitHub secrets as `CODECOV_TOKEN`

---

## 🪝 Pre-commit Hooks

Pre-commit hooks ensure code quality before commits.

### Installation

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the hooks:
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

3. (Optional) Run on all files:
   ```bash
   pre-commit run --all-files
   ```

### Included Hooks

**General:**
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Large file checks
- Merge conflict detection
- Private key detection

**Python:**
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- Bandit (security)
- mypy (type checking)

**JavaScript/TypeScript:**
- ESLint (linting)
- Prettier (formatting)

**Security:**
- detect-secrets (secret detection)
- TruffleHog (secret scanning)

**Infrastructure:**
- hadolint (Dockerfile linting)
- shellcheck (shell script linting)
- yamllint (YAML linting)
- markdownlint (Markdown linting)

**Commit Messages:**
- commitizen (conventional commits)

### Skipping Hooks

If you need to skip hooks (use sparingly):
```bash
git commit --no-verify -m "message"
```

---

## 📊 Workflow Details

### CI Workflow Triggers

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

**What it does:**
1. Runs backend tests with Redis
2. Runs frontend tests and builds
3. Checks code quality (linting, formatting, type checking)
4. Runs integration tests
5. Uploads coverage to Codecov

### Deploy Workflow Triggers

```yaml
on:
  push:
    branches: [main]
```

**What it does:**
1. Deploys frontend to Vercel
2. Builds backend Docker image
3. Pushes image to Google Container Registry
4. Deploys backend to Google Cloud Run
5. Runs smoke tests on production
6. Creates GitHub release

### Docker Workflow Triggers

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:
```

**What it does:**
1. Builds Docker images for multiple platforms (amd64, arm64)
2. Pushes to Google Container Registry
3. Pushes to Docker Hub
4. Scans for vulnerabilities with Trivy
5. Tests with Docker Compose

### Security Workflow Triggers

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
```

**What it does:**
1. Runs CodeQL analysis
2. Scans Python dependencies for vulnerabilities
3. Scans JavaScript dependencies for vulnerabilities
4. Searches for leaked secrets
5. Scans Docker images for CVEs
6. Runs SAST with Semgrep
7. Checks license compliance

---

## 🔧 Configuration Files

### Environment Variables

The workflows use these environment variables from secrets:

**Backend:**
- `GROQ_API_KEY`: LLM provider API key
- `REDIS_URL`: Redis connection URL (defaults to localhost in CI)
- `BACKEND_URL`: Backend API URL
- `CORS_ORIGINS`: Allowed CORS origins

**Frontend:**
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_WS_URL`: WebSocket URL

**Deployment:**
- Vercel: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
- GCP: `GCP_PROJECT_ID`, `GCP_SA_KEY`
- Docker: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`

### Workflow Configuration

You can customize workflows by editing files in `.github/workflows/`.

**Common customizations:**
- Change Node.js version: Update `node-version` in workflow files
- Change Python version: Update `python-version` in workflow files
- Modify test commands: Edit the test steps
- Change deployment regions: Update GCP region in deploy.yml
- Adjust security scanning: Modify security.yml rules

---

## 📖 Usage

### Running Tests Locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
pytest tests/ --cov=backend
```

**Frontend:**
```bash
cd frontend
npm install
npm run test
npm run build
```

### Manual Deployment

**Frontend (Vercel):**
```bash
cd frontend
vercel --prod
```

**Backend (Google Cloud Run):**
```bash
gcloud run deploy artisan-backend \
  --source ./backend \
  --region us-central1 \
  --allow-unauthenticated
```

### Building Docker Images

```bash
# Backend
docker build -t artisan-backend ./backend

# Frontend
docker build -t artisan-frontend ./frontend

# Full stack
docker-compose up --build
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. CI Tests Failing

**Redis connection errors:**
```
Solution: Ensure Redis service is configured in workflow
```

**Import errors:**
```
Solution: Check requirements.txt includes all dependencies
```

**Test timeouts:**
```
Solution: Increase timeout in pytest.ini or workflow
```

#### 2. Deployment Failures

**Vercel deployment fails:**
```
Check:
- VERCEL_TOKEN is valid
- VERCEL_ORG_ID and VERCEL_PROJECT_ID are correct
- vercel.json configuration is valid
```

**Google Cloud Run deployment fails:**
```
Check:
- GCP_SA_KEY has correct permissions
- Container Registry API is enabled
- Cloud Run API is enabled
- Service account has run.admin role
```

#### 3. Docker Build Failures

**Multi-platform build errors:**
```
Solution: Ensure QEMU is set up (handled automatically in workflow)
```

**Push permission denied:**
```
Check:
- DOCKERHUB_USERNAME and DOCKERHUB_TOKEN are correct
- GCP service account has storage.admin role
```

#### 4. Security Scan Failures

**False positives in secret scanning:**
```
Solution: Add to .secrets.baseline:
pre-commit run detect-secrets --all-files
git add .secrets.baseline
```

**Vulnerability in dependencies:**
```
Solution: Update dependencies:
pip-audit --fix
npm audit fix
```

### Getting Help

1. **Check workflow logs**: GitHub Actions tab → Select workflow → View logs
2. **Enable debug logging**: Add `ACTIONS_STEP_DEBUG: true` to secrets
3. **Review documentation**: See DEPLOYMENT.md for deployment details
4. **Check service status**:
   - Vercel: [status.vercel.com](https://status.vercel.com)
   - Google Cloud: [status.cloud.google.com](https://status.cloud.google.com)
   - GitHub: [githubstatus.com](https://githubstatus.com)

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel Documentation](https://vercel.com/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Docker Documentation](https://docs.docker.com)
- [Pre-commit Documentation](https://pre-commit.com)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)

---

## 🔄 Maintenance

### Regular Tasks

**Weekly:**
- Review Dependabot PRs
- Check security scan results
- Monitor deployment health

**Monthly:**
- Update base Docker images
- Review and update dependencies
- Audit access tokens and secrets

**Quarterly:**
- Review workflow efficiency
- Update CI/CD best practices
- Audit security configurations

### Updating Workflows

1. Edit workflow file in `.github/workflows/`
2. Test changes in a feature branch
3. Create pull request
4. Review workflow run in PR
5. Merge to main when tests pass

---

## 📝 Best Practices

1. **Never commit secrets**: Use GitHub Secrets for sensitive data
2. **Test locally first**: Run tests and builds before pushing
3. **Use pre-commit hooks**: Catch issues before CI
4. **Monitor deployments**: Check Cloud Run and Vercel dashboards
5. **Keep dependencies updated**: Review Dependabot PRs promptly
6. **Fix security issues immediately**: Don't ignore security scan results
7. **Use semantic versioning**: Tag releases as v1.0.0, v1.1.0, etc.
8. **Document changes**: Update CHANGELOG.md for releases

---

## 🎯 Next Steps

After completing this setup:

1. ✅ Push code to trigger first CI run
2. ✅ Create a test PR to verify CI/CD
3. ✅ Tag a release (v1.0.0) to trigger Docker build
4. ✅ Monitor first deployment
5. ✅ Set up status badges in README.md
6. ✅ Configure notification webhooks (Slack, Discord, etc.)

---

## 🆘 Support

For issues with this CI/CD setup:
1. Check this documentation
2. Review GitHub Actions logs
3. Check service status pages
4. Create an issue in the repository

**Happy deploying! 🚀**
