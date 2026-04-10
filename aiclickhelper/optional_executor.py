from __future__ import annotations


class OptionalExecutor:
    """Reserved seam for future click/type execution support."""

    def execute(self, _action) -> None:
        raise NotImplementedError("Automation execution is disabled in MVP.")
