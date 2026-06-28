# -*- coding: utf-8 -*-
"""Entry point for PyInstaller exe — uses absolute imports.

Launches the system tray app (default) or headless mode (--headless).
"""
import sys

if __name__ == "__main__":
    if "--headless" in sys.argv:
        from agent.main import main
    else:
        from agent.tray import main
    main()
