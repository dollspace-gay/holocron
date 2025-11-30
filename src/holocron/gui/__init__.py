"""Web GUI for Holocron using NiceGUI.

This package provides a modern web interface for Holocron:
- app: Main application entry point
- pages: Individual page components
- components: Reusable UI components
"""

from holocron.gui.app import run_gui

__all__ = ["run_gui"]
