#!/usr/bin/env python
"""
Startup script for DocMind-AI FastAPI server.

Usage:
    python run_api.py [--host HOST] [--port PORT] [--reload]

Examples:
    # Development mode with auto-reload
    python run_api.py --reload

    # Production mode
    python run_api.py --host 0.0.0.0 --port 8000

    # Custom host and port
    python run_api.py --host 127.0.0.1 --port 5000
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point for API server."""
    parser = argparse.ArgumentParser(
        description="DocMind-AI FastAPI Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (production only, default: 1)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Check for .env file
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("WARNING: .env file not found!")
        print("Please create .env file with required configuration:")
        print("  OPENAI_API_KEY=your_key_here")
        print()

    # Import uvicorn
    import uvicorn

    print(f"Starting DocMind-AI API server on {args.host}:{args.port}")
    print(f"Documentation: http://{args.host}:{args.port}/docs")
    print(f"ReDoc: http://{args.host}:{args.port}/redoc")
    print()

    # Run server
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()
