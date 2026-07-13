# SB Toolsmith Web - User Documentation

## Overview

**SB Toolsmith** is an elegant, production-ready tool registry and management dashboard for Python developers. It provides a unified interface to discover, manage, diagnose, and execute your Python tools with full visibility and control.

## Getting Started

### Accessing the Dashboard

1. Navigate to the SB Toolsmith application
2. Click **"Sign In to Get Started"** to authenticate with your Manus account
3. You'll be taken to the **Tool Registry Dashboard**

### First Steps

When you first access the dashboard, you'll see an empty state with a prompt to add your first tool. Click **"Add Tool"** to begin registering tools.

## Core Features

### 1. Tool Registry Dashboard

The main dashboard displays all your registered tools in a clean, organized list. Each tool entry shows:

- **Tool Name**: The display name of your tool
- **Install Status**: Visual indicator (✓ for installed, ○ for not installed)
- **Backend Used**: The package manager used (pip, poetry, uv, or auto-detected)
- **Smoke Test Status**: Pass (✓) or Fail (✗) indicator for the last test run

Click any tool in the list to view its details and manage it.

### 2. Search, Sort & Filter

The unified control bar at the top of the tool list provides three ways to discover tools:

#### Search
- Type a tool name to instantly filter the list
- Click the **X** button to clear your search

#### Filter by Status
- **All Tools**: Show all registered tools
- **Installed**: Show only tools with successful installations
- **Not Installed**: Show only tools awaiting installation

#### Sort
- **Name (A-Z)**: Alphabetical order
- **Status**: Installed tools first, then not installed
- **Recently Updated**: Most recently modified tools first

### 3. Add Tool

Register a new Python tool by providing:

- **Tool Name**: A descriptive name for your tool
- **Source**: Either a file path, directory path, or upload a `.py`, `.zip`, or `.tar.gz` file
- **Entrypoint**: The main script or module to execute (auto-detected when possible)

The system validates your input and creates a unique tool key for identification.

### 4. Tool Details Panel

When you select a tool, the right panel displays comprehensive information:

- **Tool Name & Status**: Current installation and test status
- **Tool Key**: Unique identifier (read-only)
- **Source Path**: Where the tool is located
- **Entrypoint**: The main entry point for execution
- **Last Install Result**: Success or failure of the most recent installation
- **Last Smoke Test**: Pass/fail status of the most recent test run

### 5. Tool Management Actions

#### Edit Metadata
Click **"Edit Metadata"** to update the tool's name and add a description. The tool key and source path are read-only for reference.

#### Install Tool
1. Click **"Install Tool"** button
2. Select a backend:
   - **auto-detect**: Let the system choose (recommended)
   - **pip**: Python's standard package manager
   - **poetry**: For Poetry-managed projects
   - **uv**: Fast Python package manager
3. The system will install dependencies and display real-time output in the terminal panel

#### Run Tool
1. Click **"Run Tool"** button
2. Optionally enter CLI arguments (e.g., `--help`, `--config file.json`)
3. Click **"Execute"** to run the tool
4. Real-time output appears in the terminal panel below

#### Remove Tool
1. Click **"Remove"** button
2. Confirm the deletion in the dialog
3. The tool is permanently removed from your registry

### 6. Doctor/Diagnostics

Click **"Doctor/Diagnostics"** to analyze your tool's health and configuration:

- **Detected Entrypoint**: The main script or module identified
- **Available Backends**: Package managers that can be used for installation
- **Dependency Files Found**: `requirements.txt`, `setup.py`, `pyproject.toml`, etc.
- **Inferred Requirements**: Detected dependencies from configuration files
- **Health Status**: Overall assessment of the tool's readiness

### 7. Export/Pack Tool

Click **"Export/Pack"** to bundle your tool for distribution:

- Creates a `.zip` archive containing the tool's source code
- Includes a manifest file with metadata
- Ready to share or archive

### 8. Terminal Output Panel

All command output (installation, execution, diagnostics) appears in a dark-themed terminal panel:

- **Color-coded lines**: Green for success, red for errors, yellow for warnings
- **Copy Output**: Copy all terminal text to your clipboard
- **Clear Output**: Clear the terminal for a fresh view
- **Real-time streaming**: Watch output as it happens

## Workflow Examples

### Example 1: Register and Run a Tool

1. Click **"Add Tool"** and enter:
   - Name: `My Data Processor`
   - Source: `/home/user/tools/data_processor.py`
   - Entrypoint: `data_processor.py`

2. Click **"Create"** to register the tool

3. Select the tool from the list

4. Click **"Install Tool"** and select **"auto-detect"**

5. Wait for installation to complete

6. Click **"Run Tool"**, enter arguments like `--input data.csv --output result.json`

7. Monitor the output in the terminal panel

### Example 2: Diagnose a Problematic Tool

1. Select the tool from the list

2. Click **"Doctor/Diagnostics"**

3. Review the health status and dependency information

4. If dependencies are missing, click **"Install Tool"** to resolve

5. Run **"Run Tool"** to test if the issue is fixed

### Example 3: Find and Manage Multiple Tools

1. Use **"Filter by Status"** to show only **"Not Installed"** tools

2. Sort by **"Recently Updated"** to see which tools need attention

3. Select each tool and install as needed

4. Use **"Filter by Status"** → **"Installed"** to verify all are ready

## Best Practices

### Tool Organization
- Use descriptive tool names that reflect their purpose
- Keep tool sources in organized directories
- Maintain consistent naming conventions

### Installation
- Use **"auto-detect"** backend for most tools
- Use **"poetry"** for Poetry-managed projects
- Use **"uv"** for faster installations on large projects
- Use **"pip"** for simple, standard Python packages

### Monitoring
- Run **"Doctor/Diagnostics"** regularly to catch issues early
- Check **"Smoke Test"** status to verify tool health
- Review installation logs if tests fail

### Maintenance
- Keep your tool registry clean by removing unused tools
- Update tool metadata to reflect current status
- Export/pack tools before major version changes for archival

## Troubleshooting

### Tool Won't Install
1. Click **"Doctor/Diagnostics"** to check for issues
2. Verify the source path is correct
3. Try a different backend (e.g., switch from pip to uv)
4. Check the terminal output for specific error messages

### Tool Runs but Fails
1. Verify CLI arguments are correct
2. Check the terminal output for error details
3. Run **"Doctor/Diagnostics"** to confirm dependencies are installed
4. Reinstall dependencies with a different backend

### Search/Filter Not Working
1. Clear the search box by clicking the **X** button
2. Reset the filter to **"All Tools"**
3. Refresh the page if issues persist

### Missing Tool in List
1. Check if a filter is active (should show "X of Y tools")
2. Verify the tool wasn't accidentally removed
3. Try searching by partial name

## Keyboard & UI Tips

- **Tab Navigation**: Use Tab to navigate between controls
- **Enter Key**: Press Enter to execute actions (Run Tool, Install, etc.)
- **Escape Key**: Close dialogs and cancel operations
- **Copy Output**: Use the terminal panel's copy button for easy sharing

## Advanced Features

### Real-time Monitoring
The terminal panel streams output in real-time, allowing you to:
- Watch installation progress
- Monitor tool execution
- Capture diagnostic information

### Tool Metadata
Beyond name and description, the system tracks:
- Installation history and success status
- Smoke test results
- Last update timestamp
- Backend used for installation

### Secure Management
- All tool data is user-scoped (only you see your tools)
- Destructive actions require confirmation
- Tool keys are unique and immutable for reference

## Support & Feedback

For issues, feature requests, or feedback, please contact the development team through the Manus support portal.

## Version Information

- **Application**: SB Toolsmith Web v1.0
- **Framework**: React 19 + Express 4 + tRPC 11
- **Database**: MySQL/TiDB
- **Last Updated**: May 2026

---

**Happy tool managing!** 🔧
