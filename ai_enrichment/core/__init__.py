"""
Core components for AI enrichment processing.

This package contains the fundamental building blocks for AI-powered content analysis:
- Ollama client for LLM integration
- Base processor classes
- Prompt templates for different tasks
"""

from .ollama_client import OllamaClient
from .base_processor import BaseProcessor
from .prompt_templates import PromptTemplates

__all__ = [
    "OllamaClient",
    "BaseProcessor", 
    "PromptTemplates"
]
