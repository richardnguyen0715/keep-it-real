# Spec Kit — Analysis: 15 Câu Hỏi Thực Chiến

Theo framework `policies/how-to-analyze-a-repo.md`.

---

## 1. Entry Point ở đâu?

```
pyproject.toml: specify = "specify_cli:main"
  → src/specify_cli/__init__.py → main()
  → Typer app với các sub-commands: init, extension, preset, workflow, integration, version, upgrade
```

AI agent slash commands (runtime): files trong `.claude/commands/`, `.github/agents/`, `.gemini/`, v.v.

---

## 2. Main Execution Flow là gì?

### Flow: `specify init` (bootstrap)

```
main() → init_command()
  → check_tool() (verify agent installed)
  → _locate_core_pack() (find bundled assets)
  → init_git_repo()
  → copy templates → .specify/templates/
  → copy scripts → .specify/scripts/
  → install_shared_infra() (workflows, extensions, presets)
  → CommandRegistrar.register_all()
      → detect agent dirs
      → write command files per agent format
  → write integrations.json
```

### Flow: User chạy `/speckit.specify` trong AI agent

```
User: /speckit.specify Build a photo album app
  → AI reads .claude/commands/speckit.specify.md (prompt file)
  → AI executes bash scripts (.specify/scripts/bash/)
      → git branch creation
      → feature numbering
      → directory creation
  → AI reads template: resolve_template("spec-template")
      → PresetResolver walks override/preset/extension/core stack
  → AI fills template với user description
  → AI writes specs/{branch}/spec.md
```

---

## 3. Core Abstractions là gì?

| Abstraction | Role |
|-------------|------|
| **Spec** | Functional requirements — user stories, Given/When/Then |
| **Plan** | Technical implementation — tech stack, architecture |
| **Tasks** | Actionable task list — phases, user story mapping |
| **Constitution** | Project governing principles |
| **Extension** | Plugin adding new commands |
| **Preset** | Template/command override layer |
| **Workflow** | Automated YAML pipeline |
| **Integration** | Per-agent adapter |

---

## 4. State Nằm Ở Đâu?

**Install-time state** (`.specify/`):
- `integrations.json` — installed integrations
- `extensions/.registry` — installed extensions
- `presets/.registry` — installed presets + priority
- `workflows/workflow-registry.json` — installed workflows

**Runtime state** (workflow engine):
- `.specify/workflows/runs/{id}/state.json` — step index, step results, status
- `.specify/workflows/runs/{id}/log.jsonl` — event log

**User artifacts** (trong project):
- `.specify/memory/constitution.md`
- `specs/{branch}/spec.md`, `plan.md`, `tasks.md`, v.v.

Không có singleton global state trong Python code. State hoàn toàn file-based → safe cho concurrent CLI usage.

---

## 5. Dependency Injection hoạt động thế nào?

Không dùng DI container. Dependency được truyền qua:
- Function arguments
- File-based configuration (`.specify/*.json`, YAML files)
- Environment variables cho catalog URLs, API keys

Typer auto-injects CLI arguments/options vào command functions.

---

## 6. Module Boundaries ra sao?

Clean separation:

```
agents.py       → write command files to agent dirs (biết về agent formats)
extensions.py   → extension lifecycle (không biết về agents directly)
presets.py      → preset lifecycle + template resolution
workflows/      → workflow engine (isolated sub-package)
__init__.py     → CLI commands (orchestrates các modules trên)
_utils.py       → file ops, git, tool checks (pure utilities)
_assets.py      → locate bundled files (packaging concern)
_console.py     → UI/display (pure presentation)
```

---

## 7. Extension Points ở đâu?

### Official customization surfaces (theo thứ tự cost):

| Surface | Cách dùng | Cost |
|---------|-----------|------|
| Project-local overrides | Chỉnh `.specify/templates/overrides/*.md` | Rất thấp |
| Presets | `specify preset add <name>` | Thấp |
| Extensions | `specify extension add <name>` / tạo mới | Trung bình |
| Custom catalogs | `.specify/*-catalogs.yml` | Thấp |
| Workflow YAML | `specify workflow add` / tạo mới | Trung bình |
| Fork | Fork toàn bộ repo | Rất cao |

### Extension hooks available:

```
before/after: specify, plan, tasks, implement, analyze,
              checklist, clarify, constitution, taskstoissues
```

### Template composition strategies:

`replace | prepend | append | wrap` — cho cả templates và commands.

---

## 8. Config System thế nào?

**Rất config-driven** ở nhiều tầng:

| Config | Location | Format |
|--------|----------|--------|
| Integration settings | `.specify/integrations.json` | JSON |
| Extension catalog | `.specify/extension-catalogs.yml` hoặc `SPECKIT_EXTENSION_CATALOG_URL` | YAML/env |
| Preset catalog | `.specify/preset-catalogs.yml` hoặc `SPECKIT_PRESET_CATALOG_URL` | YAML/env |
| Workflow catalog | `.specify/workflow-catalogs.yml` hoặc `SPECKIT_WORKFLOW_CATALOG_URL` | YAML/env |
| User-level config | `~/.specify/*.yml` | YAML |
| Extension config | `.specify/extensions/{id}/{id}-config.yml` | YAML |
| Script type | `--script sh|ps` CLI flag | CLI |

**Behavior configurable** (không hardcoded):
- Catalog sources
- Script type (bash vs powershell)
- Integration (which AI agent)
- Template resolution priority (via preset priorities)
- Workflow inputs

**Behavior hardcoded** (ít nhưng có):
- Feature branch naming format: `{number}-{slug}`
- Command name pattern: `speckit.{ext-id}.{cmd}`
- Template names: `spec-template`, `plan-template`, `tasks-template`
- Default 1-hour catalog cache TTL

---

## 9. Event Flow thế nào?

Không có event bus. Coordination qua:
- **Hooks** trong extensions/presets (before/after lifecycle)
- **Workflow steps** (sequential với conditional branching)
- **File-based handoff**: mỗi command đọc/write files, command tiếp theo đọc output

---

## 10. Data Flow thế nào?

```
User prompt ($ARGUMENTS)
  ↓
Slash command prompt file (Markdown + YAML frontmatter)
  ↓
AI agent reads template via resolve_template()
  ↓
AI runs bash scripts (git branch, directory setup)
  ↓
AI fills template → writes artifact file (spec.md, plan.md, tasks.md)
  ↓
Next command reads previous artifact
  ↓
Final: working code in repo
```

Data không đi qua Python server. Python CLI chỉ dùng lúc install/setup. Runtime = AI + bash scripts + Markdown templates.

---

## 11. External Dependencies nào critical?

| Dependency | Role | Swappable? |
|------------|------|-----------|
| `typer` | CLI framework | Khó — deeply coupled |
| `rich` | Console output | Medium — chỉ presentation |
| `pyyaml` | YAML parsing (manifests) | Easy |
| `json5` | JSON5 parsing | Easy |
| `packaging` | SemVer comparison | Easy |
| `pathspec` | `.extensionignore` patterns | Easy |
| `platformdirs` | User config dirs | Easy |
| `readchar` | Interactive key input | Easy |
| `uv`/`pipx` | Package management (runtime install) | External, not in code |

Không có LLM API calls trong code — hoàn toàn agent-agnostic.

---

## 12. Phần nào tightly coupled?

- **Typer decorators** trong `__init__.py` — rất nhiều, khó refactor
- **Template names** (hardcoded strings: `"spec-template"`, v.v.) — có ở Python và bash/powershell
- **Agent directory detection** trong `agents.py` — có hardcoded paths như `.claude/commands/`, `.github/agents/`
- **Command name format** (`speckit.{id}.{cmd}`) — enforced ở nhiều chỗ

---

## 13. Phần nào dễ replace?

- **Templates** (spec.md, plan.md format) — pure Markdown, replace bằng preset
- **Bash/PowerShell scripts** — replace bằng preset script override
- **Catalog sources** — pluggable via env var hoặc YAML
- **Command prompts** — replace bằng preset command override
- **Individual templates** — project-local overrides

---

## 14. Tests mô tả invariant gì?

Từ `pyproject.toml`:
- Tests dùng pytest, `testpaths = ["tests"]`
- Test naming: `test_*.py`, `Test*`, `test_*`

Từ `extensions/EXTENSION-DEVELOPMENT-GUIDE.md`, invariants được test:
- Extension manifest có đủ required fields
- Command files tồn tại ở đường dẫn trong manifest
- Command names match pattern `speckit.{ext-id}.{cmd}`
- Extension ID match pattern `^[a-z0-9-]+$`

---

## 15. Upgrade/Fork Cost nằm ở đâu?

### Upgrade cost (thấp nếu dùng official surfaces)

- Templates, extensions, presets: tự động re-apply sau upgrade vì dùng override system
- `specify upgrade` tự update CLI
- Potential breaking points: template name changes, command format changes, manifest schema changes

### Fork cost (cao)

- Phải maintain toàn bộ Python CLI (`src/specify_cli/`)
- Phải merge ngược upstream changes cho template improvements
- Extension/preset ecosystem builds on top of official API — fork có thể break compatibility

---

## Stable Core vs Volatile Layer

### Stable Core (ít thay đổi)

- Extension/Preset manifest schema
- Command naming convention (`speckit.{id}.{cmd}`)
- Template resolution logic (override > preset > extension > core)
- Workflow YAML schema
- Slash command file format per agent

### Volatile Layer (hay thay đổi)

- Template content (spec-template, plan-template, tasks-template)
- Agent integrations (thêm agents mới)
- Catalog entries
- Script implementations
- Individual command prompts

---

## Customization Strategy Recommended

| Mức độ | Strategy | Khi nào |
|--------|----------|---------|
| **A — Config-level** | Override env vars, catalog URLs | Redirect catalog, change script type |
| **B — Plugin/Extension** | Preset + Extension | Customize format, thêm commands — **best long-term** |
| **C — Monkey patch** | Trực tiếp edit `.specify/templates/` | Quick fix — fragile, lost on reinit |
| **D — Fork** | Fork toàn bộ repo | Chỉ khi cần thay đổi core Python behavior |

**Recommendation**: Bám vào **B (Preset/Extension)** cho hầu hết use cases. Chỉ dùng D nếu cần thay đổi CLI behavior hoặc workflow engine logic.

---

## Điểm Mạnh Khi Custom

1. **Template system rất flexible** — 4-level priority với 4 composition strategies
2. **Fully declarative** — extension/preset chỉ cần YAML + Markdown, không cần Python
3. **Air-gapped friendly** — bundle assets vào wheel, không cần network sau install
4. **Agent-agnostic** — thêm agent mới chỉ cần thêm adapter vào `agents.py`
5. **Workflow YAML** — powerful automation không cần code

## Điểm Khó Khi Custom

1. Template names hardcoded ở nhiều chỗ (Python + bash + powershell phải sync)
2. Không có hot-reload — phải reinstall extension/preset sau thay đổi
3. `__init__.py` rất lớn (222KB) — khó navigate
4. Bash/PowerShell scripts phải maintain cả hai variants
