# Spec Kit — Customization Guide

## Ba Cách Customize

| Priority | Cơ chế | Location | Khi nào dùng |
|----------|--------|----------|--------------|
| ⬆ 1 (cao nhất) | **Project-Local Override** | `.specify/templates/overrides/` | Patch 1 file cho 1 project, không share |
| 2 | **Preset** | `.specify/presets/{id}/templates/` | Override template/command hiện có, có thể share |
| 3 | **Extension** | `.specify/extensions/{id}/templates/` | Thêm command/capability mới |
| ⬇ 4 (thấp nhất) | **Core Default** | `.specify/templates/` | Shipped defaults, không nên sửa trực tiếp |

> **Rule**: Templates resolved **runtime** (top-down, first match). Command files applied **install-time** (khi chạy `specify extension add` hoặc `specify preset add`).

---

## 1. Project-Local Override (Dễ nhất)

Dùng khi chỉ muốn thay 1 template cho project hiện tại, không cần tạo preset.

```bash
mkdir -p .specify/templates/overrides/
cp .specify/templates/spec-template.md .specify/templates/overrides/spec-template.md
# Rồi edit file override
```

Template names (core):
- `spec-template.md`
- `plan-template.md`
- `tasks-template.md`
- `constitution-template.md`
- `checklist-template.md`

---

## 2. Presets — Customize Existing Workflows

Preset dùng khi muốn thay đổi **how** Spec Kit works — không thêm command mới, chỉ override templates/commands.

### Khi nào dùng Preset
- Enforce org standards cho spec format
- Dùng terminology domain-specific (Agile, DDD, v.v.)
- Thêm regulatory traceability sections vào plan
- Localize workflow sang ngôn ngữ khác
- Apply security review gates bắt buộc

### Install Preset

```bash
specify preset search
specify preset add lean
specify preset add lean --priority 1   # priority thấp hơn = ưu tiên cao hơn
```

### Tạo Preset Tùy Chỉnh

**Cấu trúc tối thiểu**:

```
my-preset/
├── preset.yml          # Manifest
├── templates/          # Template overrides
│   └── spec-template.md
└── commands/           # Command overrides (optional)
    └── speckit.specify.md
```

**`preset.yml`**:

```yaml
schema_version: "1.0"

preset:
  id: "my-preset"
  name: "My Preset"
  version: "1.0.0"
  description: "Custom preset for our org"
  author: "Your Name"

requires:
  speckit_version: ">=0.8.0"

provides:
  templates:
    - name: "spec-template"
      file: "templates/spec-template.md"
      strategy: "replace"     # replace | prepend | append | wrap

  commands:
    - name: "speckit.specify"
      type: "command"
      file: "commands/speckit.specify.md"
      strategy: "wrap"        # wrap cho phép inject CORE_TEMPLATE
```

**Composition strategies**:

| Strategy | Hành vi |
|----------|---------|
| `replace` (default) | Hoàn toàn thay thế core template |
| `prepend` | Thêm content **trước** core |
| `append` | Thêm content **sau** core |
| `wrap` | Dùng `{CORE_TEMPLATE}` placeholder — bao quanh core |

**Ví dụ — Wrap strategy** (thêm header bắt buộc):

```markdown
<!-- my-preset/templates/spec-template.md -->
## ⚠️ COMPLIANCE NOTICE
This spec must be reviewed by Security team before implementation.

{CORE_TEMPLATE}

## Regulatory Traceability
- Requirement ID: [JIRA-XXX]
- Compliance Owner: [NAME]
```

**Install locally (dev)**:

```bash
specify preset add --dev /path/to/my-preset
```

**Multiple presets** — stacking:

```bash
specify preset add security-gates --priority 1
specify preset add agile-format --priority 2
# security-gates (priority 1) wins khi conflict
```

---

## 3. Extensions — Add New Capabilities

Extension dùng khi muốn thêm **command mới** hoàn toàn — ví dụ: Jira integration, V-Model test traceability, code review gate, health diagnostics.

### Install Extension

```bash
specify extension search
specify extension add git     # Bundled git extension
specify extension add --dev /path/to/my-extension  # Local dev
```

### Tạo Extension Tùy Chỉnh

**Cấu trúc tối thiểu**:

```
my-ext/
├── extension.yml           # Manifest
└── commands/
    └── hello.md            # Command prompt
```

**`extension.yml`**:

```yaml
schema_version: "1.0"

extension:
  id: "my-ext"              # lowercase, alphanumeric + hyphens only
  name: "My Extension"
  version: "1.0.0"
  description: "Adds custom workflow"
  author: "Your Name"
  repository: "https://github.com/you/spec-kit-my-ext"

requires:
  speckit_version: ">=0.8.0"

provides:
  commands:
    - name: "speckit.my-ext.hello"   # MUST match: speckit.{ext-id}.{cmd}
      file: "commands/hello.md"
      description: "Say hello"

hooks:                        # Optional: auto-run after core commands
  after_tasks:
    command: "speckit.my-ext.hello"
    optional: true
    prompt: "Run hello?"

tags:
  - "utility"
```

**`commands/hello.md`**:

```markdown
---
description: "Hello command"
---

# Hello

## User Input
$ARGUMENTS

## Steps

1. Greet the user

```bash
echo "Hello from my extension! Args: $ARGUMENTS"
```
```

**Naming rules**:
- Extension ID: `^[a-z0-9-]+$` (lowercase, hyphens only)
- Command name: `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`

### Available Hook Points

```
before_specify / after_specify
before_plan / after_plan
before_tasks / after_tasks
before_implement / after_implement
before_analyze / after_analyze
before_checklist / after_checklist
before_clarify / after_clarify
before_constitution / after_constitution
before_taskstoissues / after_taskstoissues
```

### Config Files cho Extension

```yaml
# extension.yml
provides:
  config:
    - name: "my-ext-config.yml"
      template: "my-ext-config.template.yml"
      required: false
```

Config được install vào: `.specify/extensions/my-ext/my-ext-config.yml`

Config loading precedence (trong command script):
1. Extension defaults (`extension.yml` → `defaults`)
2. Project config (`.specify/extensions/my-ext/my-ext-config.yml`)
3. Local overrides (`my-ext-config.local.yml` — gitignored)
4. Environment variables (`SPECKIT_MY_EXT_*`)

### Exclude Dev Files (`.extensionignore`)

```gitignore
# .extensionignore
tests/
.github/
*.pyc
CONTRIBUTING.md
```

---

## 4. Preset với Extension Command Override

Preset cũng có thể override commands của extension (không chỉ core commands):

```yaml
# my-preset/preset.yml
provides:
  commands:
    - name: "speckit.my-ext.hello"   # Extension command
      type: "command"
      file: "commands/speckit.my-ext.hello.md"
      strategy: "prepend"
```

> Extension phải được install trước — nếu extension chưa install, preset skip command đó.

---

## 5. Custom Catalog Sources

### Project-level catalogs

```yaml
# .specify/extension-catalogs.yml
catalogs:
  - url: "https://raw.githubusercontent.com/myorg/spec-kit-catalog/main/catalog.json"
    priority: 1
    install_allowed: true
    name: "My Org Catalog"
```

```yaml
# .specify/workflow-catalogs.yml
catalogs:
  - url: "https://..."
    priority: 1
    install_allowed: true
```

### User-level catalogs

```yaml
# ~/.specify/extension-catalogs.yml
# ~/.specify/preset-catalogs.yml
# ~/.specify/workflow-catalogs.yml
```

### Environment variable override

```bash
SPECKIT_EXTENSION_CATALOG_URL="https://my-catalog.example.com/catalog.json"
SPECKIT_PRESET_CATALOG_URL="https://..."
SPECKIT_WORKFLOW_CATALOG_URL="https://..."
```

---

## 6. Debug Template Resolution

Kiểm tra template nào đang được dùng:

```bash
specify preset resolve spec-template
specify preset resolve plan-template
```

---

## Khi Nào Dùng Gì — Bảng Quyết Định

| Goal | Dùng cái nào |
|------|-------------|
| Thay format spec/plan/tasks template | Preset hoặc Local Override |
| Thêm command `/speckit.jira.sync` mới | Extension |
| Enforce org standards cho tất cả projects | Preset (publish lên catalog) |
| Integrate external tool (Jira, Linear) | Extension |
| Thêm security review gate vào plan | Preset (wrap strategy) |
| Patch 1 file template chỉ cho 1 project | Local Override (`.specify/templates/overrides/`) |
| Localize sang tiếng Việt | Preset (replace tất cả templates) |
| Auto-run code review sau tasks | Extension (after_tasks hook) |
