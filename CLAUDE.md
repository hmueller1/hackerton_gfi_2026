# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hackathon project (hackerton_gfi_2026) using the **BMAD framework** (v6.0.3) configured for Claude Code. There is no traditional build/test pipeline — the repository is a BMAD methodology workspace.

The primary user is **Jonathan**. All communication and document output should be in **German**.

## BMAD Module Architecture

BMAD modules live under `_bmad/` and outputs go to `_bmad-output/`:

```
_bmad/
  _config/          # Installation manifest, IDE config, per-agent customizations
  core/             # Core BMAD module: bmad-master agent, brainstorming/party-mode workflows
  bmb/              # BMAD Builder: agents and workflows for creating/editing agents, workflows, modules
  tea/              # Test Architecture Enterprise: test design, automation, ATDD, traceability, CI
_bmad-output/
  bmb-creations/    # Output from bmb (agent/workflow/module builder)
  test-artifacts/   # Output from tea (test-design, test-reviews, traceability)
doc/
  berufe/           # Source data: large PDF (gesamt-bpue-w25-data.pdf) split into 115 individual pages
```

### Installed Modules

| Module | Version | Purpose |
|--------|---------|---------|
| `core` | 6.0.3 | BMAD master agent, brainstorming, editorial review, adversarial review |
| `bmb`  | 0.1.6 | Build/edit/validate BMAD agents, workflows, and modules |
| `tea`  | 1.2.3 | Test architecture: design, automation, ATDD, traceability, CI, NFR assessment |

## Key Configuration

All module configs share these core values (`_bmad/*/config.yaml`):

- `user_name: Jonathan`
- `communication_language: German`
- `document_output_language: German`
- `output_folder: {project-root}/_bmad-output`

TEA-specific config (`_bmad/tea/config.yaml`):
- `risk_threshold: p1`
- `tea_use_playwright_utils: true`
- Test stack, CI platform, test framework, and browser automation are all set to `auto` (detected at runtime)

## BMAD Skills (Slash Commands)

Invoke BMAD agents and workflows via the Skill tool or slash commands:

- `/bmad-agent-bmad-master` — orchestrates all BMAD capabilities
- `/bmad-agent-tea-tea` — TEA test architect agent
- `/bmad-bmb-create-agent`, `/bmad-bmb-edit-agent`, `/bmad-bmb-validate-agent` — agent lifecycle
- `/bmad-bmb-create-workflow`, `/bmad-bmb-edit-workflow`, `/bmad-bmb-validate-workflow` — workflow lifecycle
- `/bmad-bmb-create-module`, `/bmad-bmb-edit-module`, `/bmad-bmb-validate-module` — module lifecycle

## TEA Workflow Step-File Architecture

TEA workflows in `_bmad/tea/workflows/testarch/` use a strict step-file pattern:

- Each workflow folder contains `workflow.md` (entrypoint), `steps-c/` (create), `steps-e/` (edit), `steps-v/` (validate)
- **Load one step at a time** — never preload future steps
- Follow the MANDATORY SEQUENCE exactly; no skipping or reordering

Available TEA workflows: `test-design`, `automate`, `atdd`, `test-review`, `trace`, `framework`, `ci`, `nfr-assess`

## Customizing BMAD Agents

Per-agent customization files are in `_bmad/_config/agents/` (e.g., `tea-tea.customize.yaml`, `core-bmad-master.customize.yaml`). These support overriding persona, adding memories, adding menu items, and adding custom prompts. All fields are optional and empty by default.

## Source Data

`doc/berufe/gesamt-bpue-w25-data.pdf` is the main source document (Berufspädagogische Überprüfung W25 data), also available as 115 individual page PDFs in `doc/berufe/pages/`.
