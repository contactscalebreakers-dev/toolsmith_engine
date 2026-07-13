# SB Toolsmith Pro - Development TODO

## Phase 1: Core Runtime ✅ COMPLETE
- [x] Event bus system (typed events, subscriptions, history)
- [x] Async scheduler (task scheduling, retries, dependencies)
- [x] PySide6 main window (dark theme, menus, docking)
- [x] Logging infrastructure (JSON logging, file rotation)
- [x] Application entry point (async initialization)
- [x] Architecture documentation
- [x] Project README

## Phase 2: DAG Engine & Plugin SDK ✅ COMPLETE
- [x] DAG engine (node execution, dependency resolution, retry/rollback)
- [x] Plugin manifest system (capabilities, permissions, sandbox boundaries)
- [x] RuntimeManager (venv lifecycle, subprocess supervision, snapshots)
- [x] Runtime snapshots (state capture, rollback, export/import)
- [x] Structured event stream (execution traces, event timelines)
- [ ] Plugin loader (dynamic loading, validation)
- [ ] Agent framework (base agent class, event-driven communication)
- [ ] Database schema (SQLite migrations)
- [ ] Unit tests for Phase 2

## Phase 3: Autonomous Agents ✅ COMPLETE
- [x] PlannerAgent (dependency analysis, DAG generation)
- [x] InstallerAgent (pip/poetry/uv detection, installation)
- [x] DependencyAgent (AST analysis, conflict resolution)
- [x] RepairAgent (health monitoring, auto-fix suggestions)
- [x] ExecutionAgent (process isolation, output capture)
- [x] PackagingAgent (tool bundling, manifest generation)
- [x] Agent orchestration and communication
- [ ] Unit tests for agents

## Phase 4: UI Components ✅ COMPLETE
- [x] Tool registry panel (list, search, filter)
- [x] Terminal widget (ANSI colors, scrollback, copy/paste)
- [ ] Graph editor (visual DAG editor, drag-drop)
- [x] Agent monitor panel (activity log, decision traces)
- [x] Diagnostics panel (tool health, dependencies)
- [ ] Workspace manager (multi-workspace support)
- [ ] Status bar and notifications
- [ ] Keyboard shortcuts and accelerators

## Phase 5: AI Integration ✅ COMPLETE
- [x] Ollama provider (local LLM integration)
- [x] OpenAI provider (cloud API integration)
- [x] Embeddings system (semantic search, similarity matching)
- [x] Tool router (intelligent tool selection with reasoning)
- [x] AI-assisted repair (suggestion engine, failure analysis)
- [x] Configuration UI for AI providers
- [ ] Unit tests for AI integration

## Phase 6: Runtime & Execution
- [ ] Sandbox system (process isolation, resource limits)
- [ ] Virtual environment manager (venv creation, cleanup)
- [ ] Process runner (subprocess management, timeouts)
- [ ] Terminal bridge (output streaming, ANSI handling)
- [ ] Execution monitoring (resource usage, health checks)
- [ ] Error handling and recovery
- [ ] Unit tests for runtime

## Phase 7: Database & Persistence
- [ ] SQLite store (schema, migrations)
- [ ] Tool registry persistence
- [ ] Execution history
- [ ] Snapshot storage
- [ ] Agent logs
- [ ] Plugin registry
- [ ] Workspace definitions
- [ ] Database tests

## Phase 8: Packaging & Distribution
- [ ] PyInstaller configuration
- [ ] Build script (exe generation)
- [ ] NSIS installer script
- [ ] Auto-updater mechanism
- [ ] Signed builds
- [ ] Release pipeline
- [ ] Windows packaging tests

## Phase 9: Testing & Quality
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] UI tests
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Code review checklist
- [ ] Documentation review

## Phase 10: Documentation & Deployment
- [ ] API documentation
- [ ] User guide
- [ ] Developer guide
- [ ] Plugin development guide
- [ ] Troubleshooting guide
- [ ] Deployment instructions
- [ ] Release notes

## Known Issues & Blockers
- [ ] PySide6 rendering on Windows 11 (needs local testing)
- [ ] Terminal embedding with ANSI colors (research required)
- [ ] Plugin hot-reloading (asyncio lifecycle management)
- [ ] Multi-workspace synchronization (database locking)

## Performance Targets
- [ ] Startup time: < 5 seconds
- [ ] Memory usage: < 200 MB base
- [ ] DAG execution: Parallel with dependency resolution
- [ ] Plugin loading: Lazy on-demand

## Security Considerations
- [ ] Sandbox process isolation
- [ ] Virtual environment isolation
- [ ] File system access control
- [ ] Network isolation options
- [ ] Plugin permission model
- [ ] Audit logging

## Future Enhancements (Post v1.0)
- [ ] Linux/macOS support
- [ ] Multi-workspace cloud sync
- [ ] Collaborative editing
- [ ] Advanced AI features
- [ ] Mobile companion app
- [ ] Kubernetes orchestration
- [ ] Enterprise licensing
