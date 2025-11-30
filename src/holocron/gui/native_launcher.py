#!/usr/bin/env python
"""Standalone native GUI launcher for Holocron.

This script runs Holocron in native desktop mode using pywebview.
Run directly with: python -m holocron.gui.native_launcher
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Holocron Native GUI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    args = parser.parse_args()

    from holocron.gui.app import run_gui
    run_gui(host=args.host, port=args.port, native=True)


if __name__ == "__main__":
    main()
