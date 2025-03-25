# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy the repository contents into the image
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install uv package manager and create a virtual environment
RUN pip install uv

# Create virtual environment using uv and sync dependencies
RUN uv venv && . .venv/bin/activate && uv sync

# Set the command to run the MCP server
CMD [".venv/bin/python", "browser-use.py"]
