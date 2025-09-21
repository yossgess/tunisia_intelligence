"""
Vector Generation Service for Tunisia Intelligence System.

This module provides comprehensive vector generation capabilities using Ollama models
for semantic embeddings, supporting Arabic and French content with pgvector integration.
"""

import json
import logging
import hashlib
import numpy as np
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
import requests
import json
import re
import time
import threading

# Import our new helpers
from ..utils.content_cleaner import ContentCleaner, VectorHomogenizer, VectorValidator
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

from .ollama_client import OllamaClient, OllamaConfig

logger = logging.getLogger(__name__)

@dataclass
class VectorConfig:
    """Configuration for vector generation service."""
    model: str = "qwen2.5:7b"
    embedding_dimensions: int = 1536
    batch_size: int = 10
    max_workers: int = 4
    chunk_size: int = 1000  # Max characters per chunk
    overlap_size: int = 100  # Overlap between chunks
    min_content_length: int = 50  # Minimum content length to vectorize
    cache_vectors: bool = True
    normalize_vectors: bool = True
    timeout: int = 180  # Longer timeout for embedding generation

@dataclass
class VectorResult:
    """Result of vector generation."""
    content_id: str
    content_type: str  # 'article', 'social_post', 'comment', 'entity'
    vector: Optional[List[float]] = None
    content_hash: Optional[str] = None
    processing_time: float = 0.0
    error: Optional[str] = None
    chunks_processed: int = 0
    language: Optional[str] = None

class ContentPreprocessor:
    """Preprocessor for content before vectorization."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text for vectorization."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Simple language detection for Arabic/French content."""
        if not text:
            return "unknown"
        
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        
        # Count Latin characters (French/English)
        latin_chars = len(re.findall(r'[a-zA-ZÀ-ÿ]', text))
        
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return "unknown"
        
        arabic_ratio = arabic_chars / total_chars
        latin_ratio = latin_chars / total_chars
        
        if arabic_ratio > 0.3:
            return "arabic"
        elif latin_ratio > 0.5:
            return "french"
        else:
            return "mixed"
    
    @staticmethod
    def chunk_content(text: str, chunk_size: int = 1000, overlap_size: int = 100) -> List[str]:
        """Split content into overlapping chunks for better vectorization."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end),
                    text.rfind('。', start, end),  # Arabic sentence ending
                )
                
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + chunk_size - overlap_size, end)
            
            if start >= len(text):
                break
        
        return chunks
    
    @staticmethod
    def generate_content_hash(text: str) -> str:
        """Generate a hash for content deduplication."""
        normalized_text = ContentPreprocessor.clean_text(text).lower()
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

class VectorService:
    """
    Service for generating semantic embeddings using Ollama models.
    
    Supports batch processing, content chunking, and pgvector integration.
    """
    
    def __init__(self, config: Optional[VectorConfig] = None):
        """Initialize the vector service."""
        self.config = config or VectorConfig()
        self.preprocessor = ContentPreprocessor()
        self._lock = threading.Lock()
        self._cache = {} if self.config.cache_vectors else None
        
        # Initialize Ollama client with vector-specific config
        ollama_config = OllamaConfig(
            model=self.config.model,
            timeout=self.config.timeout,
            temperature=0.0,  # Deterministic for embeddings
            max_tokens=4096
        )
        self.ollama_client = OllamaClient(ollama_config)
        
        logger.info(f"VectorService initialized with model: {self.config.model}")
    
    def health_check(self) -> bool:
        """Check if the vector service is ready."""
        return self.ollama_client.health_check()
    
    def _generate_embedding_prompt(self, text: str, language: str = "unknown") -> str:
        """Generate a prompt for embedding generation."""
        system_context = {
            "arabic": "You are generating semantic embeddings for Arabic text content.",
            "french": "You are generating semantic embeddings for French text content.",
            "mixed": "You are generating semantic embeddings for multilingual text content.",
            "unknown": "You are generating semantic embeddings for text content."
        }
        
        prompt = f"""
{system_context.get(language, system_context["unknown"])}

Generate a semantic embedding vector for the following text. The embedding should capture the semantic meaning, context, and key concepts.

Text to embed:
{text}

Please provide a numerical vector representation that captures the semantic essence of this content.
"""
        return prompt
    
    def _extract_vector_from_response(self, response: str) -> Optional[List[float]]:
        """Extract vector from Ollama response using robust homogenization."""
        if not response:
            return None
        
        try:
            # Use our new robust vector extraction
            vector = VectorHomogenizer.extract_clean_vector(response, self.config.embedding_dimensions)
            
            if vector and VectorValidator.validate_vector(vector, self.config.embedding_dimensions):
                return vector
            
            # If extraction failed, generate fallback vector
            logger.warning("Could not extract valid vector from response, generating fallback vector")
            return VectorHomogenizer.create_fallback_vector(response, self.config.embedding_dimensions)
            
        except Exception as e:
            logger.error(f"Error extracting vector from response: {e}")
            # Final fallback
            return VectorHomogenizer.create_fallback_vector(response or "fallback", self.config.embedding_dimensions)
    
    def _generate_hash_vector(self, text: str) -> List[float]:
        """Generate a simple hash-based vector as fallback."""
        # Create a deterministic vector based on text hash
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # Convert to normalized float vector
        vector = []
        for i in range(0, min(len(hash_bytes), self.config.embedding_dimensions // 8), 1):
            # Convert byte to float in range [-1, 1]
            byte_val = hash_bytes[i]
            float_val = (byte_val - 127.5) / 127.5
            vector.append(float_val)
        
        # Pad or truncate to desired dimensions
        while len(vector) < self.config.embedding_dimensions:
            vector.append(0.0)
        
        vector = vector[:self.config.embedding_dimensions]
        
        # Normalize if required
        if self.config.normalize_vectors:
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = (np.array(vector) / norm).tolist()
        
        return vector
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length."""
        if not vector:
            return vector
        
        np_vector = np.array(vector)
        norm = np.linalg.norm(np_vector)
        
        if norm == 0:
            return vector
        
        return (np_vector / norm).tolist()
    
    def generate_vector(
        self,
        content: str,
        content_id: str,
        content_type: str = "article",
        force_regenerate: bool = False
    ) -> VectorResult:
        """
        Generate vector for a single piece of content.
        
        Args:
            content: Text content to vectorize
            content_id: Unique identifier for the content
            content_type: Type of content ('article', 'social_post', 'comment', 'entity')
            force_regenerate: Whether to regenerate even if cached
            
        Returns:
            VectorResult with generated vector and metadata
        """
        start_time = time.time()
        
        result = VectorResult(
            content_id=content_id,
            content_type=content_type
        )
        
        try:
            # Preprocess content using our robust cleaner
            cleaned_content = ContentCleaner.clean_article_content("", content, max_length=4000)
            
            if len(cleaned_content) < self.config.min_content_length:
                result.error = f"Content too short: {len(cleaned_content)} chars"
                return result
            
            # Generate content hash
            content_hash = self.preprocessor.generate_content_hash(cleaned_content)
            result.content_hash = content_hash
            
            # Check cache
            if self._cache and not force_regenerate:
                with self._lock:
                    if content_hash in self._cache:
                        cached_result = self._cache[content_hash]
                        result.vector = cached_result['vector']
                        result.language = cached_result['language']
                        result.processing_time = time.time() - start_time
                        logger.debug(f"Vector retrieved from cache for {content_id}")
                        return result
            
            # Detect language
            language = self.preprocessor.detect_language(cleaned_content)
            result.language = language
            
            # Chunk content if necessary
            chunks = self.preprocessor.chunk_content(
                cleaned_content,
                self.config.chunk_size,
                self.config.overlap_size
            )
            result.chunks_processed = len(chunks)
            
            # Generate embeddings for chunks
            chunk_vectors = []
            
            for i, chunk in enumerate(chunks):
                logger.debug(f"Processing chunk {i+1}/{len(chunks)} for {content_id}")
                
                # Generate embedding prompt
                prompt = self._generate_embedding_prompt(chunk, language)
                
                # Get response from Ollama
                response = self.ollama_client.generate(
                    prompt=prompt,
                    temperature=0.0,
                    max_tokens=4096
                )
                
                if response:
                    # Extract vector from response
                    chunk_vector = self._extract_vector_from_response(response)
                    if chunk_vector:
                        chunk_vectors.append(chunk_vector)
                    else:
                        # Fallback to hash-based vector
                        chunk_vector = self._generate_hash_vector(chunk)
                        chunk_vectors.append(chunk_vector)
                else:
                    # Fallback to hash-based vector
                    chunk_vector = self._generate_hash_vector(chunk)
                    chunk_vectors.append(chunk_vector)
            
            if not chunk_vectors:
                result.error = "Failed to generate any vectors"
                return result
            
            # Combine chunk vectors (average)
            if len(chunk_vectors) == 1:
                final_vector = chunk_vectors[0]
            else:
                # Average the vectors
                vector_array = np.array(chunk_vectors)
                final_vector = np.mean(vector_array, axis=0).tolist()
            
            # Ensure consistent dimensions
            if len(final_vector) > self.config.embedding_dimensions:
                final_vector = final_vector[:self.config.embedding_dimensions]
            elif len(final_vector) < self.config.embedding_dimensions:
                # Pad with zeros
                final_vector.extend([0.0] * (self.config.embedding_dimensions - len(final_vector)))
            
            # Normalize if required
            if self.config.normalize_vectors:
                final_vector = self._normalize_vector(final_vector)
            
            result.vector = final_vector
            
            # Cache result
            if self._cache:
                with self._lock:
                    self._cache[content_hash] = {
                        'vector': final_vector,
                        'language': language,
                        'timestamp': time.time()
                    }
            
            logger.debug(f"Vector generated for {content_id}: {len(final_vector)} dimensions")
            
        except Exception as e:
            result.error = f"Vector generation failed: {str(e)}"
            logger.error(f"Error generating vector for {content_id}: {e}")
        
        result.processing_time = time.time() - start_time
        return result
    
    def batch_generate_vectors(
        self,
        content_items: List[Dict[str, Any]],
        force_regenerate: bool = False
    ) -> List[VectorResult]:
        """
        Generate vectors for multiple content items in parallel.
        
        Args:
            content_items: List of dicts with 'content', 'id', 'type' keys
            force_regenerate: Whether to regenerate even if cached
            
        Returns:
            List of VectorResult objects
        """
        logger.info(f"Starting batch vector generation for {len(content_items)} items")
        
        results = []
        
        # Process in batches to manage memory and API load
        for i in range(0, len(content_items), self.config.batch_size):
            batch = content_items[i:i + self.config.batch_size]
            batch_results = []
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                # Submit tasks
                future_to_item = {}
                for item in batch:
                    future = executor.submit(
                        self.generate_vector,
                        content=item.get('content', ''),
                        content_id=str(item.get('id', '')),
                        content_type=item.get('type', 'article'),
                        force_regenerate=force_regenerate
                    )
                    future_to_item[future] = item
                
                # Collect results
                for future in as_completed(future_to_item):
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        item = future_to_item[future]
                        error_result = VectorResult(
                            content_id=str(item.get('id', '')),
                            content_type=item.get('type', 'article'),
                            error=f"Batch processing error: {str(e)}"
                        )
                        batch_results.append(error_result)
            
            results.extend(batch_results)
            
            # Log progress
            successful = sum(1 for r in batch_results if r.vector is not None)
            logger.info(f"Batch {i//self.config.batch_size + 1}: {successful}/{len(batch)} successful")
            
            # Small delay between batches
            if i + self.config.batch_size < len(content_items):
                time.sleep(1)
        
        successful_total = sum(1 for r in results if r.vector is not None)
        logger.info(f"Batch vector generation completed: {successful_total}/{len(content_items)} successful")
        
        return results
    
    def clear_cache(self):
        """Clear the vector cache."""
        if self._cache:
            with self._lock:
                self._cache.clear()
            logger.info("Vector cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._cache:
            return {"cache_enabled": False}
        
        with self._lock:
            return {
                "cache_enabled": True,
                "cached_items": len(self._cache),
                "cache_size_mb": sum(len(str(v)) for v in self._cache.values()) / (1024 * 1024)
            }
