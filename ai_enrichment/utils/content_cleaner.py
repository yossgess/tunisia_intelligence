#!/usr/bin/env python3
"""
Content preprocessing and vector homogenization utilities.
"""

import re
import json
import numpy as np
from typing import List, Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

class ContentCleaner:
    """Comprehensive content cleaning and preprocessing."""
    
    @staticmethod
    def clean_article_content(title: str, content: str, max_length: int = 4000) -> str:
        """
        Clean and prepare article content for vectorization.
        
        Args:
            title: Article title
            content: Article content
            max_length: Maximum content length to prevent context overflow
            
        Returns:
            Cleaned and truncated content
        """
        # Combine title and content
        full_text = f"{title}\n\n{content}" if content else title
        
        # Basic cleaning
        cleaned = ContentCleaner._basic_clean(full_text)
        
        # Truncate if too long
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
            logger.info(f"Content truncated to {max_length} characters")
        
        return cleaned
    
    @staticmethod
    def _basic_clean(text: str) -> str:
        """Basic text cleaning operations."""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()

class VectorHomogenizer:
    """Vector data homogenization and validation."""
    
    @staticmethod
    def extract_clean_vector(response: str, target_dimensions: int = 1536) -> Optional[List[float]]:
        """
        Extract and clean vector from Ollama response with robust error handling.
        
        Args:
            response: Raw response from Ollama
            target_dimensions: Expected vector dimensions
            
        Returns:
            Clean vector or None if extraction fails
        """
        if not response:
            return None
        
        try:
            # Method 1: Try direct JSON parsing
            vector = VectorHomogenizer._try_json_parse(response)
            if vector:
                return VectorHomogenizer._homogenize_vector(vector, target_dimensions)
            
            # Method 2: Extract from text patterns
            vector = VectorHomogenizer._extract_from_patterns(response)
            if vector:
                return VectorHomogenizer._homogenize_vector(vector, target_dimensions)
            
            # Method 3: Extract numbers from anywhere in response
            vector = VectorHomogenizer._extract_all_numbers(response)
            if vector and len(vector) >= 100:  # Minimum reasonable vector size
                return VectorHomogenizer._homogenize_vector(vector, target_dimensions)
            
            logger.warning("Could not extract valid vector from response")
            return None
            
        except Exception as e:
            logger.error(f"Error in vector extraction: {e}")
            return None
    
    @staticmethod
    def _try_json_parse(response: str) -> Optional[List[float]]:
        """Try to parse response as JSON array."""
        try:
            # Look for JSON array in response
            response = response.strip()
            if response.startswith('[') and response.endswith(']'):
                data = json.loads(response)
                if isinstance(data, list):
                    return [float(x) for x in data if isinstance(x, (int, float))]
        except:
            pass
        return None
    
    @staticmethod
    def _extract_from_patterns(response: str) -> Optional[List[float]]:
        """Extract vector from common patterns."""
        try:
            # Pattern 1: [num, num, num, ...]
            pattern1 = r'\[([\d\.\-\s,]+)\]'
            matches = re.findall(pattern1, response)
            
            for match in matches:
                numbers = VectorHomogenizer._parse_number_string(match)
                if len(numbers) > 50:  # Reasonable minimum
                    return numbers
            
            # Pattern 2: Vector: [numbers]
            pattern2 = r'[Vv]ector\s*:?\s*\[([\d\.\-\s,]+)\]'
            matches = re.findall(pattern2, response)
            
            for match in matches:
                numbers = VectorHomogenizer._parse_number_string(match)
                if len(numbers) > 50:
                    return numbers
            
        except Exception as e:
            logger.debug(f"Pattern extraction error: {e}")
        
        return None
    
    @staticmethod
    def _extract_all_numbers(response: str) -> Optional[List[float]]:
        """Extract all floating point numbers from response."""
        try:
            # Find all floating point numbers
            numbers = re.findall(r'-?\d+\.?\d*', response)
            float_numbers = []
            
            for num_str in numbers:
                try:
                    if '.' in num_str or len(num_str) <= 3:  # Likely a float or small int
                        float_numbers.append(float(num_str))
                except ValueError:
                    continue
            
            return float_numbers if len(float_numbers) > 100 else None
            
        except Exception as e:
            logger.debug(f"Number extraction error: {e}")
        
        return None
    
    @staticmethod
    def _parse_number_string(number_string: str) -> List[float]:
        """Parse a string of comma-separated numbers."""
        numbers = []
        for item in number_string.split(','):
            item = item.strip()
            if item and item != '...' and item != '...':
                try:
                    numbers.append(float(item))
                except ValueError:
                    continue
        return numbers
    
    @staticmethod
    def _homogenize_vector(vector: List[float], target_dimensions: int) -> List[float]:
        """
        Ensure vector has consistent dimensions and valid values.
        
        Args:
            vector: Input vector
            target_dimensions: Target number of dimensions
            
        Returns:
            Homogenized vector
        """
        # Remove any NaN or infinite values
        clean_vector = []
        for val in vector:
            if isinstance(val, (int, float)) and np.isfinite(val):
                clean_vector.append(float(val))
        
        if not clean_vector:
            logger.warning("No valid numbers in vector")
            return None
        
        # Pad or truncate to target dimensions
        if len(clean_vector) < target_dimensions:
            # Pad with zeros
            clean_vector.extend([0.0] * (target_dimensions - len(clean_vector)))
        elif len(clean_vector) > target_dimensions:
            # Truncate
            clean_vector = clean_vector[:target_dimensions]
        
        # Normalize to prevent extreme values
        vector_array = np.array(clean_vector)
        
        # Clip extreme values
        vector_array = np.clip(vector_array, -10.0, 10.0)
        
        # Optional: Normalize to unit vector
        norm = np.linalg.norm(vector_array)
        if norm > 0:
            vector_array = vector_array / norm
        
        return vector_array.tolist()
    
    @staticmethod
    def create_fallback_vector(content: str, dimensions: int = 1536) -> List[float]:
        """
        Create a deterministic fallback vector based on content hash.
        
        Args:
            content: Source content
            dimensions: Vector dimensions
            
        Returns:
            Deterministic vector
        """
        import hashlib
        
        # Create hash of content
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Convert hash to vector
        vector = []
        for i in range(dimensions):
            # Use different parts of hash for each dimension
            hash_part = content_hash[(i * 2) % len(content_hash):(i * 2 + 2) % len(content_hash)]
            if len(hash_part) < 2:
                hash_part = content_hash[:2]
            
            # Convert hex to float in range [-1, 1]
            hex_val = int(hash_part, 16)
            float_val = (hex_val - 127.5) / 127.5
            vector.append(float_val)
        
        return vector

class VectorValidator:
    """Validate vectors before storage."""
    
    @staticmethod
    def validate_vector(vector: List[float], expected_dimensions: int = 1536) -> bool:
        """
        Validate that vector is suitable for storage.
        
        Args:
            vector: Vector to validate
            expected_dimensions: Expected number of dimensions
            
        Returns:
            True if vector is valid
        """
        if not vector:
            return False
        
        if len(vector) != expected_dimensions:
            logger.warning(f"Vector has {len(vector)} dimensions, expected {expected_dimensions}")
            return False
        
        # Check for valid numeric values
        for val in vector:
            if not isinstance(val, (int, float)) or not np.isfinite(val):
                logger.warning(f"Invalid value in vector: {val}")
                return False
        
        return True
    
    @staticmethod
    def get_vector_stats(vector: List[float]) -> dict:
        """Get statistics about a vector."""
        if not vector:
            return {"error": "Empty vector"}
        
        vector_array = np.array(vector)
        return {
            "dimensions": len(vector),
            "min": float(np.min(vector_array)),
            "max": float(np.max(vector_array)),
            "mean": float(np.mean(vector_array)),
            "std": float(np.std(vector_array)),
            "norm": float(np.linalg.norm(vector_array))
        }
