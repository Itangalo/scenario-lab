# Instructions for Agents

You are working on **Scenario Lab**, an AI-powered scenario simulation framework.

## 🛑 CRITICAL: Ground Truth

Before proposing or implementing **ANY** changes to the system architecture, logic, or data models, you **MUST** read the ground truth document:

👉 [**docs/ARCHITECTURE.md**](../docs/ARCHITECTURE.md)

This document describes the intended design and behavior of the system. If your task involves changing how the system works, you must:
1.  Verify your plan against the architecture document.
2.  Update the architecture document to reflect your changes **before** or **during** your implementation.

## Core Philosophy (Do Not Break)

1.  **Pure LLM Architecture:** Do not move game logic (rules, calculations, narrative) into Python. Python is for orchestration only.
2.  **Jinja2 Templates:** Use the template system for prompt engineering. Do not hardcode prompt strings in Python.
3.  **Incremental Persistence:** Ensure all data is saved immediately. Do not wait until the end of a run.

## Project Structure

-   **`scenario_lab/`**: Core Python package (Orchestrator, Loader, LLM Client).
-   **`templates/`**: Jinja2 templates for user prompts.
-   **`scenarios/`**: Scenario data (YAML/Markdown) and specific overrides.
-   **`tests/evals/`**: LLM evaluation suite.

## Common Tasks

-   **Adding Features:** Check `ARCHITECTURE.md` first.
-   **Modifying Prompts:** Edit files in `templates/user-prompts/`, not Python code.
-   **Running Scenarios:** Use the CLI: `python -m scenario_lab.cli scenarios/sweden-ai-2030`.
