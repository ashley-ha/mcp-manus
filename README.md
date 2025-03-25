# MCP Browser Agent

[![smithery badge](https://smithery.ai/badge/@ashley-ha/mcp-manus)](https://smithery.ai/server/@ashley-ha/mcp-manus)

Built at AGI House MCP Hackathon

## Overview

This project is a browser automation agent that uses the Model Context Protocol (MCP) to enable browser interactions. It provides a seamless integration between Claude and browser automation capabilities through our MCP server. 

Thank you to Browser-Use for their browser agent capabilities that help power our MCP server!

## System Requirements

- macOS (darwin 24.2.0)
- Python 3.12 or higher
- `uv` package manager
- Google Chrome browser (Ensure your browser is closed before running task(s).)

## Installation

### Installing via Smithery

To install Browser Automation Agent for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ashley-ha/mcp-manus):

```bash
npx -y @smithery/cli install @ashley-ha/mcp-manus --client claude
```

### Manual Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd mcp
```

2. Set up the Python environment using `uv`:
```bash
uv venv
source .venv/bin/activate
uv sync
```

## Configuration

### Claude Desktop Configuration

Create or modify your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/mcp",
        "run",
        "browser-use.py"
      ]
    }
  }
}
```

Replace `/ABSOLUTE/PATH/TO/browser-use` with the absolute path to your project directory.

### Browser Configuration

The agent is configured to use Google Chrome with the following default settings:
- Non-headless mode for development
- Window size: 1280x1100
- Disabled security features for testing
- Recording path: ./tmp/recordings

## Features

- Browser automation through MCP tools
- State management and planning capabilities
- Interactive element detection and manipulation
- Configurable browser contexts
- Logging and debugging support

## Usage

The agent provides two main tools:

1. `get_planner_state`: Retrieves the current browser state and planning context
2. `execute_actions`: Executes planned actions in the browser

## Development

### Logging

The project uses Python's built-in logging with the following configuration:
- All logs are directed to stderr
- Custom formatting: `%(levelname)-8s [%(name)s] %(message)s`
- Root logger level: INFO
- Third-party loggers level: WARNING

### Project Structure

- `browser-use.py`: Main entry point and server implementation
- `tmp/recordings`: Directory for browser session recordings
- Dependencies managed through `uv`

## Contributing

This project was built during the AGI House MCP Hackathon. Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Jaeyun Ha, Ashley Ha

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
