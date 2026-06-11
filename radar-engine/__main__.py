"""
Radar Engine - Command Line Interface

Entry point for running autonomous intelligence operations
"""

import asyncio
from .main import main

if __name__ == "__main__":
    asyncio.run(main())