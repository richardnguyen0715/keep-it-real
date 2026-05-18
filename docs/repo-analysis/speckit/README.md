# Spec Kit — Repo Analysis Index

Phân tích toàn diện repo [spec-kit](https://github.com/github/spec-kit) theo framework trong `policies/how-to-analyze-a-repo.md`.

## Documents

| File | Nội dung |
|------|----------|
| [overview.md](./overview.md) | Business domain, core philosophy, core abstractions |
| [setup.md](./setup.md) | Cài đặt, khởi tạo project, tích hợp AI agent |
| [usage.md](./usage.md) | Hướng dẫn đầy đủ workflow commands — specify, plan, tasks, implement, v.v. |
| [architecture.md](./architecture.md) | Architecture map, layers, entry points, data flow, state management |
| [customization.md](./customization.md) | Extensions, Presets, Local Overrides — khi nào dùng cái nào |
| [extension-guide.md](./extension-guide.md) | Hướng dẫn tạo extension từ đầu |
| [workflow-engine.md](./workflow-engine.md) | Workflow engine — step types, expressions, state persistence |
| [analysis.md](./analysis.md) | 15-câu checklist thực chiến, stable core vs volatile, customization strategy |

## TL;DR

**Spec Kit là gì**: CLI tool (`specify`) + bộ template + slash commands để thực hành Spec-Driven Development (SDD) với AI coding agents. Thay vì "vibe code", bạn viết spec → plan → tasks → implement có cấu trúc.

**Stack**: Python 3.11+, Typer CLI, Rich, PyYAML, uv/pipx.

**Extension points chính**: Extensions (thêm command mới) + Presets (override template/command hiện có) + Local Overrides (patch 1 file không cần tạo preset).

**Customization strategy**: Config-level → Preset/Extension → fork (hạn chế).
