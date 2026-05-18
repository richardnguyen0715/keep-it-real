# Spec Kit — Workflow Engine

Workflow engine cho phép tạo **automated multi-step pipelines** YAML-driven, resume được khi bị interrupt.

## Khi Nào Dùng Workflows

Workflow phù hợp khi cần:
- Automate toàn bộ SDD cycle (specify → plan → tasks → implement) không cần manual
- Conditional logic (nếu spec phức tạp → chạy thêm clarify)
- Fan-out (implement nhiều features song song)
- Gate (pause để human review trước khi implement)
- Retry / loop logic

---

## Quick Start

### Install workflow

```bash
specify workflow search
specify workflow add speckit       # Bundled speckit workflow
```

### Run workflow

```bash
specify workflow run speckit --input feature="my feature description"
```

### Resume paused workflow

```bash
specify workflow status            # List runs
specify workflow resume <run_id>   # Resume from gate
```

---

## Workflow Definition Format

```yaml
# .specify/workflows/my-workflow/workflow.yml

name: "My Workflow"
version: "1.0.0"
description: "Automate SDD cycle"

inputs:
  feature:
    type: string
    required: true
    description: "Feature description"
  mode:
    type: enum
    allowed: ["full", "lean"]
    default: "full"
    description: "Workflow mode"

defaults:
  integration: "copilot"

steps:
  - id: specify
    type: command
    command: "speckit.specify"
    args: "{{ inputs.feature }}"

  - id: check_mode
    type: if
    condition: "{{ inputs.mode == 'full' }}"
    then:
      - id: clarify
        type: command
        command: "speckit.clarify"
      - id: checklist
        type: command
        command: "speckit.checklist"

  - id: plan
    type: command
    command: "speckit.plan"
    args: "{{ inputs.tech_stack | default('') }}"

  - id: review_gate
    type: gate
    message: "Review spec and plan before continuing"
    required: true

  - id: tasks
    type: command
    command: "speckit.tasks"

  - id: analyze
    type: command
    command: "speckit.analyze"

  - id: implement
    type: command
    command: "speckit.implement"
```

---

## Step Types

### `command` — Run slash command

```yaml
- id: my_step
  type: command
  command: "speckit.specify"
  args: "{{ inputs.feature }}"
```

### `prompt` — Arbitrary inline prompt

```yaml
- id: my_prompt
  type: prompt
  prompt: "Summarize the tasks in {{ steps.tasks.output.file }}"
```

### `shell` — Run shell command

```yaml
- id: check_branch
  type: shell
  command: "git branch --show-current"
  capture_output: true   # Store in steps.check_branch.output.stdout
```

### `gate` — Human review checkpoint

```yaml
- id: review
  type: gate
  message: "Review the spec before continuing. Check specs/*/spec.md"
  required: true   # CI: auto-fail. Interactive: prompt user
```

### `if` — Conditional branching

```yaml
- id: conditional
  type: if
  condition: "{{ inputs.mode == 'full' }}"
  then:
    - id: clarify
      type: command
      command: "speckit.clarify"
  else:
    - id: skip_notice
      type: shell
      command: "echo 'Lean mode: skipping clarify'"
```

### `switch` — Multi-branch

```yaml
- id: route
  type: switch
  value: "{{ inputs.agent }}"
  cases:
    claude:
      - id: claude_setup
        type: shell
        command: "echo 'Claude mode'"
    copilot:
      - id: copilot_setup
        type: shell
        command: "echo 'Copilot mode'"
  default:
    - id: default_setup
      type: shell
      command: "echo 'Default mode'"
```

### `while` / `do-while` — Loop

```yaml
- id: retry_loop
  type: while
  condition: "{{ steps.analyze.output.has_issues == true }}"
  max_iterations: 3
  body:
    - id: fix
      type: command
      command: "speckit.implement"

- id: do_once_at_least
  type: do-while
  condition: "{{ steps.check.output.needs_more == true }}"
  body:
    - id: check
      type: command
      command: "speckit.clarify"
```

### `fan-out` / `fan-in` — Parallel dispatch

```yaml
- id: multi_feature
  type: fan-out
  collection: "{{ inputs.features }}"    # List of items
  item_var: "feature"
  steps:
    - id: specify_feature
      type: command
      command: "speckit.specify"
      args: "{{ item }}"

- id: collect_results
  type: fan-in
  source: "multi_feature"
  aggregate: "all"
```

---

## Expression Engine

Workflow dùng `{{ expression }}` syntax:

| Feature | Syntax | Ví dụ |
|---------|--------|-------|
| Input access | `{{ inputs.name }}` | `{{ inputs.feature }}` |
| Step output | `{{ steps.plan.output.file }}` | Reference previous step |
| Comparison | `==`, `!=`, `>`, `<` | `{{ count > 5 }}` |
| Boolean | `and`, `or`, `not` | `{{ items and status == 'ok' }}` |
| Membership | `in`, `not in` | `{{ 'error' not in status }}` |
| Filter: default | `{{ val \| default('fallback') }}` | Fallback cho None |
| Filter: join | `{{ list \| join(', ') }}` | Join list |
| Filter: contains | `{{ text \| contains('sub') }}` | Substring check |
| Filter: map | `{{ list \| map('attr') }}` | Extract attribute |

### Expression Namespace

| Key | Source |
|-----|--------|
| `inputs` | Workflow inputs |
| `steps` | Accumulated step results |
| `item` | Current item (inside fan-out) |
| `fan_in` | Aggregated results (inside fan-in) |

---

## State & Resume

Workflow state được persist sau mỗi step:

```
.specify/workflows/runs/{run_id}/
├── state.json    # step index, status, results
├── inputs.json   # resolved inputs
└── log.jsonl     # append-only event log
```

States:

```
CREATED → RUNNING → COMPLETED
                  → PAUSED (gate step)
                  → FAILED
                  → ABORTED
PAUSED → RUNNING (resume)
FAILED → RUNNING (resume)
```

Resume:

```bash
specify workflow resume <run_id>
```

> **Lưu ý**: Resume tracking ở top-level step index. Nested steps (trong if/while) re-run parent khi resume — không có exact nested path tracking.

---

## Catalog & Distribution

### Project-level catalog

```yaml
# .specify/workflow-catalogs.yml
catalogs:
  - url: "https://raw.githubusercontent.com/myorg/workflows/main/catalog.json"
    priority: 1
    install_allowed: true
```

### Env override

```bash
SPECKIT_WORKFLOW_CATALOG_URL="https://my-catalog.example.com/catalog.json"
```

### Custom catalog format

```json
{
  "workflows": [
    {
      "id": "my-workflow",
      "name": "My Workflow",
      "version": "1.0.0",
      "description": "Custom automated pipeline",
      "url": "https://raw.githubusercontent.com/you/my-workflow/main/workflow.yml"
    }
  ]
}
```

---

## File Locations

| Component | Location |
|-----------|----------|
| Workflow definitions | `.specify/workflows/{id}/workflow.yml` |
| Workflow registry | `.specify/workflows/workflow-registry.json` |
| Run state | `.specify/workflows/runs/{run_id}/state.json` |
| Catalog cache | `.specify/workflows/.cache/*.json` (1hr TTL) |
| Project catalogs | `.specify/workflow-catalogs.yml` |
| User catalogs | `~/.specify/workflow-catalogs.yml` |
