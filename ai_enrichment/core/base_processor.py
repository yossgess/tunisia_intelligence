"""
Abstract base class for AI processors.

This module defines the common interface and functionality for all
AI processing components (sentiment, NER, keywords, categories).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass
from enum import Enum

from .ollama_client import OllamaClient, OllamaConfig

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Status of processing operations."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"

@dataclass
class ProcessingResult:
    """Base result class for all processing operations."""
    status: ProcessingStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseProcessor(ABC):
    """
    Abstract base class for all AI processors.
    
    Provides common functionality for:
    - Ollama client management
    - Error handling
    - Logging
    - Result validation
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the processor.
        
        Args:
            ollama_client: Optional Ollama client instance
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.ollama_client = ollama_client or OllamaClient()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validate Ollama connection on initialization
        if not self.ollama_client.health_check():
            self.logger.warning("Ollama service is not available")
    
    @abstractmethod
    def process(self, content: str, **kwargs) -> ProcessingResult:
        """
        Process content and return results.
        
        Args:
            content: Text content to process
            **kwargs: Additional processing parameters
            
        Returns:
            ProcessingResult with status and data
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this processor.
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate the processing result.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def preprocess_content(self, content: str) -> str:
        """
        Preprocess content before AI analysis.
        
        Args:
            content: Raw content string
            
        Returns:
            Preprocessed content
        """
        if not content:
            return ""
        
        # Basic preprocessing
        content = content.strip()
        
        # Remove excessive whitespace
        import re
        content = re.sub(r'\s+', ' ', content)
        
        # Truncate if too long (model context limit)
        max_length = self.config.get('max_content_length', 4000)
        if len(content) > max_length:
            content = content[:max_length] + "..."
            self.logger.debug(f"Content truncated to {max_length} characters")
        
        return content
    
    def postprocess_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Postprocess AI result before returning.
        
        Args:
            result: Raw AI result
            
        Returns:
            Processed result
        """
        # Override in subclasses for specific postprocessing
        return result
    
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the result.
        
        Args:
            result: Processing result
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Default implementation - override in subclasses
        return result.get('confidence', 0.5)
    
    def handle_error(self, error: Exception, content: str) -> ProcessingResult:
        """
        Handle processing errors gracefully.
        
        Args:
            error: Exception that occurred
            content: Content being processed
            
        Returns:
            ProcessingResult with error status
        """
        error_msg = f"Processing failed: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        
        return ProcessingResult(
            status=ProcessingStatus.FAILED,
            error=error_msg,
            metadata={
                'content_length': len(content),
                'error_type': type(error).__name__
            }
        )
    
    def batch_process(
        self,
        contents: List[str],
        **kwargs
    ) -> List[ProcessingResult]:
        """
        Process multiple content items in batch.
        
        Args:
            contents: List of content strings to process
            **kwargs: Additional processing parameters
            
        Returns:
            List of ProcessingResult objects
        """
        results = []
        total = len(contents)
        
        self.logger.info(f"Starting batch processing of {total} items")
        
        for i, content in enumerate(contents):
            try:
                self.logger.debug(f"Processing item {i+1}/{total}")
                result = self.process(content, **kwargs)
                results.append(result)
                
                # Log progress every 10 items
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Processed {i+1}/{total} items")
                    
            except Exception as e:
                result = self.handle_error(e, content)
                results.append(result)
        
        # Log summary
        successful = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
        self.logger.info(f"Batch processing completed: {successful}/{total} successful")
        
        return results
    
    def get_processing_stats(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """
        Calculate processing statistics.
        
        Args:
            results: List of processing results
            
        Returns:
            Statistics dictionary
        """
        if not results:
            return {}
        
        total = len(results)
        successful = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
        
        # Calculate average confidence for successful results
        successful_results = [r for r in results if r.status == ProcessingStatus.SUCCESS and r.confidence]
        avg_confidence = (
            sum(r.confidence for r in successful_results) / len(successful_results)
            if successful_results else 0.0
        )
        
        # Calculate average processing time
        timed_results = [r for r in results if r.processing_time]
        avg_time = (
            sum(r.processing_time for r in timed_results) / len(timed_results)
            if timed_results else 0.0
        )
        
        return {
            'total_processed': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0.0,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_time
        }
