import sys
import os

# Add the parent directory to sys.path to allow imports from backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app import create_app

app = create_app()

# Vercel expects 'app' to be the application instance.
# For Flask, this is the Flask object.

if __name__ == "__main__":
    app.run()
from backend.app import create_app

app = create_app()
