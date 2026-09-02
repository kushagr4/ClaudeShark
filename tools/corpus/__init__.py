"""Corpus tooling: reference labels, structural tags, corpus construction.

Nothing in this package ships. It exists to build and audit the position
suites the arena and the move-quality analysis run on. The reference engine it
drives (see ``oracle.py``) is tooling only and is never packaged; the
submission stays pure Python over python-chess.
"""
