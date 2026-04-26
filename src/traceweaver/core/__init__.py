"""Module M1 — common types, configuration, paths, errors, logging.

Single source of truth for cross-cutting primitives. No imports from
``traceweaver.store`` / ``traceweaver.daemon`` etc — the dependency
graph in ``docs/plan/01_dev_environment.md §1.5.2`` is strictly
unidirectional and ``core`` is the leaf.
"""

from __future__ import annotations
