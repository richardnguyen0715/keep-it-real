# Spec Kit — Architecture

## Repository Structure

```
spec-kit/
├── src/specify_cli/        # Python CLI source
│   ├── __init__.py         # Main CLI + all commands (specify init, extension, preset, workflow, v.v.)
│   ├── agents.py           # CommandRegistrar — write command files to agent dirs
│   ├── extensions.py       # ExtensionManifest, ExtensionRegistry, ExtensionManager, ExtensionCatalog
│   ├── presets.py          # PresetManifest, PresetRegistry, PresetManager, PresetCatalog, PresetResolver
│   ├── integration_runtime.py  # Invoke AI agent CLIs at runtime
│   ├── integration_state.py    # Read/write .specify/integrations.json
│   ├── shared_infra.py     # Install shared infrastructure (scripts, templates)
│   ├── catalogs.py         # Shared catalog fetch logic
│   ├── workflows/          # Workflow engine
│   │   ├── __init__.py
│   │   ├── engine.py       # WorkflowDefinition, WorkflowEngine, RunState
│   │   ├── base.py         # StepBase, StepContext, StepResult
│   │   ├── expressions.py  # {{ }} expression evaluator
│   │   ├── catalog.py      # WorkflowCatalog
│   │   └── steps/          # 10 step types: command, shell, gate, if, switch, while, do-while, fan-out, fan-in, prompt
│   ├── authentication/     # Auth helpers
│   ├── integrations/       # Per-agent integration configs
│   ├── _assets.py          # Locate bundled files (core_pack)
│   ├── _console.py         # Rich console, banners, interactive prompts
│   ├── _utils.py           # File ops, git, tool checks
│   ├── _version.py         # Version check, self-upgrade
│   └── _github_http.py     # GitHub API calls
│
├── templates/              # Core Markdown templates
│   ├── spec-template.md
│   ├── plan-template.md
│   ├── tasks-template.md
│   ├── constitution-template.md
│   ├── checklist-template.md
│   └── commands/           # Slash command prompt files
│       ├── specify.md
│       ├── plan.md
│       ├── tasks.md
│       ├── implement.md
│       ├── constitution.md
│       ├── clarify.md
│       ├── analyze.md
│       ├── checklist.md
│       └── taskstoissues.md
│
├── scripts/
│   ├── bash/               # .sh automation scripts
│   └── powershell/         # .ps1 automation scripts
│
├── extensions/             # Extension ecosystem docs & catalog
│   ├── EXTENSION-DEVELOPMENT-GUIDE.md
│   ├── EXTENSION-API-REFERENCE.md
│   ├── EXTENSION-PUBLISHING-GUIDE.md
│   ├── EXTENSION-USER-GUIDE.md
│   ├── catalog.json        # Official extensions
│   ├── catalog.community.json  # Community extensions
│   ├── git/                # Bundled git extension
│   └── template/           # Extension scaffold
│
├── presets/                # Preset ecosystem docs & catalog
│   ├── ARCHITECTURE.md
│   ├── README.md
│   ├── catalog.json
│   ├── catalog.community.json
│   ├── lean/               # Bundled lean preset
│   └── scaffold/           # Preset scaffold
│
├── workflows/
│   ├── ARCHITECTURE.md
│   ├── catalog.json
│   └── speckit/            # Bundled speckit workflow
│
├── docs/                   # User-facing documentation
├── integrations/           # Integration-specific docs
└── pyproject.toml          # Package config + bundled asset mapping
```

---

## Architecture Layers

```
┌────────────────────────────────────────────────────────┐
│  User / AI Agent Interface Layer                        │
│  Slash commands: /speckit.specify, /speckit.plan, v.v.  │
│  Nằm ở: .claude/commands/, .github/agents/, v.v.        │
└──────────────┬─────────────────────────────────────────┘
               │ AI executes prompt → runs scripts
┌──────────────▼──────────────────────────────┐
│  Template Resolution Layer (Runtime)         │
│  PresetResolver walks priority stack         │
│  Override > Preset > Extension > Core        │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Scripts Layer                               │
│  bash/powershell scripts: branch creation,   │
│  directory setup, feature numbering          │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  CLI Layer (specify)                         │
│  specify init / extension add / preset add   │
│  / workflow run / integration add            │
│  Source: src/specify_cli/__init__.py         │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Core Infrastructure                         │
│  agents.py: CommandRegistrar                 │
│  presets.py: PresetManager, PresetResolver   │
│  extensions.py: ExtensionManager             │
│  workflows/engine.py: WorkflowEngine         │
└─────────────────────────────────────────────┘
```

---

## Entry Points

### CLI entry point

```
pyproject.toml → [project.scripts]
  specify = "specify_cli:main"
    → src/specify_cli/__init__.py → main()
```

### Main command tree (Typer app)

```
specify
├── init          # Bootstrap project
├── version       # Show version
├── upgrade       # Self-upgrade
├── integration
│   ├── list
│   ├── add
│   └── remove
├── extension
│   ├── list
│   ├── search
│   ├── add
│   ├── remove
│   └── info
├── preset
│   ├── list
│   ├── search
│   ├── add
│   ├── remove
│   ├── info
│   └── resolve
└── workflow
    ├── list
    ├── search
    ├── add
    ├── run
    ├── resume
    ├── status
    └── remove
```

---

## Data Flow: `specify init`

```
specify init my-project --integration copilot
  │
  ├── _locate_core_pack()       # Find bundled assets in installed package
  ├── init_git_repo()           # git init (if not already)
  ├── copy templates/           # .specify/templates/
  ├── copy scripts/             # .specify/scripts/bash/, /powershell/
  ├── install workflows/speckit/ # .specify/workflows/speckit/
  ├── install extensions/git/   # .specify/extensions/git/
  ├── install presets/lean/     # .specify/presets/lean/ (nếu có)
  ├── CommandRegistrar.register_all()
  │     → detect agent dirs (.claude/, .github/agents/, .gemini/, v.v.)
  │     → write slash command files per agent format
  └── write .specify/integrations.json
```

---

## Data Flow: `specify extension add <name>`

```
specify extension add git
  │
  ├── ExtensionCatalog.fetch()
  │     → check SPECKIT_EXTENSION_CATALOG_URL env
  │     → else read .specify/extension-catalogs.yml
  │     → else use built-in catalog.json
  ├── Download extension files → .specify/extensions/git/
  ├── Parse extension.yml manifest
  ├── Copy commands/* → resolve relative paths
  ├── CommandRegistrar.register(commands)
  │     → write to all detected agent dirs
  └── Update .specify/extensions/.registry
```

---

## Data Flow: Template Resolution (Runtime, trong AI session)

```
AI runs /speckit.specify
  │
  → bash script runs resolve_template("spec-template")
      │
      ├── 1. Check .specify/templates/overrides/spec-template.md
      ├── 2. Check .specify/presets/{id}/templates/spec-template.md  (sorted by priority)
      ├── 3. Check .specify/extensions/{id}/templates/spec-template.md
      └── 4. Use .specify/templates/spec-template.md  (core default)
```

Composition strategies (nếu preset dùng `strategy: wrap`):

```
wrap: {CORE_TEMPLATE} → replaced với core content
prepend/append: content thêm trước/sau core
replace (default): full override
```

---

## State Management

### Install-time state

| File | Mô tả |
|------|-------|
| `.specify/integrations.json` | Installed integrations và settings |
| `.specify/extensions/.registry` | Installed extensions metadata |
| `.specify/presets/.registry` | Installed presets metadata + priority |
| `.specify/workflows/workflow-registry.json` | Installed workflows |

### Runtime state (Workflow engine)

| File | Mô tả |
|------|-------|
| `.specify/workflows/runs/{id}/state.json` | Execution state (step index, results) |
| `.specify/workflows/runs/{id}/inputs.json` | Resolved input values |
| `.specify/workflows/runs/{id}/log.jsonl` | Append-only event log |
| `.specify/workflows/.cache/*.json` | Catalog cache (1hr TTL) |

### User-generated artifacts

| File | Tạo bởi |
|------|---------|
| `.specify/memory/constitution.md` | `/speckit.constitution` |
| `specs/{branch}/spec.md` | `/speckit.specify` |
| `specs/{branch}/plan.md` | `/speckit.plan` |
| `specs/{branch}/tasks.md` | `/speckit.tasks` |

---

## Module Dependency Graph

```
__init__.py (CLI commands)
  ├── agents.py          (CommandRegistrar)
  ├── extensions.py      (ExtensionManager, ExtensionCatalog)
  ├── presets.py         (PresetManager, PresetCatalog, PresetResolver)
  ├── integration_runtime.py
  ├── integration_state.py
  ├── shared_infra.py
  ├── catalogs.py
  ├── workflows/__init__.py
  │     └── engine.py, base.py, expressions.py, catalog.py, steps/*
  ├── _assets.py
  ├── _console.py
  ├── _utils.py
  ├── _version.py
  └── _github_http.py
```

Không có circular dependency. Clean layered architecture.

---

## Coupling Analysis

### Tightly coupled (khó swap)
- **Typer** — CLI framework, dùng decorators khắp nơi trong `__init__.py`
- **Rich** — Console output, dùng trực tiếp trong `_console.py` và `__init__.py`
- **Platform-specific paths** — `platformdirs` cho user config dirs

### Loosely coupled (dễ replace/extend)
- **Template content** — pure markdown files, không có Python coupling
- **Agent directories** — `agents.py` dùng config-driven detection
- **Catalog sources** — pluggable via env var hoặc YAML config
- **Script engine** — bash và powershell đều được support, auto-selected
- **Extension/Preset system** — dựa trên YAML manifests, hoàn toàn declarative
