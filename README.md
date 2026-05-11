# keep-it-real

Stay up to date by following state of the art.

## Research Operating System Layout

This repository is structured as a long-term AI research workspace that balances:

1. Fast experimentation
2. Easy retrieval after months
3. Reusable shared components
4. Clean organization (not a notebook dump)

```txt
.
├── README.md
├── INDEX.md
├── TIMELINE.md
├── pyproject.toml
├── requirements/
├── .env.example
├── .gitignore
├── Makefile
├── docs/
├── shared/
├── experiments/
├── papers/
├── projects/
├── benchmarks/
├── datasets/
├── notebooks/
├── scripts/
├── configs/
└── domains/
```

## Layer Intent

- `experiments/`: short-lived, fast trend tests
- `papers/`: paper re-implementations and reproduction logs
- `projects/`: maturing systems with stronger quality bar
- `shared/`: reusable infra/components to avoid copy-paste
- `benchmarks/`: cross-experiment evaluations and comparisons
- `docs/`: notes, ideas, paper summaries, benchmark notes
- `configs/`: train/eval/inference/dataset configuration files
- `domains/`: domain-level grouping for agents/rag/vision/voice/etc.

## Experiment Naming Convention

Use date-prefixed names for chronology and cleanup:

- `2026-05-12-qwen3-tool-calling`
- `2026-05-rag-reranker-ablation`
- `2026-05-openmanus-clone`

Each experiment folder should contain:

- `README.md`
- `notes.md`
- `run.py`
- `config.yaml`
- `results/`
- `artifacts/`

## Data & Model Artifacts

Do not commit large datasets or checkpoints.
Use remote storage (Git LFS, Hugging Face Hub, S3, MinIO, Cloudflare R2) when needed.

## Quick Start

```bash
make setup
make test
```
