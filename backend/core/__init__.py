"""Core package.

Keep package import side effects minimal. Submodules should be imported on demand.
"""

__all__ = [
    "auth",
    "embeddings",
    "llm_client",
    "orchestrator",
    "prompts",
    "rag",
    "storage",
    "tenant",
]
