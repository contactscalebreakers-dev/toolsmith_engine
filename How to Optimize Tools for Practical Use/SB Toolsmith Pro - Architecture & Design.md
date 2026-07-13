# SB Toolsmith Pro - Architecture & Design

## Overview

**SB Toolsmith Pro** is a production-grade autonomous Windows 11 desktop platform for tool management, isolated execution, AI-assisted debugging, and agentic workflow orchestration.

### Core Principles

1. **Python-First**: Pure Python runtime with PySide6 UI
2. **Event-Driven**: All components communicate through typed event bus
3. **Modular**: Plugin architecture for extensibility
4. **Autonomous**: Agent-based orchestration with self-healing
5. **Portable**: Reproducible builds, no machine-specific coupling
6. **Offline-Capable**: Local-first execution with optional cloud integration
7. **Observable**: Comprehensive logging and runtime introspection

---

## System Architecture

### Core Module (`/core`)

**Responsibility**: Runtime orchestration, event management, scheduling, DAG execution

#### Components

- **event_bus.py**: Typed event system for inter-component communication
  - Event registry with type validation
  - Async event dispatch and subscriptions
  - Event history and replay capability
  - Priority-based event queuing

- **scheduler.py**: Async task scheduling and execution
  - Coroutine-based task scheduling
  - Retry policies with exponential backoff
  - Task dependency management
  - Cancellation support

- **runtime_manager.py**: Central orchestration point
  - Manages tool lifecycle (register, initialize, execute, cleanup)
  - Coordinates agent interactions
  - Handles workspace state
  - Manages runtime snapshots

- **dag_engine.py**: Directed Acyclic Graph execution engine
  - Node-based workflow definition
  - Parallel execution with dependency resolution
  - Retry and rollback support
  - Progress tracking and cancellation

- **snapshot_manager.py**: Runtime state persistence
  - Captures tool environment state
  - Enables rollback to previous snapshots
  - Manages snapshot storage and cleanup
  - Supports incremental snapshots

---

### Agent System (`/agents`)

**Responsibility**: Autonomous decision-making and task execution

#### Agents

1. **PlannerAgent**: Analyzes tool requirements and creates execution plans
   - Infers dependencies from source code
   - Generates DAG execution plans
   - Optimizes execution order
   - Handles plan modification and adaptation

2. **InstallerAgent**: Manages dependency installation
   - Detects package manager (pip, poetry, uv)
   - Installs dependencies in isolated environments
   - Handles version conflicts
   - Provides installation rollback

3. **DependencyAgent**: Analyzes and resolves dependencies
   - AST-based dependency inference
   - Dependency graph visualization
   - Conflict detection and resolution
   - Version compatibility checking

4. **RepairAgent**: Autonomous problem detection and fixing
   - Monitors tool health
   - Detects runtime failures
   - Suggests and applies fixes
   - Learns from repair history

5. **ExecutionAgent**: Runs tools with monitoring
   - Executes in isolated sandboxes
   - Captures output and errors
   - Monitors resource usage
   - Handles timeouts and interrupts

6. **PackagingAgent**: Builds and exports tools
   - Creates distributable packages
   - Generates manifests
   - Handles versioning
   - Supports multiple formats (zip, wheel, exe)

#### Agent Communication

- All agents communicate through **event bus**
- Agents emit structured events for state changes
- No direct agent-to-agent coupling
- Event-driven request/response pattern

---

### Plugin System (`/plugins`)

**Responsibility**: Runtime extensibility

#### Structure

```
/plugins
  /sdk/
    plugin_base.py      # Base plugin class
    manifest_schema.py   # Plugin manifest validation
    hooks.py            # Lifecycle hooks
  /loaders/
    plugin_loader.py    # Dynamic plugin loading
    validator.py        # Plugin validation
  /manifests/
    example_plugin.yaml # Example plugin manifest
```

#### Plugin Lifecycle

1. **Discovery**: Scan plugin directories
2. **Validation**: Verify manifest and dependencies
3. **Loading**: Import and instantiate plugin
4. **Initialization**: Call plugin setup hooks
5. **Registration**: Register commands and event handlers
6. **Execution**: Plugin runs within sandbox
7. **Cleanup**: Call plugin teardown hooks

---

### Runtime System (`/runtime`)

**Responsibility**: Tool execution isolation and process management

#### Components

- **sandbox.py**: Execution isolation
  - Virtual environment management
  - Resource limits (CPU, memory, disk)
  - File system isolation
  - Network isolation options

- **venv_manager.py**: Python virtual environment management
  - Creates isolated venvs per tool
  - Manages Python versions
  - Handles venv cleanup
  - Supports venv snapshots

- **process_runner.py**: Subprocess execution
  - Spawns isolated processes
  - Captures stdout/stderr
  - Manages timeouts
  - Handles signal forwarding

- **terminal_bridge.py**: Terminal output streaming
  - Real-time output capture
  - ANSI color preservation
  - Output buffering and flushing
  - Terminal emulation

---

### UI System (`/ui`)

**Responsibility**: Windows 11 native user interface

#### Components

- **main_window.py**: Main application window
  - Docking system integration
  - Menu bar and toolbars
  - Status bar and notifications
  - Keyboard shortcuts

- **docking_system.py**: Dockable panel management
  - Tool registry panel
  - Terminal panel
  - Agent monitor panel
  - Diagnostics panel
  - Graph editor panel

- **graph_editor.py**: Visual DAG editor
  - Node creation and connection
  - Drag-and-drop interface
  - Real-time preview
  - Export to execution format

- **terminal_widget.py**: Embedded terminal
  - ANSI color support
  - Scrollback buffer
  - Copy/paste support
  - Search functionality

- **workspace_manager.py**: Workspace UI management
  - Multi-workspace support
  - Workspace persistence
  - Quick access panel
  - Recent items

---

### AI Integration (`/ai`)

**Responsibility**: LLM integration and intelligent features

#### Components

- **ollama_provider.py**: Local Ollama integration
  - Connects to local Ollama instance
  - Supports model switching
  - Handles streaming responses
  - Manages context windows

- **openai_provider.py**: OpenAI-compatible endpoints
  - Supports OpenAI API
  - Supports Azure OpenAI
  - Supports other compatible endpoints
  - API key management

- **embeddings.py**: Embedding generation
  - Code embeddings for similarity
  - Dependency embeddings
  - Error embeddings for repair suggestions

- **tool_router.py**: Intelligent tool routing
  - Analyzes tool requirements
  - Routes to appropriate agents
  - Suggests repair strategies
  - Learns from outcomes

---

### Database (`/database`)

**Responsibility**: Persistent state management

#### Components

- **sqlite_store.py**: SQLite-based storage
  - Tool registry
  - Execution history
  - Agent logs
  - Snapshots metadata
  - Configuration

#### Schema

- `tools`: Tool registry
- `executions`: Execution history
- `snapshots`: Snapshot metadata
- `agent_logs`: Agent decision logs
- `plugins`: Plugin registry
- `workspaces`: Workspace definitions

---

### Packaging (`/packaging`)

**Responsibility**: Distribution and deployment

#### Components

- **pyinstaller_builder.py**: PyInstaller integration
  - Builds standalone executables
  - Handles dependencies
  - Manages hooks
  - Creates Windows installer

- **updater.py**: Auto-update mechanism
  - Checks for updates
  - Downloads and installs
  - Rollback support
  - Delta updates

---

### Utilities (`/utils`)

**Responsibility**: Common utilities and helpers

- **config.py**: Configuration management
- **logging.py**: Structured logging
- **paths.py**: Portable path handling
- **validators.py**: Input validation
- **serialization.py**: JSON/YAML serialization

---

## Data Flow

### Tool Execution Flow

```
User Action
    ↓
UI Event
    ↓
RuntimeManager
    ↓
PlannerAgent (create DAG)
    ↓
DAGEngine (execute plan)
    ├→ DependencyAgent (analyze)
    ├→ InstallerAgent (install)
    ├→ ExecutionAgent (run)
    └→ RepairAgent (on failure)
    ↓
SnapshotManager (save state)
    ↓
UI Update (display results)
```

### Event Flow

```
Agent Action
    ↓
Emit Event (EventBus)
    ↓
Event Subscribers
    ├→ UI Components (update display)
    ├→ Logger (record)
    ├→ Database (persist)
    └→ Other Agents (react)
```

---

## Execution Model

### Synchronous vs Asynchronous

- **UI Thread**: Responsive, non-blocking
- **Event Bus**: Async event dispatch
- **Agents**: Async task execution
- **Scheduler**: Coroutine-based scheduling
- **Process Runner**: Subprocess isolation

### Concurrency Strategy

- **asyncio**: Core async framework
- **ThreadPoolExecutor**: CPU-bound tasks
- **ProcessPoolExecutor**: Isolation for untrusted code
- **Queue-based**: UI-to-runtime communication

---

## Failure Recovery

### Retry Strategy

1. **Transient Failures**: Automatic retry with backoff
2. **Dependency Failures**: RepairAgent suggests fixes
3. **Execution Failures**: Rollback to last snapshot
4. **Agent Failures**: Escalate to user

### Rollback Mechanism

1. **Snapshot Capture**: Before each major operation
2. **Rollback Trigger**: On failure or user request
3. **State Restoration**: Restore from snapshot
4. **Verification**: Verify restoration success

---

## Security Model

### Isolation Levels

1. **Process Isolation**: Each tool runs in separate process
2. **Environment Isolation**: Separate venvs per tool
3. **File System Isolation**: Restricted access paths
4. **Network Isolation**: Optional network restrictions
5. **Resource Limits**: CPU, memory, disk quotas

### Permission Model

- **Plugin Permissions**: Manifest-declared capabilities
- **Tool Permissions**: Scope-based access control
- **User Permissions**: Role-based access control
- **Audit Trail**: All actions logged

---

## Performance Considerations

### Startup Time

- Lazy loading of plugins
- Cached dependency graphs
- Precompiled bytecode
- Minimal UI initialization

### Memory Usage

- Streaming output processing
- Incremental snapshot storage
- Lazy agent initialization
- Garbage collection tuning

### Execution Speed

- Parallel DAG execution
- Dependency caching
- Process pooling
- Optimized event dispatch

---

## Deployment Strategy

### Development

- Source-based installation
- Direct Python execution
- Hot reloading support
- Debug logging

### Production

- PyInstaller bundled executable
- Signed Windows installer
- Auto-update mechanism
- Telemetry (optional)

### Distribution

- Standalone .exe
- Portable zip archive
- Windows Store (future)
- Chocolatey package (future)

---

## Future Roadmap

### Phase 5+

- Multi-workspace cloud sync
- Collaborative editing
- Advanced AI features (code generation)
- Mobile companion app
- Linux/macOS support
- Docker integration
- Kubernetes orchestration
- Enterprise licensing

---

## References

- PySide6 Documentation: https://doc.qt.io/qtforpython/
- asyncio: https://docs.python.org/3/library/asyncio.html
- PyInstaller: https://pyinstaller.org/
- SQLite: https://www.sqlite.org/
