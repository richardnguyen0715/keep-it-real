# Spec Kit — Overview & Business Domain

## Bài toán nó giải quyết

Spec Kit giải quyết vấn đề **gap giữa specification và implementation** trong quy trình phát triển phần mềm với AI coding agents.

Khi dùng AI agent để code, có hai thái cực:
- **Vibe coding**: prompt mơ hồ → code rác, không maintainable
- **Spec-Driven Development (SDD)**: prompt có cấu trúc → code chất lượng, traceable

Spec Kit cung cấp scaffold để thực hành SDD: templates, scripts, CLI, và slash commands cho AI agents.

---

## Core Abstraction: Spec-Driven Development (SDD)

SDD **đảo ngược quyền lực** so với development truyền thống:

```
Traditional:    Code là truth  →  spec là ghi chú phụ
SDD:            Spec là truth  →  code là output được generate từ spec
```

Workflow cốt lõi:

```
Constitution (nguyên tắc dự án)
  → Spec (what & why — không phải how)
  → Clarify (resolve ambiguity)
  → Checklist (validate quality)
  → Plan (technical implementation — how)
  → Tasks (actionable task list)
  → Analyze (cross-artifact consistency)
  → Implement (execute)
```

---

## Core Abstractions

| Abstraction | Mô tả | File/Location |
|-------------|-------|---------------|
| **Constitution** | Nguyên tắc dự án — coding standards, architecture decisions, quality gates | `.specify/memory/constitution.md` |
| **Spec** | Functional requirement — user stories, acceptance scenarios, dưới dạng Given/When/Then | `specs/{branch}/spec.md` |
| **Plan** | Technical implementation plan — tech stack, architecture, data model, contracts | `specs/{branch}/plan.md` |
| **Tasks** | Actionable task list — grouped by user story, parallel execution flags | `specs/{branch}/tasks.md` |
| **Extension** | Plugin thêm command mới cho Spec Kit | `.specify/extensions/{id}/` |
| **Preset** | Override template/command hiện có của Spec Kit | `.specify/presets/{id}/` |
| **Workflow** | Automated multi-step pipeline YAML | `.specify/workflows/{id}/workflow.yml` |
| **Integration** | Cấu hình cho từng AI coding agent (Claude, Copilot, Gemini, v.v.) | `.specify/integrations/` |

---

## Value Thực Sự Nằm Ở Đâu

1. **Templates**: Định nghĩa output format cho AI — spec.md, plan.md, tasks.md đều có structure cụ thể để AI biết cần điền gì
2. **Slash commands** (`.md` files trong agent dirs): Là prompts được pre-built với workflow steps, injected `$ARGUMENTS` từ user
3. **Scripts** (bash/powershell): Auto-create git branch, detect feature number, setup directory structure
4. **CLI** (`specify`): Bootstrap toàn bộ ecosystem vào 1 project — templates, scripts, agent command files

Không có AI logic ở đây. Spec Kit là **scaffolding + prompt engineering** giúp AI agent làm việc có cấu trúc.

---

## Supported AI Coding Agents (30+)

Spec Kit hoạt động với 30+ agents. Tiêu biểu:
- **Claude Code** (`claude`) — markdown `.md` command files
- **GitHub Copilot** (`copilot`) — `.agent.md` + `.prompt.md`
- **Gemini CLI** (`gemini`) — `.toml` format
- **Codex CLI** (`codex`) — có thể dùng "skills mode" thay slash commands
- Cursor, Windsurf, Qwen, Tabnine, Kiro, Pi, Goose, Mistral, opencode, Forge, v.v.

---

## Development Phases Được Hỗ Trợ

| Phase | Scenario | Mô tả |
|-------|----------|-------|
| **0-to-1 (Greenfield)** | Build from scratch | Generate spec → plan → implement toàn bộ |
| **Creative Exploration** | Parallel implementations | Cùng 1 spec, nhiều plan/tech stack khác nhau |
| **Iterative (Brownfield)** | Add feature / modernize | Thêm feature vào project existing |

---

## Phiên Bản & License

- Package name: `specify-cli`
- Version hiện tại: `0.8.12.dev0`
- License: MIT (theo badge trên README)
- Không có trên PyPI chính thức — cài từ GitHub repo
