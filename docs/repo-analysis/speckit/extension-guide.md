# Spec Kit — Extension Development Guide

Hướng dẫn tạo extension từ đầu, test locally, và distribute.

## Extension là gì

Extension thêm **command mới** vào Spec Kit. Khác với preset (chỉ override template/command có sẵn), extension mở rộng khả năng của Spec Kit — thêm workflow hoàn toàn mới, tích hợp external tools, v.v.

---

## Tạo Extension Từ Đầu

### Step 1: Tạo thư mục

```bash
mkdir spec-kit-my-ext
cd spec-kit-my-ext
```

### Step 2: Tạo `extension.yml` manifest

```yaml
schema_version: "1.0"

extension:
  id: "my-ext"              # lowercase, alphanumeric + hyphens: ^[a-z0-9-]+$
  name: "My Extension"
  version: "1.0.0"          # Semantic versioning: MAJOR.MINOR.PATCH
  description: "My custom extension"
  author: "Your Name"
  repository: "https://github.com/you/spec-kit-my-ext"
  license: "MIT"

requires:
  speckit_version: ">=0.8.0"   # Minimum spec-kit version
  tools:                        # Optional: external tools required
    - name: "jq"
      required: true
  commands:                     # Optional: core commands this ext depends on
    - "speckit.tasks"

provides:
  commands:
    - name: "speckit.my-ext.run"      # Pattern: speckit.{ext-id}.{cmd}
      file: "commands/run.md"
      description: "Run my workflow"
      aliases: ["speckit.my-ext.go"]  # Optional aliases

  config:                             # Optional: config files
    - name: "my-ext-config.yml"
      template: "my-ext-config.template.yml"
      description: "Extension configuration"
      required: false

hooks:                                # Optional: auto-run after core commands
  after_tasks:
    command: "speckit.my-ext.run"
    optional: true                    # false = always run, true = prompt user
    prompt: "Run my extension?"
    description: "Auto-run after tasks generation"

tags:
  - "automation"
  - "integration"
```

### Step 3: Tạo command file

```bash
mkdir commands
```

**`commands/run.md`**:

```markdown
---
description: "Run my workflow"
tools:
  - 'bash'
scripts:
  sh: .specify/scripts/bash/common.sh    # Reference core scripts
  ps: .specify/scripts/powershell/common.ps1
---

# My Workflow

## User Input

$ARGUMENTS

## Steps

1. Load project context
2. Execute workflow
3. Report results

```bash
#!/usr/bin/env bash
set -euo pipefail

ARGS="$ARGUMENTS"
EXT_DIR=".specify/extensions/my-ext"

# Load config
if [ -f "$EXT_DIR/my-ext-config.yml" ]; then
  echo "Config found"
fi

echo "Running with args: $ARGS"
```

## Output

Show summary of what was done.
```

### Step 4: Tạo config template (optional)

**`my-ext-config.template.yml`**:

```yaml
# My Extension Configuration
# Copy to my-ext-config.yml and customize

api:
  endpoint: "https://api.example.com"
  timeout: 30

features:
  feature_a: true

credentials:
  # Use env var: SPECKIT_MY_EXT_API_KEY
  api_key: "${MY_EXT_API_KEY}"
```

### Step 5: Tạo `.extensionignore`

```gitignore
# .extensionignore
tests/
.github/
*.pyc
__pycache__/
CONTRIBUTING.md
```

### Step 6: Test locally

```bash
cd /path/to/your-project
specify extension add --dev /path/to/spec-kit-my-ext
```

Verify:

```bash
specify extension list
# ✓ My Extension (v1.0.0)
#   Commands: 1 | Hooks: 1 | Status: Enabled

specify extension info my-ext
```

Test command trong Claude:

```bash
claude
> /speckit.my-ext.run some arguments
```

Kiểm tra command file đã được tạo:

```bash
ls .claude/commands/speckit.my-ext.*
cat .claude/commands/speckit.my-ext.run.md
```

### Step 7: Remove và reinstall

```bash
specify extension remove my-ext
specify extension add --dev /path/to/spec-kit-my-ext
```

---

## Validation Rules

| Field | Pattern | Valid | Invalid |
|-------|---------|-------|---------|
| Extension ID | `^[a-z0-9-]+$` | `my-ext`, `jira-sync` | `MyExt`, `my_ext` |
| Version | SemVer | `1.0.0` | `v1.0`, `1.0.0-beta` |
| Command name | `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$` | `speckit.my-ext.run` | `my-ext.run`, `speckit.run` |
| Command file | Relative path | `commands/run.md` | `/absolute/path.md`, `../outside.md` |

---

## Config Loading Pattern

```bash
#!/usr/bin/env bash
EXT_DIR=".specify/extensions/my-ext"

# 1. Default values
ENDPOINT="https://api.example.com"
TIMEOUT=30

# 2. Load from config file
if [ -f "$EXT_DIR/my-ext-config.yml" ]; then
  ENDPOINT=$(yq eval '.api.endpoint' "$EXT_DIR/my-ext-config.yml")
  TIMEOUT=$(yq eval '.api.timeout' "$EXT_DIR/my-ext-config.yml")
fi

# 3. Load local overrides (gitignored)
if [ -f "$EXT_DIR/my-ext-config.local.yml" ]; then
  ENDPOINT=$(yq eval '.api.endpoint // env(ENDPOINT)' "$EXT_DIR/my-ext-config.local.yml")
fi

# 4. Environment variable override
ENDPOINT="${SPECKIT_MY_EXT_ENDPOINT:-$ENDPOINT}"
API_KEY="${SPECKIT_MY_EXT_API_KEY:-}"
```

---

## Extension với Hooks

Hook cho phép extension tự động chạy sau/trước core commands.

```yaml
# extension.yml
hooks:
  after_tasks:
    command: "speckit.my-ext.review"
    optional: false          # Always run — không prompt user
    description: "Auto-review tasks after generation"

  before_implement:
    command: "speckit.my-ext.pre-check"
    optional: true
    prompt: "Run pre-implementation check?"
```

Available hooks:
```
before/after_specify
before/after_plan
before/after_tasks
before/after_implement
before/after_analyze
before/after_checklist
before/after_clarify
before/after_constitution
before/after_taskstoissues
```

---

## Script Path Rewriting

Khi extension install, relative script paths được rewrite tự động:

**Trong extension.yml**:
```yaml
scripts:
  sh: ../../scripts/bash/helper.sh
```

**Sau khi install**:
```yaml
scripts:
  sh: .specify/scripts/bash/helper.sh
```

Điều này cho phép extension reference core spec-kit scripts.

---

## Distribute Extension

### Option 1: Local dev path

```bash
specify extension add --dev /path/to/my-ext
```

### Option 2: Git repository

```bash
# Clone và install
git clone https://github.com/you/spec-kit-my-ext
specify extension add --dev spec-kit-my-ext/
```

### Option 3: Submit lên Community Catalog

1. Tạo GitHub repo: `spec-kit-my-ext`
2. Tạo release (tag `v1.0.0`)
3. File issue dùng "Extension Submission" template trên github/spec-kit
4. Maintainer review → thêm vào `catalog.community.json`
5. Users có thể install:
   ```bash
   specify extension search my-ext
   specify extension add my-ext
   ```

---

## Automated Testing

```python
# tests/test_my_extension.py
from pathlib import Path
from specify_cli.extensions import ExtensionManifest

def test_manifest_valid():
    manifest = ExtensionManifest(Path("extension.yml"))
    assert manifest.id == "my-ext"
    assert len(manifest.commands) >= 1

def test_command_files_exist():
    manifest = ExtensionManifest(Path("extension.yml"))
    for cmd in manifest.commands:
        cmd_file = Path(cmd["file"])
        assert cmd_file.exists(), f"Command file not found: {cmd_file}"
```

---

## Registry Debug

```bash
# Xem extension registry
cat .specify/extensions/.registry

# Xem command files đã được register
ls .claude/commands/speckit.my-ext.*

# Verify extension installed
specify extension list
specify extension info my-ext
```
