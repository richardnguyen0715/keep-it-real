# Spec Kit — Usage Guide (Full Workflow)

## Workflow Overview

### Lean path (quick experiments):

```
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

### Full path (production / ambiguous requirements):

```
/speckit.constitution
  → /speckit.specify
  → /speckit.clarify        # Resolve ambiguity
  → /speckit.checklist      # Validate requirements quality
  → /speckit.plan
  → /speckit.tasks
  → /speckit.analyze        # Cross-artifact consistency check
  → /speckit.implement
```

> **Context awareness**: Spec Kit auto-detect active feature dựa trên git branch hiện tại (format `001-feature-name`). Switch feature = switch branch.

---

## Core Commands

### `/speckit.constitution` — Thiết lập nguyên tắc dự án

Tạo hoặc update `.specify/memory/constitution.md` với governing principles của project. Chạy **1 lần đầu** khi setup project.

```bash
/speckit.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements.
```

```bash
/speckit.constitution This project follows a "Library-First" approach. All features must be implemented as standalone libraries first. We use TDD strictly.
```

**Output**: `.specify/memory/constitution.md`

AI agent sẽ reference file này trong tất cả các bước tiếp theo.

---

### `/speckit.specify` — Tạo feature specification

Mô tả **what** bạn muốn build và **why** — không focus vào tech stack.

```bash
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping.
```

**Những gì xảy ra tự động**:
1. Scan existing specs → xác định feature number tiếp theo (001, 002, ...)
2. Tạo git branch: `001-photo-albums`
3. Tạo directory: `specs/001-photo-albums/`
4. Generate `spec.md` từ template với user stories, acceptance scenarios (Given/When/Then), functional requirements, success criteria

**Output**: `specs/{branch}/spec.md`

---

### `/speckit.clarify` — Làm rõ ambiguities

Chạy **sau** `/speckit.specify`, **trước** `/speckit.plan`. AI sẽ hỏi clarifying questions để fill gaps.

```bash
/speckit.clarify Focus on security and performance requirements.
```

```bash
/speckit.clarify I want to clarify task card details: status changes, unlimited comments, user assignment.
```

Có thể chạy `/speckit.clarify` nhiều lần để tiếp tục refine.

**Output**: Update `specs/{branch}/spec.md`

---

### `/speckit.checklist` — Validate requirements quality

Generate custom checklist để kiểm tra spec completeness, clarity, consistency — như "unit tests for English".

```bash
/speckit.checklist
```

**Output**: `specs/{branch}/checklist.md`

---

### `/speckit.plan` — Tạo technical implementation plan

Cung cấp **how** — tech stack, architecture choices. AI đọc spec và tạo detailed technical plan.

```bash
/speckit.plan The application uses Vite with minimal libraries. Use vanilla HTML, CSS, JavaScript. Metadata stored in local SQLite.
```

```bash
/speckit.plan Use .NET Aspire, Postgres database. Frontend: Blazor server with drag-and-drop, real-time updates. REST API with projects, tasks, notifications endpoints.
```

**Những gì được generate**:
- `specs/{branch}/plan.md` — tech context, architecture, project structure
- `specs/{branch}/research.md` — Phase 0 research
- `specs/{branch}/data-model.md` — data model
- `specs/{branch}/quickstart.md` — validation scenarios
- `specs/{branch}/contracts/` — API contracts

---

### `/speckit.tasks` — Generate task list

Đọc plan.md (và data-model.md, contracts/ nếu có) → tạo actionable task list grouped by user story.

```bash
/speckit.tasks
```

**Output format**: `specs/{branch}/tasks.md`

```
[ID] [P?] [Story] Description
- [P] = can run in parallel
- [Story] = US1, US2, US3...
```

Phases:
- Phase 1: Setup (shared infrastructure)
- Phase 2: Foundational (blocking prerequisites)
- Phase 3+: User Story N (P1 → P2 → P3...)
- Phase N: Polish & cross-cutting concerns

---

### `/speckit.analyze` — Cross-artifact consistency check

Audit spec + plan + tasks để tìm gaps, contradictions, missing coverage. Chạy **sau** `/speckit.tasks`, **trước** `/speckit.implement`.

```bash
/speckit.analyze
```

Có thể chạy lại sau implement như extra review.

---

### `/speckit.implement` — Execute implementation

Execute toàn bộ tasks theo plan.

```bash
/speckit.implement
```

> **Tip — Phased Implementation**: Với project lớn, implement theo phases để tránh context saturation:
> ```bash
> /speckit.implement Phase 1 and Phase 2 only
> ```

---

### `/speckit.taskstoissues` — Convert tasks thành GitHub Issues

```bash
/speckit.taskstoissues
```

Convert tasks.md thành GitHub Issues để track và execute.

---

## CLI Commands (Terminal)

### Init & Setup

```bash
specify init <project>              # Bootstrap project
specify init .                      # Init in current dir
specify version                     # Show version
```

### Integration Management

```bash
specify integration list            # List installed integrations
specify integration add copilot     # Add integration
specify integration remove copilot  # Remove integration
```

### Extension Management

```bash
specify extension list              # List installed extensions
specify extension search            # Search available extensions
specify extension add git           # Install extension
specify extension add --dev /path   # Install local extension (dev)
specify extension remove git        # Remove extension
specify extension info git          # Show extension details
```

### Preset Management

```bash
specify preset list                 # List installed presets
specify preset search               # Search available presets
specify preset add lean             # Install preset
specify preset add lean --priority 1  # Install with priority
specify preset remove lean          # Remove preset
specify preset info lean            # Show preset details
specify preset resolve spec-template  # Debug template resolution
```

### Workflow Management

```bash
specify workflow list               # List installed workflows
specify workflow search             # Search available workflows
specify workflow add <id>           # Install workflow
specify workflow run <id>           # Run a workflow
specify workflow resume <run_id>    # Resume paused workflow
specify workflow status <run_id>    # Check run status
specify workflow remove <id>        # Remove workflow
```

### Self-Update

```bash
specify upgrade                     # Upgrade CLI to latest
```

---

## Ví Dụ End-to-End: Taskify

```bash
# 1. Setup
specify init taskify --integration copilot
cd taskify

# 2. Trong AI agent chat:
/speckit.constitution Taskify is "Security-First". All inputs validated. Microservices architecture.

/speckit.specify Develop Taskify, a team productivity platform with Kanban boards, 5 predefined users (1 PM + 4 engineers), 3 sample projects, drag-and-drop cards.

/speckit.clarify When launched, show user list. Click user → main view. Click project → Kanban board. Cards assigned to me = different color.

/speckit.checklist

/speckit.plan Use .NET Aspire, Postgres. Frontend: Blazor server with real-time updates. REST APIs: projects, tasks, notifications.

/speckit.tasks

/speckit.analyze

/speckit.implement
```
