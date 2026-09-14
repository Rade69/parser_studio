# Presentation: cli package.
# Eksportuje: main, build_parser, VERSION.
# Ne zna za: SQLite direktno, Docling, contract.
"""Parser Studio CLI entry point.

Komande (MVP):
- psbuild --version
- psbuild --help
- psbuild import <path>
- psbuild analyze <path>
- psbuild confirm <path> --field kolicina=5 --actor user:radovan
"""
from .psbuild import VERSION, build_parser, main

__all__ = ["VERSION", "build_parser", "main"]
