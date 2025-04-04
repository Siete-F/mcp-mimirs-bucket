#!/bin/bash
# This shell script updates embeddings for all documents in the knowledge base

echo "Updating embeddings in the knowledge base..."

# Activate virtual environment if it exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    echo "No virtual environment found at .venv. Please create it or modify this script."
    exit 1
fi

# Run the update script
python update_embeddings.py "$@"

# Deactivate virtual environment
deactivate

echo "Embedding update complete!"
