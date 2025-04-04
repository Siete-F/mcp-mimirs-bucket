#!/bin/bash
# Setup script for Mimir's Bucket MCP Server on Unix-like systems

echo "Setting up Mimir's Bucket environment..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "UV package manager not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        echo "Failed to install UV. Please install manually and try again."
        exit 1
    fi
    # Add UV to PATH for the current session
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment
echo "Creating virtual environment..."
uv venv
if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
uv add "mcp[cli]" python-arango python-dotenv numpy
uv add -o sentence-transformers

# Install the package in development mode
echo "Installing package in development mode..."
uv pip install -e .

echo "Setup complete!"
echo ""
echo "To use Mimir's Bucket:"
echo "1. Run \"python main.py\" to start the MCP server"
echo "2. Or use \"python scripts/update_embeddings.py\" to update document embeddings"
echo ""

# Make scripts executable
chmod +x scripts/*.py
chmod +x main.py
