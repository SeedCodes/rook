"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Add .rook/ to path so `import rook` works
sys.path.insert(0, str(Path(__file__).parent.parent / ".rook"))
