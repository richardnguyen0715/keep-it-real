# Spec Kit — Setup & Installation

## Prerequisites

- Python 3.11+
- Git
- `uv` (recommended) hoặc `pipx`
- Một AI coding agent: Claude Code, GitHub Copilot, Gemini CLI, v.v.

---

## Cài `uv` (nếu chưa có)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 1. Cài Specify CLI

### Persistent Installation (Recommended)

```bash
# Thay vX.Y.Z bằng version mới nhất từ Releases
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

Sau khi install, dùng `specify` trực tiếp:

```bash
specify init my-project --integration copilot
```

### One-time (Không cần install)

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init my-project
```

### Dùng pipx

```bash
pipx install git+https://github.com/github/spec-kit.git
```

### Upgrade

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

### Verify

```bash
specify version
```

> ⚠️ **Lưu ý**: Không dùng `pip install specify-cli` từ PyPI — đó là package không liên quan.

---

## 2. Khởi Tạo Project

### Tạo project mới

```bash
specify init my-project --integration copilot
cd my-project
```

### Init trong thư mục hiện tại

```bash
specify init .
# hoặc
specify init --here

# Force merge vào thư mục đã có files
specify init . --force
```

### Chọn AI agent integration

```bash
specify init my-project --integration claude       # Claude Code
specify init my-project --integration copilot      # GitHub Copilot
specify init my-project --integration gemini       # Gemini CLI
specify init my-project --integration codex        # Codex CLI
specify init my-project --integration codebuddy    # Codebuddy
specify init my-project --integration pi           # Pi
```

Interactive mode (prompt chọn agent):

```bash
specify init my-project  # Sẽ hỏi bạn chọn agent
```

### Chọn script type

```bash
specify init my-project --script sh   # Bash (mặc định Linux/macOS)
specify init my-project --script ps   # PowerShell (mặc định Windows)
```

### Skills mode (Codex CLI)

```bash
specify init . --integration codex --integration-options="--skills"
```

### Bỏ qua agent tools check

```bash
specify init my-project --integration claude --ignore-agent-tools
```

---

## 3. Cấu Trúc Project Sau Init

```
my-project/
├── .specify/
│   ├── templates/          # Core templates (spec, plan, tasks, v.v.)
│   │   └── overrides/      # Project-local template overrides
│   ├── memory/
│   │   └── constitution.md # Project principles (tạo bằng /speckit.constitution)
│   ├── scripts/
│   │   ├── bash/           # .sh scripts
│   │   └── powershell/     # .ps1 scripts
│   ├── extensions/         # Installed extensions
│   ├── presets/            # Installed presets
│   └── workflows/          # Installed workflows
├── .claude/
│   └── commands/           # Slash command .md files (nếu dùng Claude)
├── .github/
│   └── agents/             # Copilot command files (nếu dùng Copilot)
├── specs/                  # Feature specs, plans, tasks (tạo trong quá trình dùng)
└── ...
```

---

## 4. Thêm Integration Vào Project Đã Có

```bash
# Thêm integration mới
specify integration add copilot

# List integrations đã install
specify integration list
```

---

## 5. Thêm Extensions & Presets

```bash
# Search extensions
specify extension search

# Cài extension
specify extension add git

# Search presets
specify preset search

# Cài preset
specify preset add lean
```

---

## 6. Enterprise / Air-Gapped Installation

Nếu môi trường không có internet access:

1. Build wheel locally từ source:
   ```bash
   git clone https://github.com/github/spec-kit.git
   cd spec-kit
   uv build
   ```

2. Copy wheel file sang môi trường air-gapped

3. Install từ wheel:
   ```bash
   uv tool install specify-cli --from ./dist/specify_cli-*.whl
   ```

Templates và core assets đã được bundle vào wheel (xem `pyproject.toml` `force-include` section) — không cần network sau khi install.
