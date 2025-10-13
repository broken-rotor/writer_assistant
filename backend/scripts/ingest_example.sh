#!/bin/bash
# Example script for ingesting stories on Linux/Mac
# Modify the paths to match your story directories

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Ingesting stories into ChromaDB..."
echo ""

# Replace these paths with your actual story directories
python scripts/ingest_stories.py \
    "/home/username/Documents/Stories" \
    "/home/username/Documents/OldStories" \
    --db-path chroma_db \
    --batch-size 100

echo ""
echo "Ingestion complete!"
echo ""
