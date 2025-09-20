"""
Prompt templates for different AI processing tasks.

This module contains optimized prompts for multilingual content analysis,
specifically designed for Arabic, French, and English content from Tunisian sources.
"""

from typing import Dict, Any, Optional
from enum import Enum

class Language(Enum):
    """Supported languages."""
    ARABIC = "ar"
    FRENCH = "fr"
    ENGLISH = "en"
    AUTO = "auto"

class PromptTemplates:
    """
    Collection of prompt templates for AI processing tasks.
    
    All prompts are optimized for:
    - Multilingual content (Arabic, French, English)
    - Tunisian context and entities
    - Structured JSON output
    - High accuracy and consistency
    """
    
    # System prompts for different tasks
    SYSTEM_PROMPTS = {
        'sentiment': """You are an expert sentiment analyst specializing in Arabic, French, and English text analysis. 
You understand Tunisian context, culture, and current events. Always respond with valid JSON format only.
Focus on the overall emotional tone and opinion expressed in the text.""",
        
        'entities': """You are an expert named entity recognition system specializing in Arabic, French, and English text.
You have deep knowledge of Tunisian politics, geography, organizations, and public figures.
Always respond with valid JSON format only. Focus on identifying persons, organizations, and locations.""",
        
        'keywords': """You are an expert keyword extraction system for Arabic, French, and English text.
You understand Tunisian context and can identify the most important terms, phrases, and concepts.
Always respond with valid JSON format only. Focus on meaningful terms that capture the essence of the content.""",
        
        'categories': """You are an expert content classifier specializing in Tunisian news and social media content.
You can categorize content in Arabic, French, and English into relevant topics.
Always respond with valid JSON format only. Focus on the main subject matter and themes."""
    }
    
    @staticmethod
    def get_sentiment_prompt(content: str, language: Language = Language.AUTO) -> str:
        """
        Generate sentiment analysis prompt.
        
        Args:
            content: Text content to analyze
            language: Target language (auto-detect if not specified)
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze the sentiment of the following text and respond with valid JSON only:

Text to analyze:
"{content}"

Respond with this exact JSON structure:
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation in the same language as the text",
    "emotions": ["list", "of", "detected", "emotions"],
    "language_detected": "ar|fr|en"
}}

Consider:
- Cultural context and Tunisian expressions
- Sarcasm and irony
- Political and social nuances
- Mixed language content (Arabic-French code-switching)"""
    
    @staticmethod
    def get_entities_prompt(content: str, language: Language = Language.AUTO) -> str:
        """
        Generate named entity recognition prompt.
        
        Args:
            content: Text content to analyze
            language: Target language (auto-detect if not specified)
            
        Returns:
            Formatted prompt string
        """
        return f"""Extract named entities from the following text and respond with valid JSON only:

Text to analyze:
"{content}"

Respond with this exact JSON structure:
{{
    "entities": [
        {{
            "text": "entity name as it appears",
            "type": "PERSON|ORGANIZATION|LOCATION",
            "confidence": 0.0-1.0,
            "canonical_name": "standardized name",
            "context": "surrounding context"
        }}
    ],
    "language_detected": "ar|fr|en"
}}

Focus on:
- Tunisian political figures, ministers, officials
- Government institutions and organizations
- Tunisian cities, governorates, and regions
- International entities mentioned in Tunisian context
- Handle Arabic transliterations and French names
- Consider alternative spellings and aliases"""
    
    @staticmethod
    def get_keywords_prompt(content: str, language: Language = Language.AUTO) -> str:
        """
        Generate keyword extraction prompt.
        
        Args:
            content: Text content to analyze
            language: Target language (auto-detect if not specified)
            
        Returns:
            Formatted prompt string
        """
        return f"""Extract the most important keywords and key phrases from the following text and respond with valid JSON only:

Text to analyze:
"{content}"

Respond with this exact JSON structure:
{{
    "keywords": [
        {{
            "text": "keyword or phrase",
            "type": "single_word|phrase|concept",
            "importance": 0.0-1.0,
            "frequency": "number of occurrences",
            "category": "politics|economy|society|culture|sports|other"
        }}
    ],
    "language_detected": "ar|fr|en",
    "main_topics": ["list", "of", "main", "topics"]
}}

Focus on:
- Most significant terms that capture the content essence
- Tunisian-specific terminology and concepts
- Political, economic, and social terms
- Proper nouns and technical terms
- Multi-word phrases and expressions
- Avoid common stop words and articles"""
    
    @staticmethod
    def get_categories_prompt(content: str, language: Language = Language.AUTO) -> str:
        """
        Generate category classification prompt.
        
        Args:
            content: Text content to analyze
            language: Target language (auto-detect if not specified)
            
        Returns:
            Formatted prompt string
        """
        return f"""Classify the following text into appropriate categories and respond with valid JSON only:

Text to analyze:
"{content}"

Respond with this exact JSON structure:
{{
    "primary_category": "main category",
    "secondary_categories": ["list", "of", "secondary", "categories"],
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "language_detected": "ar|fr|en"
}}

Available categories:
- Politics (سياسة / Politique)
- Economy (اقتصاد / Économie)  
- Society (مجتمع / Société)
- Culture (ثقافة / Culture)
- Sports (رياضة / Sport)
- Education (تعليم / Éducation)
- Health (صحة / Santé)
- Technology (تكنولوجيا / Technologie)
- Environment (بيئة / Environnement)
- Security (أمن / Sécurité)
- International (دولي / International)
- Regional (جهوي / Régional)
- Other (أخرى / Autre)

Consider:
- Main subject matter and themes
- Tunisian context and relevance
- Multiple categories if content spans topics
- Political and social nuances"""
    
    @staticmethod
    def get_summary_prompt(content: str, max_length: int = 200, language: Language = Language.AUTO) -> str:
        """
        Generate text summarization prompt.
        
        Args:
            content: Text content to summarize
            max_length: Maximum summary length in characters
            language: Target language for summary
            
        Returns:
            Formatted prompt string
        """
        return f"""Summarize the following text in {max_length} characters or less, maintaining the original language:

Text to summarize:
"{content}"

Respond with this exact JSON structure:
{{
    "summary": "concise summary in original language",
    "key_points": ["list", "of", "main", "points"],
    "language_detected": "ar|fr|en",
    "word_count": "number of words in original"
}}

Requirements:
- Keep the summary in the same language as the original text
- Capture the most important information
- Maintain factual accuracy
- Use clear and concise language
- Preserve key names, dates, and numbers"""
    
    @staticmethod
    def get_translation_prompt(content: str, target_language: Language) -> str:
        """
        Generate translation prompt.
        
        Args:
            content: Text content to translate
            target_language: Target language for translation
            
        Returns:
            Formatted prompt string
        """
        lang_names = {
            Language.ARABIC: "Arabic",
            Language.FRENCH: "French", 
            Language.ENGLISH: "English"
        }
        
        target_lang = lang_names.get(target_language, "English")
        
        return f"""Translate the following text to {target_lang} and respond with valid JSON only:

Text to translate:
"{content}"

Respond with this exact JSON structure:
{{
    "translation": "translated text",
    "source_language": "ar|fr|en",
    "target_language": "{target_language.value}",
    "confidence": 0.0-1.0,
    "notes": "any translation notes or challenges"
}}

Requirements:
- Maintain meaning and context
- Preserve proper names and technical terms
- Consider cultural nuances
- Handle mixed-language content appropriately
- Maintain formal/informal tone as appropriate"""
    
    @staticmethod
    def get_custom_prompt(
        task: str,
        content: str,
        instructions: str,
        output_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate custom prompt for specific tasks.
        
        Args:
            task: Task description
            content: Text content to process
            instructions: Specific instructions
            output_format: Expected output format structure
            
        Returns:
            Formatted prompt string
        """
        format_section = ""
        if output_format:
            format_section = f"\nRespond with this exact JSON structure:\n{output_format}"
        
        return f"""Task: {task}

{instructions}

Text to process:
"{content}"
{format_section}

Always respond with valid JSON format only."""
