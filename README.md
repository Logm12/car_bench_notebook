# car-bench-ijcai-vsf

A2A evaluation harness for the CAR-bench Challenge at IJCAI-ECAI 2026. Participants build a dockerized agent, and the evaluator sends A2A messages, executes tools, and computes scores.

[![Paper](https://img.shields.io/badge/Paper-2601.22027-b31b1b.svg)](https://arxiv.org/abs/2601.22027)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Setup](#setup)
  - [Common Setup](#common-setup)
  - [Track 1 Setup](#track-1-setup)
  - [Track 2 Setup](#track-2-setup)
- [Running Evaluations](#running-evaluations)
  - [A. Local Smoke Test](#a-local-smoke-test)
  - [B. Full Local Test Set](#b-full-local-test-set)
  - [C. Docker Build and Test](#c-docker-build-and-test)
  - [D. GHCR Image Validation](#d-ghcr-image-validation)
- [Running Unit Tests](#running-unit-tests)
- [Project Structure](#project-structure)
- [Evaluation Metrics](#evaluation-metrics)
- [License](#license)

---

## Overview

[CAR-bench](https://github.com/CAR-bench/car-bench) evaluates tool-using LLM agents in realistic, uncertain, user-facing settings. The benchmark uses an in-car voice assistant domain with ambiguous requests, mutable vehicle state, domain policies, and unavailable capabilities.

This repository turns CAR-bench into a competition-ready A2A evaluation harness:

- The **evaluator** owns the simulated user, tools, environment state, trajectories, and scoring.
- The **agent under test** receives policy context, user messages, tool definitions, and tool results via A2A messages, then returns text or tool calls.
- The evaluator is the only component that executes CAR-bench tools.

The official competition has two tracks:

| Track | Goal |
|-------|------|
| **Track 1: Open Track** | Any model, provider, framework, or architecture. Focuses on agent harnessing and reliability design. |
| **Track 2: Cerebras Fast-Reasoning with Codex Pro** | Codex Pro-backed agents using `gpt-5.3-codex-spark` to turn fast inference into better reliability within the official time budget. |

CAR-bench benchmark scope:

| Dimension | Details |
|-----------|---------|
| Tools | 58 interconnected navigation, vehicle-control, charging, weather, and productivity tools |
| Policies | 19 domain-specific policies agents must follow |
| User model | LLM-simulated multi-turn user |
| Tasks | 254 public tasks across Base, Hallucination, and Disambiguation categories |
| Reliability metric | `Pass^3`: a task must pass all 3 independent trials |

---

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- Docker (for Docker-based scenarios)

---

## Quick Start

```bash
git clone https://github.com/YOUR_ORG/car-bench-ijcai-vsf.git
cd car-bench-ijcai-vsf

python3.11 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

./scripts/setup_car_bench.sh

cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

uv sync --extra track-1-agent --extra car-bench-evaluator

uv run car-bench-run scenarios/track_1_agent_under_test/local_smoke.toml --show-logs
```

---

## Setup

### Common Setup

Fork this repository first, then clone your fork. This gives you a clean place for your agent code, Dockerfile, scenario configs, and notes.

```bash
git clone https://github.com/YOUR_ORG_OR_USERNAME/car-bench-ijcai-vsf.git
cd car-bench-ijcai-vsf

python3.11 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

./scripts/setup_car_bench.sh
cp .env.example .env
```

`setup_car_bench.sh` clones the original CAR-bench repository into `third_party/car-bench/`. That checkout is treated as a local dependency for evaluator runs.

Set at least the evaluator key in `.env`:

```
GEMINI_API_KEY=your_key_here
```

### Track 1 Setup

Track 1 accepts any model provider. Install the Track 1 dependencies:

```bash
uv sync --extra track-1-agent --extra car-bench-evaluator
```

Add your provider keys to `.env`:

```
AGENT_LLM=anthropic/claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=your_key_here
```

For the full Track 1 reference, see [`src/track_1_agent_under_test/README.md`](src/track_1_agent_under_test/README.md).

### Track 2 Setup

Track 2 uses Codex Pro-backed inference with `gpt-5.3-codex-spark`.

```bash
uv sync --extra car-bench-evaluator
```

Install and authenticate the Codex CLI following the [official instructions](https://developers.openai.com/codex/cli). For Docker runs, use a dedicated Codex home:

```bash
mkdir -p "$HOME/.codex-car-bench"
CODEX_HOME="$HOME/.codex-car-bench" codex login
CODEX_HOME="$HOME/.codex-car-bench" codex login status
```

Then set the path in `.env`:

```
CODEX_HOME_HOST=/Users/yourname/.codex-car-bench
GEMINI_API_KEY=your_key_here
```

Track 2 reference agent READMEs:

| Reference | README |
|-----------|--------|
| Direct Codex JSON agent | [`src/track_2_agent_under_test_codex/README.md`](src/track_2_agent_under_test_codex/README.md) |
| Planner/executor agent | [`src/track_2_agent_under_test_codex_planner/README.md`](src/track_2_agent_under_test_codex_planner/README.md) |
| Python-call DSL agent | [`src/track_2_agent_under_test_codex_python/README.md`](src/track_2_agent_under_test_codex_python/README.md) |

---

## Running Evaluations

Scenarios are configured by TOML files in the `scenarios/` directory. Each agent directory contains a standard set of six scenario files:

| Scenario File | Purpose |
|--------------|---------|
| `local_smoke.toml` | Local Python, train split, one task per type, one trial |
| `local_test_set.toml` | Local Python, public test split, three trials |
| `local_docker_smoke.toml` | Local Docker build, train smoke |
| `local_docker_test_set.toml` | Local Docker build, public test split |
| `ghcr_smoke.toml` | Published GHCR image, train smoke |
| `ghcr_test_set.toml` | Published GHCR image, public test split |

Use the progression: local smoke -> local test set -> Docker smoke -> Docker test set -> GHCR.

### A. Local Smoke Test

The fastest way to iterate. Agents run as local Python processes.

```bash
# Track 1
uv run car-bench-run scenarios/track_1_agent_under_test/local_smoke.toml --show-logs

# Track 2: Direct Codex JSON
uv run car-bench-run scenarios/track_2_agent_under_test_codex/local_smoke.toml --show-logs

# Track 2: Planner/executor
uv run car-bench-run scenarios/track_2_agent_under_test_codex_planner/local_smoke.toml --show-logs

# Track 2: Python-call DSL
uv run car-bench-run scenarios/track_2_agent_under_test_codex_python/local_smoke.toml --show-logs
```

### B. Full Local Test Set

Run only after the smoke scenario passes. These are development validation runs, not official final evaluation.

```bash
# Track 1
uv run car-bench-run scenarios/track_1_agent_under_test/local_test_set.toml --show-logs
```

### C. Docker Build and Test

Use this before publishing. It verifies your Dockerfile and runtime environment without local Python process assumptions.

**Step 1 - Generate the compose file:**

```bash
# Track 1
uv run python generate_compose.py --scenario scenarios/track_1_agent_under_test/local_docker_smoke.toml
```

**Step 2 - Run:**

```bash
docker compose --env-file .env \
  -f scenarios/track_1_agent_under_test/docker-compose.yml \
  up --abort-on-container-exit
```

Replace the scenario directory with the relevant Track 2 directory for Track 2 agents.

### D. GHCR Image Validation

Build and push an `linux/amd64` image, then validate it before submission:

```bash
# Build
docker build --platform linux/amd64 \
  -f src/track_1_agent_under_test/Dockerfile.track-1-agent-under-test \
  -t ghcr.io/yourusername/your-agent:latest .

# Push
docker push ghcr.io/yourusername/your-agent:latest

# Generate compose and run
uv run python generate_compose.py \
  --scenario scenarios/track_1_agent_under_test/ghcr_smoke.toml

docker compose --env-file .env \
  -f scenarios/track_1_agent_under_test/docker-compose.yml \
  up --abort-on-container-exit
```

Results are written to `output/<agent-name>/` with filenames that include the timestamp, scenario name, task selection, and trial count.

---

## Running Unit Tests

The test suite covers the A2A response contract, scenario file structure, and agent internals. Tests use Python's built-in `unittest` module.

**Run all tests:**

```bash
uv run python -m unittest discover tests
```

**Run a single test file:**

```bash
uv run python -m unittest tests.test_scenario_contract
uv run python -m unittest tests.test_a2a_response_contract
uv run python -m unittest tests.test_codex_planner_agent
uv run python -m unittest tests.test_codex_python_call_agent
```

**Run a single test case:**

```bash
uv run python -m unittest tests.test_scenario_contract.ScenarioContractTest.test_compose_generation_uses_evaluator_and_agent_under_test
```

**Verbose output:**

```bash
uv run python -m unittest discover -v tests
```

The test suite includes:

| File | What it covers |
|------|---------------|
| `test_scenario_contract.py` | Scenario TOML structure, compose generation, output path logic, client/runner parsing |
| `test_a2a_response_contract.py` | A2A message serialization, token usage parsing, turn metrics, Codex agent response shapes |
| `test_codex_planner_agent.py` | Planner/executor agent internal logic |
| `test_codex_python_call_agent.py` | Python-call DSL agent response and action handling |

> **Note:** Some tests require the Track 2 agent dependencies to be installed. If you are only working with Track 1, some tests may fail due to missing imports. Install Track 2 dependencies to run the full suite.

---

## Project Structure

```text
.
├── src/
│   ├── agentbeats/                                     A2A runner helpers and client CLI
│   │   ├── Dockerfile.a2a-client
│   │   ├── client.py                                   Async A2A HTTP client
│   │   ├── client_cli.py                               CLI entry point for running scenarios
│   │   ├── evaluator_executor.py                       Evaluator-side agent executor
│   │   ├── models.py                                   Shared data models
│   │   ├── run_scenario.py                             Scenario runner (car-bench-run entrypoint)
│   │   ├── sync_client.py                              Synchronous A2A client wrapper
│   │   └── tool_provider.py                            Tool call forwarding helpers
│   │
│   ├── evaluator/                                      CAR-bench evaluator A2A server
│   │   ├── Dockerfile.evaluator
│   │   ├── car_bench_evaluator.py                      Main evaluator logic
│   │   ├── car_bench_paths.py                          Path resolution for CAR-bench assets
│   │   └── server.py                                   Evaluator HTTP server entrypoint
│   │
│   ├── track_1_agent_under_test/                       Track 1 minimal template agent
│   │   ├── Dockerfile.track-1-agent-under-test
│   │   ├── car_bench_agent.py                          Agent executor implementation
│   │   ├── server.py                                   A2A server entrypoint
│   │   └── README.md
│   │
│   ├── track_2_agent_under_test_codex/                 Track 2 direct Codex JSON agent
│   │   ├── Dockerfile.track-2-agent-under-test-codex
│   │   ├── car_bench_agent.py                          Agent executor with Codex JSON output
│   │   ├── codex_client.py                             Codex CLI subprocess client
│   │   ├── server.py                                   A2A server entrypoint
│   │   └── README.md
│   │
│   ├── track_2_agent_under_test_codex_planner/         Track 2 planner/executor agent
│   │   ├── Dockerfile.track-2-agent-under-test-codex-planner
│   │   ├── planner_agent.py                            Planner + executor agent logic
│   │   ├── server.py                                   A2A server entrypoint
│   │   └── README.md
│   │
│   ├── track_2_agent_under_test_codex_python/          Track 2 Python-call DSL agent
│   │   ├── Dockerfile.track-2-agent-under-test-codex-python
│   │   ├── python_call_agent.py                        Python-call DSL agent logic
│   │   ├── server.py                                   A2A server entrypoint
│   │   └── README.md
│   │
│   ├── extract_trajectories.py                         Utility to extract evaluation trajectories
│   ├── logging_utils.py                                Shared logging setup
│   ├── tool_call_types.py                              Shared tool-call data models (Protobuf wrappers)
│   └── turn_metrics.py                                 Shared metadata keys for turn-level metrics
│
├── scenarios/
│   ├── track_1_agent_under_test/
│   │   ├── local_smoke.toml                            Local Python, train split, 1 task per type, 1 trial
│   │   ├── local_test_set.toml                         Local Python, public test split, 3 trials
│   │   ├── local_docker_smoke.toml                     Local Docker build, train smoke
│   │   ├── local_docker_test_set.toml                  Local Docker build, public test split
│   │   ├── ghcr_smoke.toml                             GHCR image, train smoke
│   │   └── ghcr_test_set.toml                          GHCR image, public test split
│   │
│   ├── track_2_agent_under_test_codex/                 Same 6-file matrix for Track 2 Codex JSON
│   ├── track_2_agent_under_test_codex_planner/         Same 6-file matrix for Track 2 planner
│   ├── track_2_agent_under_test_codex_python/          Same 6-file matrix for Track 2 Python-call
│   └── README.md                                       Scenario config reference
│
├── tests/
│   ├── test_a2a_response_contract.py                   A2A message shapes, token usage, turn metrics
│   ├── test_codex_planner_agent.py                     Planner/executor agent internal logic
│   ├── test_codex_python_call_agent.py                 Python-call DSL agent response handling
│   └── test_scenario_contract.py                       Scenario TOML structure and compose generation
│
├── docs/
│   ├── development-guide.md                            A2A turn contract — inbound/outbound message shapes
│   ├── agent-under-test-harnessing.md                  Allowed agent harness boundaries
│   ├── codex-harness-patterns.md                       Track 2 model and harness patterns
│   └── a2a-introduction.md                             A2A protocol background
│
├── notebooks/
│   ├── qwen_coder_baseline.ipynb                       vLLM-based Qwen baseline evaluation
│   ├── finetune_llm.ipynb                              Fine-tuning with ORPO
│   ├── finetune_llm_dpo.ipynb                          Fine-tuning with DPO
│   ├── offline_finetune_llm_local_pc.ipynb             Offline ORPO fine-tuning (local)
│   └── offline_finetune_llm_dpo_local_pc.ipynb         Offline DPO fine-tuning (local)
│
├── data/
│   └── ft_dataset.jsonl                                Fine-tuning dataset
│
├── scripts/
│   ├── setup_car_bench.sh                              Clones third_party/car-bench
│   ├── demo_function_calling.py                        Function calling demonstration script
│   └── make_offline_notebooks.py                       Generates offline notebook variants
│
├── third_party/
│   └── car-bench/                                      Official CAR-bench repo (local dependency)
│
├── generate_compose.py                                 Generates docker-compose.yml from scenario TOML
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Evaluation Metrics

CAR-bench uses three task categories:

| Task Type | Public Tasks | What It Tests |
|-----------|:---:|--------------|
| Base | 100 | Correct tool use, final state, intermediate state, and policy compliance |
| Hallucination | 98 | Whether the agent acknowledges missing capabilities or data instead of fabricating |
| Disambiguation | 56 | Whether the agent resolves ambiguity through preferences or clarification before acting |

Each task receives fine-grained scores across action correctness, information-gathering tool use, tool execution validity, policy compliance, and user end-conversation behavior. A task reward is 1 only when all required metrics pass.

| Metric | Meaning |
|--------|---------|
| `Pass^3` | Task passes in all 3 independent trials. This is the main deployment-readiness score. |
| `Pass@3` | Task passes in at least 1 of 3 trials. This measures latent capability. |

For reward calculator details, see `third_party/car-bench/car_bench/envs/reward_calculators.py` after running `./scripts/setup_car_bench.sh`.

---

## License

MIT. See [LICENSE](LICENSE) for the full text.

The bundled CAR-bench code in `third_party/car-bench/` is subject to its own license. See [`third_party/README.md`](third_party/README.md) for details.

---

## Further Reading

- [A2A turn contract](docs/development-guide.md) - exact message shapes your agent must handle
- [Harnessing boundaries](docs/agent-under-test-harnessing.md) - what internal operations are and are not allowed
- [Track 2 harness patterns](docs/codex-harness-patterns.md) - Codex-specific model and harness patterns
- [A2A protocol](docs/a2a-introduction.md) - background on the Agent-to-Agent protocol
- [Original CAR-bench repo](https://github.com/CAR-bench/car-bench)
- [Competition website](https://car-bench.github.io/car-bench/)
- [Paper](https://arxiv.org/abs/2601.22027)
