@echo off
REM Example script for ingesting stories on Windows
REM Modify the paths to match your story directories

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Ingesting stories into ChromaDB...
echo.

REM Replace these paths with your actual story directories
python scripts\ingest_stories.py ^
    "C:\Users\YourName\Documents\Stories" ^
    "C:\Users\YourName\Desktop\OldStories" ^
    --db-path chroma_db ^
    --batch-size 100

echo.
echo Ingestion complete!
echo.
pause
