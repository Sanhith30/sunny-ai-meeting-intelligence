# Hugging Face Spaces Entry Point
# This file is for deploying on HF Spaces

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment for HF Spaces
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "7860")

from web.app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
