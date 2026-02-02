"""
Engram CLI entry point

Run as: python -m engram
"""

import sys
import argparse
from engram.api import main


def cli():
    parser = argparse.ArgumentParser(description="Engram API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")
    
    args = parser.parse_args()
    
    print(f"🧠 Starting Engram API on {args.host}:{args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs")
    print()
    
    main(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    cli()
