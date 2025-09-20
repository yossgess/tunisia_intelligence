"""
Ollama Client for local LLM integration.

This module provides a robust client for interacting with Ollama models,
specifically optimized for the qwen2.5:7b model and multilingual content.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    temperature: float = 0.1
    max_tokens: int = 2048

class OllamaClient:
    """
    Client for interacting with Ollama API.
    
    Provides robust error handling, retry logic, and optimizations
    for multilingual content processing.
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize the Ollama client."""
        self.config = config or OllamaConfig()
        self._session = None
        self._lock = threading.Lock()
        self._setup_session()
        
    def _setup_session(self):
        """Setup HTTP session with retry strategy."""
        self._session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Set default headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = self._session.get(
                f"{self.config.base_url}/api/tags",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            response = self._session.get(
                f"{self.config.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Generate text using the Ollama model.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text or None if failed
        """
        with self._lock:
            try:
                # Prepare the request payload
                payload = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature or self.config.temperature,
                        "num_predict": max_tokens or self.config.max_tokens,
                        **kwargs
                    }
                }
                
                # Add system prompt if provided
                if system_prompt:
                    payload["system"] = system_prompt
                
                logger.debug(f"Sending request to Ollama: {payload['model']}")
                start_time = time.time()
                
                response = self._session.post(
                    f"{self.config.base_url}/api/generate",
                    json=payload,
                    timeout=self.config.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                duration = time.time() - start_time
                logger.debug(f"Ollama request completed in {duration:.2f}s")
                
                return result.get('response', '').strip()
                
            except requests.exceptions.Timeout:
                logger.error("Ollama request timed out")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Ollama request failed: {e}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama response: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in Ollama generate: {e}")
                return None
    
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        expected_format: str = "json",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generate structured output (JSON) from the model.
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system prompt
            expected_format: Expected output format (default: "json")
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response or None if failed
        """
        # Enhance prompt for structured output
        structured_prompt = f"{prompt}\n\nPlease respond with valid {expected_format} format only."
        
        if system_prompt:
            system_prompt += f"\n\nAlways respond in valid {expected_format} format."
        else:
            system_prompt = f"You are a helpful assistant that always responds in valid {expected_format} format."
        
        response = self.generate(
            prompt=structured_prompt,
            system_prompt=system_prompt,
            **kwargs
        )
        
        if not response:
            return None
        
        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                # Look for JSON-like content between braces
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            logger.error(f"Failed to parse structured response: {response[:200]}...")
            return None
    
    def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[Optional[str]]:
        """
        Generate responses for multiple prompts.
        
        Args:
            prompts: List of prompts to process
            system_prompt: Optional system prompt for all requests
            **kwargs: Additional parameters
            
        Returns:
            List of generated responses (None for failed requests)
        """
        results = []
        for i, prompt in enumerate(prompts):
            logger.debug(f"Processing batch item {i+1}/{len(prompts)}")
            result = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            results.append(result)
            
            # Small delay between requests to be respectful
            if i < len(prompts) - 1:
                time.sleep(0.1)
        
        return results
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current model."""
        try:
            response = self._session.post(
                f"{self.config.base_url}/api/show",
                json={"name": self.config.model},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._session:
            self._session.close()
