import sys
import os

# Add repository root to Python path so backend package is discoverable
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import app

# Export WSGI application for Vercel Serverless Function runtime
handler = app
