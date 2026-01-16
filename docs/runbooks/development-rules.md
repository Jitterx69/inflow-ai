# Development Rules & Contracts

> **Status**: P0 — MANDATORY READING FOR ALL DEVELOPERS

## Overview

These rules ensure clean ownership, safe development, and zero surprises in production. **Violations will block your PR.**

---

## Branch Rules

### Where to Branch From

| Your Work | Branch From | Merge To |
|-----------|-------------|----------|
| ML code | `ml` | `ml` |
| Backend/API code | `services` | `services` |
| Infra/Platform code | `platform` | `platform` |

### ❌ NEVER

- Branch from `main` directly
- Merge feature branches to `develop` or `main`
- Force push to any protected branch

### Feature Branch Naming

```
feature/<domain>/<ticket-id>-<short-description>

Examples:
feature/ml/ML-123-add-tokenizer
feature/service/SVC-456-user-api
feature/platform/PLT-789-vault-setup
```

---

## Code Ownership

### Directory Restrictions

| Directory | Owner | Who Can Edit |
|-----------|-------|--------------|
| `/ml/` | ML Team | ML Team only |
| `/services/` | Services Team | Services Team only |
| `/infra/` | Platform | Platform only |
| `/platform/` | Platform | Platform only |
| `/.github/` | Platform | Platform only |
| `/docs/` | All | With Platform review |

### What This Means

- **ML engineers**: Do NOT touch `/infra/` or `/services/`
- **Backend devs**: Do NOT touch `/ml/` or `/infra/`
- **Everyone**: Do NOT touch `/.github/` without Platform approval

---

## Dependency Rules

### Adding New Dependencies

1. Open an issue first describing why the dependency is needed
2. Get approval from:
   - ML Lead (for ML dependencies)
   - Services Lead (for backend dependencies)
   - Platform (for any infra/security dependencies)
3. Add to the appropriate requirements file
4. Create PR with dependency update only (no other changes)

### ❌ Forbidden Dependencies

- Anything with known CVEs
- Unmaintained packages (no updates in 2+ years)
- Packages with restrictive licenses (GPL, AGPL) without legal review

---

## Security Rules

### ❌ NEVER (Zero Tolerance)

| Violation | Consequence |
|-----------|-------------|
| Hardcoded secrets | PR blocked, incident report |
| API keys in code | PR blocked, key rotation required |
| Passwords in config | PR blocked, incident report |
| Credentials in logs | PR blocked, log purge required |

### ✅ Always

- Use environment variables for configuration
- Use Vault for secrets (when available)
- Use `.env.example` as template (never `.env` in git)
- Add sensitive files to `.gitignore`

### Secret Patterns (CI Will Catch These)

```python
# ❌ BAD
api_key = "sk-1234567890abcdef"
password = "mysecretpassword"
DATABASE_URL = "postgres://user:pass@host/db"

# ✅ GOOD
api_key = os.environ["API_KEY"]
password = os.environ.get("DB_PASSWORD")
DATABASE_URL = os.environ["DATABASE_URL"]
```

---

## Code Quality Rules

### Required for All PRs

| Check | Requirement |
|-------|-------------|
| Linting | Must pass (ruff for Python, yamllint for YAML) |
| Formatting | Must be consistent with project style |
| Tests | Must pass, coverage must not decrease |
| Documentation | New features must be documented |

### Python Style

```python
# Use type hints
def process_data(input: pd.DataFrame, threshold: float = 0.5) -> dict:
    ...

# Use docstrings
def train_model(config: TrainingConfig) -> Model:
    """
    Train a model with the given configuration.
    
    Args:
        config: Training configuration object
        
    Returns:
        Trained model instance
        
    Raises:
        ValidationError: If config is invalid
    """
    ...
```

---

## PR Requirements

### Before Opening a PR

- [ ] Code is linted and formatted
- [ ] Tests pass locally
- [ ] No secrets in code
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] My code follows the project style
- [ ] I have added tests
- [ ] I have updated documentation
- [ ] No secrets in code
```

---

## What Happens If You Break Rules

| Violation | First Offense | Repeat Offense |
|-----------|---------------|----------------|
| Wrong branch | PR rejected | Warning + education |
| Edit wrong directory | PR rejected | Escalation to lead |
| Hardcoded secret | PR blocked + rotation | Incident report |
| Skip tests | PR rejected | Pipeline access review |
| Force push | Reverted + warning | Branch access revoked |

---

## Questions?

- **Branch strategy**: Ask Platform team
- **Code ownership**: Check CODEOWNERS
- **Dependency approval**: Open an issue
- **Security concerns**: Contact Platform immediately

---

> ⚠️ **These rules are not optional.** They exist to protect everyone, including you.
