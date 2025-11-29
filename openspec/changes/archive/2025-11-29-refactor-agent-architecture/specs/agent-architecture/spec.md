# Agent Architecture Specification

## ADDED Requirements

### Requirement: Agent Package Structure

The system SHALL organize each Agent as a fully self-contained package under `packages/agent_{name}/` directory with the following structure:
- `core/` - Agent core implementation (agent, model_factory, prompts, callbacks)
- `tools/` - Agent-specific tools
- `utils/` - Agent-specific utilities

Each Agent package SHALL be independently importable and publishable.

#### Scenario: Import Agent package successfully

- **WHEN** a developer imports `from packages.agent_fishing import FishingAgent, create_agent`
- **THEN** the import SHALL succeed without errors
- **AND** the `FishingAgent` class and `create_agent` function SHALL be available

#### Scenario: Agent tools are self-contained

- **WHEN** a developer imports `from packages.agent_fishing.tools import get_all_tools`
- **THEN** all fishing-related tools SHALL be returned
- **AND** no imports from `src/` directory SHALL be required

### Requirement: Application Layer Separation

The system SHALL separate application concerns into `apps/` directory:
- `apps/cli/` - Command-line interface application
- `apps/api/` - FastAPI REST API application

Each application SHALL import Agent packages as dependencies.

#### Scenario: CLI application runs independently

- **WHEN** a user executes `uv run python main.py`
- **THEN** the CLI SHALL start and accept user input
- **AND** the CLI SHALL use `packages.agent_fishing` for Agent functionality

#### Scenario: API application starts successfully

- **WHEN** a developer runs `uv run uvicorn apps.api.main:app`
- **THEN** the FastAPI server SHALL start on port 8000
- **AND** the `/health` endpoint SHALL return `{"status": "ok"}`

### Requirement: Shared Resources

The system SHALL maintain shared resources in `shared/` directory:
- `shared/config/` - Global configuration
- `shared/data/` - Shared data files (e.g., national_region_database)

Shared resources SHALL be importable by all packages and applications.

#### Scenario: Shared config is accessible

- **WHEN** any module imports `from shared.config import settings`
- **THEN** the global configuration SHALL be available
- **AND** environment variables SHALL be properly loaded

### Requirement: LangGraph Integration

The system SHALL support LangGraph integration via `langgraph.json`:
- Each Agent package SHALL export a module-level `agent` object
- Multiple Agents SHALL be registerable in the graphs configuration

#### Scenario: LangGraph discovers fishing agent

- **WHEN** LangGraph reads `langgraph.json` with path `./packages/agent_fishing:agent`
- **THEN** the fishing Agent SHALL be loaded successfully
- **AND** the Agent SHALL respond to user queries

#### Scenario: Multiple agents can be registered

- **WHEN** `langgraph.json` contains multiple graph entries
- **THEN** each Agent SHALL be independently loadable
- **AND** LangGraph dev server SHALL list all registered Agents

### Requirement: No Backward Compatibility

The system SHALL NOT maintain backward compatibility with `src/` directory imports.
All code SHALL use the new import paths under `packages/`, `apps/`, and `shared/`.

#### Scenario: Old import paths fail

- **WHEN** a developer attempts `from src.agent import create_optimized_fishing_agent`
- **THEN** the import SHALL raise `ModuleNotFoundError`
- **AND** the error message SHALL indicate `src` module does not exist

### Requirement: Test Organization

The system SHALL organize tests in root-level `tests/` directory:
- `tests/agent_fishing/` - Agent package tests
- `tests/api/` - API tests
- `tests/integration/` - Integration tests

#### Scenario: All tests pass after migration

- **WHEN** a developer runs `uv run pytest tests/`
- **THEN** all tests SHALL pass
- **AND** test coverage SHALL remain at or above pre-migration levels
