"""
AI Enrichment Module for Tunisia Intelligence

This module provides AI-powered content enrichment capabilities including:
- Sentiment analysis
- Named entity recognition (NER)
- Keyword/key phrase extraction
- Category classification

The module integrates with Ollama for local LLM processing and supports
Arabic, French, and English content analysis.
"""

from .core.ollama_client import OllamaClient
from .services.enrichment_service import EnrichmentService
from .models.enrichment_models import (
    SentimentResult,
    EntityResult,
    KeywordResult,
    CategoryResult,
    EnrichmentResult
)

__version__ = "1.0.0"
__author__ = "Tunisia Intelligence Team"

# Main exports
__all__ = [
    "OllamaClient",
    "EnrichmentService",
    "SentimentResult",
    "EntityResult", 
    "KeywordResult",
    "CategoryResult",
    "EnrichmentResult"
]
