"""
AI Enrichment Prompts for Tunisia Intelligence System

This module provides editable prompts for AI enrichment processing, organized by content type
and processing mode. Prompts can be customized through the web dashboard and are designed
for optimal performance with the qwen2.5:7b model.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of AI enrichment prompts."""
    FULL_ENRICHMENT = "full_enrichment"
    SENTIMENT_ONLY = "sentiment_only"
    KEYWORDS_ONLY = "keywords_only"
    ENTITIES_ONLY = "entities_only"
    CATEGORIES_ONLY = "categories_only"
    TRANSLATION = "translation"
    ENHANCED_COMMENT = "enhanced_comment"


class ContentType(str, Enum):
    """Content types for prompts."""
    ARTICLE = "article"
    POST = "post"
    COMMENT = "comment"


class AIEnrichmentPrompts:
    """
    AI Enrichment Prompts Manager.
    
    Provides editable prompts for different content types and processing modes,
    with support for dynamic prompt customization and template variables.
    """
    
    def __init__(self):
        """Initialize the prompts manager."""
        self.prompts = self._initialize_default_prompts()
        self.prompt_metadata = {
            "version": "1.0.0",
            "last_updated": datetime.now(),
            "updated_by": "system"
        }
    
    def _initialize_default_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize default prompts for all content types and processing modes."""
        return {
            # =====================================================
            # ARTICLE PROMPTS
            # =====================================================
            ContentType.ARTICLE: {
                PromptType.FULL_ENRICHMENT: """Analyze the following French article content and provide comprehensive AI enrichment in JSON format.

Article Content: {content}

Requirements:
1. Sentiment Analysis: Determine overall sentiment (positive/negative/neutral) with confidence score
2. Keyword Extraction: Extract top {max_keywords} most important keywords with importance scores and categories
3. Named Entity Recognition: Identify persons, organizations, locations with Tunisian context priority
4. Category Classification: Classify into primary and secondary categories from Tunisian context
5. Summary Generation: Create concise Arabic summary (max {summary_max_length} characters)
6. Language Detection: Detect source language and processing language

Focus on Tunisian political, social, and economic context. Prioritize Tunisian entities and keywords.
Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.85,
  "keywords": [
    {{
      "text": "keyword_text",
      "importance": 0.95,
      "category": "politics|economy|social|security|international|other",
      "normalized_form": "normalized_keyword"
    }}
  ],
  "entities": [
    {{
      "text": "entity_text",
      "type": "PERSON|ORGANIZATION|LOCATION",
      "canonical_name": "Official_Name",
      "confidence": 0.95,
      "context": "brief_context",
      "is_tunisian": true
    }}
  ],
  "category": {{
    "primary_category": "politics|economy|social|security|international|sports|culture|health|education|technology|other",
    "secondary_categories": ["subcategory1", "subcategory2"],
    "confidence": 0.88,
    "reasoning": "brief_explanation"
  }},
  "summary": "Arabic summary text",
  "language_detected": "ar|fr|en|mixed",
  "confidence": 0.89,
  "processing_metadata": {{
    "model_version": "qwen2.5:7b",
    "processing_time_ms": 0,
    "content_length": 0
  }}
}}""",

                PromptType.SENTIMENT_ONLY: """Analyze the sentiment of the following French article content.

Article Content: {content}

Requirements:
- Determine overall sentiment: positive, negative, or neutral
- Provide confidence score (0.0 to 1.0)
- Brief reasoning for the sentiment classification
- Consider Tunisian cultural and political context

Return only valid JSON:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.85,
  "confidence": 0.90,
  "reasoning": "brief_explanation",
  "language_detected": "fr"
}}""",

                PromptType.KEYWORDS_ONLY: """Extract the most important keywords from the following French article content.

Article Content: {content}

Requirements:
- Extract top {max_keywords} most important keywords
- Provide importance scores (0.0 to 1.0)
- Categorize keywords by topic
- Focus on Tunisian context and terminology

Return only valid JSON:
{{
  "keywords": [
    {{
      "text": "keyword_text",
      "importance": 0.95,
      "category": "politics|economy|social|security|international|other",
      "normalized_form": "normalized_keyword"
    }}
  ],
  "confidence": 0.88,
  "language_detected": "fr"
}}""",

                PromptType.ENTITIES_ONLY: """Extract named entities from the following French article content.

Article Content: {content}

Requirements:
- Identify persons, organizations, and locations
- Prioritize Tunisian entities
- Provide confidence scores and context
- Use canonical names for well-known entities

Return only valid JSON:
{{
  "entities": [
    {{
      "text": "entity_text",
      "type": "PERSON|ORGANIZATION|LOCATION",
      "canonical_name": "Official_Name",
      "confidence": 0.95,
      "context": "brief_context",
      "is_tunisian": true
    }}
  ],
  "confidence": 0.90,
  "language_detected": "fr"
}}""",

                PromptType.TRANSLATION: """Translate the following Arabic content to French, maintaining meaning and context.

Arabic Content: {content}

Requirements:
- Accurate translation preserving meaning
- Maintain formal tone appropriate for news content
- Preserve proper names and technical terms
- Consider Tunisian Arabic dialect nuances

Return only valid JSON:
{{
  "content_fr": "French translation",
  "language_detected": "ar",
  "confidence": 0.95,
  "translation_quality": "high|medium|low"
}}"""
            },
            
            # =====================================================
            # SOCIAL MEDIA POST PROMPTS
            # =====================================================
            ContentType.POST: {
                PromptType.FULL_ENRICHMENT: """Analyze the following French social media post and provide comprehensive AI enrichment in JSON format.

Post Content: {content}

Requirements:
1. Sentiment Analysis: Determine sentiment (positive/negative/neutral) with confidence score
2. Keyword Extraction: Extract top {max_keywords} keywords including hashtags and key phrases
3. Named Entity Recognition: Identify persons, organizations, locations mentioned
4. Category Classification: Classify post topic and context
5. Summary Generation: Create brief Arabic summary (max {summary_max_length} characters)
6. Social Media Elements: Process hashtags, mentions, and social context

Focus on Tunisian social and political context. Consider informal language and social media conventions.
Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.75,
  "keywords": [
    {{
      "text": "keyword_text",
      "importance": 0.85,
      "category": "hashtag|mention|topic|other",
      "normalized_form": "normalized_keyword",
      "is_hashtag": false
    }}
  ],
  "entities": [
    {{
      "text": "entity_text",
      "type": "PERSON|ORGANIZATION|LOCATION",
      "canonical_name": "Official_Name",
      "confidence": 0.90,
      "is_tunisian": true,
      "is_mention": false
    }}
  ],
  "category": {{
    "primary_category": "politics|social|opinion|news|personal|other",
    "confidence": 0.80,
    "reasoning": "brief_explanation"
  }},
  "summary": "Arabic summary",
  "social_elements": {{
    "hashtags": ["#hashtag1", "#hashtag2"],
    "mentions": ["@user1", "@user2"],
    "urls": ["url1", "url2"]
  }},
  "language_detected": "ar|fr|en|mixed",
  "confidence": 0.82
}}""",

                PromptType.SENTIMENT_ONLY: """Analyze the sentiment of the following French social media post.

Post Content: {content}

Requirements:
- Determine sentiment: positive, negative, or neutral
- Consider social media context and informal language
- Account for sarcasm, irony, and cultural nuances
- Provide confidence score and reasoning

Return only valid JSON:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.75,
  "confidence": 0.85,
  "reasoning": "brief_explanation",
  "language_detected": "fr"
}}""",

                PromptType.TRANSLATION: """Translate the following Arabic social media post to French, preserving social media style and context.

Arabic Post: {content}

Requirements:
- Maintain informal social media tone
- Preserve hashtags and mentions
- Keep cultural references and expressions
- Consider Tunisian dialect and social context

Return only valid JSON:
{{
  "content_fr": "French translation",
  "language_detected": "ar",
  "confidence": 0.90,
  "social_elements_preserved": true
}}"""
            },
            
            # =====================================================
            # COMMENT PROMPTS
            # =====================================================
            ContentType.COMMENT: {
                PromptType.SENTIMENT_ONLY: """Analyze the sentiment of the following French comment.

Comment Content: {content}

Requirements:
- Determine sentiment: positive, negative, or neutral
- Consider comment context and conversational tone
- Account for brevity and informal language
- Provide confidence score

Return only valid JSON:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.70,
  "confidence": 0.80,
  "language_detected": "fr"
}}""",

                PromptType.ENHANCED_COMMENT: """Analyze the following French comment and provide enhanced AI enrichment in JSON format.

Comment Content: {content}

Requirements:
1. Sentiment Analysis: Determine sentiment (positive/negative/neutral)
2. Keyword Extraction: Extract top {max_keywords} keywords with importance scores
3. Named Entity Recognition: Identify persons, organizations, locations
4. Bilingual Output: Provide French translations of Arabic keywords and entities
5. Relevance Assessment: Assess comment relevance and quality

Focus on Tunisian context. Handle brief, informal comment language.
Return only valid JSON without markdown formatting.

Expected JSON structure:
{{
  "sentiment": "positive|negative|neutral",
  "sentiment_score": 0.72,
  "keywords": [
    {{
      "text": "original_keyword",
      "importance": 0.85,
      "category": "opinion|topic|emotion|other",
      "normalized_form": "normalized_keyword"
    }}
  ],
  "entities": [
    {{
      "text": "original_entity",
      "type": "PERSON|ORGANIZATION|LOCATION",
      "canonical_name": "Official_Name",
      "confidence": 0.90,
      "is_tunisian": true
    }}
  ],
  "keywords_fr": [
    {{
      "text": "french_keyword",
      "importance": 0.85,
      "original_text": "original_arabic_keyword"
    }}
  ],
  "entities_fr": [
    {{
      "text": "french_entity",
      "canonical_name": "Official_Name",
      "original_text": "original_arabic_entity"
    }}
  ],
  "relevance_score": 0.75,
  "quality_indicators": {{
    "is_spam": false,
    "is_offensive": false,
    "is_constructive": true
  }},
  "confidence": 0.78
}}""",

                PromptType.TRANSLATION: """Translate the following Arabic comment to French, maintaining conversational tone.

Arabic Comment: {content}

Requirements:
- Preserve informal conversational style
- Maintain emotional tone and intent
- Keep cultural expressions where appropriate
- Handle brief, colloquial language

Return only valid JSON:
{{
  "content_fr": "French translation",
  "language_detected": "ar",
  "confidence": 0.85,
  "tone_preserved": true
}}"""
            }
        }
    
    def get_prompt(self, content_type: ContentType, prompt_type: PromptType, **kwargs) -> str:
        """
        Get a prompt template for the specified content type and prompt type.
        
        Args:
            content_type: Type of content (article, post, comment)
            prompt_type: Type of processing (full_enrichment, sentiment_only, etc.)
            **kwargs: Template variables for prompt formatting
            
        Returns:
            Formatted prompt string
        """
        try:
            if content_type not in self.prompts:
                raise ValueError(f"Unknown content type: {content_type}")
            
            if prompt_type not in self.prompts[content_type]:
                raise ValueError(f"Unknown prompt type: {prompt_type} for content type: {content_type}")
            
            prompt_template = self.prompts[content_type][prompt_type]
            
            # Format the prompt with provided variables
            if kwargs:
                try:
                    return prompt_template.format(**kwargs)
                except KeyError as e:
                    logger.warning(f"Missing template variable: {e}. Using unformatted prompt.")
                    return prompt_template
            
            return prompt_template
            
        except Exception as e:
            logger.error(f"Error getting prompt: {e}")
            return self._get_fallback_prompt(content_type, prompt_type)
    
    def _get_fallback_prompt(self, content_type: ContentType, prompt_type: PromptType) -> str:
        """Get a basic fallback prompt when the main prompt fails."""
        if prompt_type == PromptType.SENTIMENT_ONLY:
            return """Analyze the sentiment of the following content: {content}

Return JSON: {{"sentiment": "positive|negative|neutral", "sentiment_score": 0.5, "confidence": 0.5}}"""
        
        return """Analyze the following content: {content}

Return basic analysis in JSON format."""
    
    def update_prompt(self, content_type: ContentType, prompt_type: PromptType, new_prompt: str, updated_by: str = "user") -> bool:
        """
        Update a specific prompt.
        
        Args:
            content_type: Type of content
            prompt_type: Type of processing
            new_prompt: New prompt text
            updated_by: Who updated the prompt
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if content_type not in self.prompts:
                self.prompts[content_type] = {}
            
            self.prompts[content_type][prompt_type] = new_prompt
            
            # Update metadata
            self.prompt_metadata["last_updated"] = datetime.now()
            self.prompt_metadata["updated_by"] = updated_by
            
            logger.info(f"Updated prompt: {content_type}/{prompt_type} by {updated_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating prompt: {e}")
            return False
    
    def get_all_prompts(self) -> Dict[str, Dict[str, str]]:
        """Get all prompts for dashboard display."""
        return self.prompts.copy()
    
    def get_prompt_metadata(self) -> Dict[str, Any]:
        """Get prompt metadata."""
        return self.prompt_metadata.copy()
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Validate a prompt for common issues.
        
        Args:
            prompt: Prompt text to validate
            
        Returns:
            Validation results dictionary
        """
        issues = []
        warnings = []
        
        # Check for basic structure
        if not prompt.strip():
            issues.append("Prompt is empty")
        
        if len(prompt) < 50:
            warnings.append("Prompt is very short, may not provide enough context")
        
        if len(prompt) > 5000:
            warnings.append("Prompt is very long, may exceed model context limits")
        
        # Check for JSON requirement
        if "json" not in prompt.lower():
            warnings.append("Prompt doesn't mention JSON format requirement")
        
        # Check for template variables
        template_vars = []
        import re
        vars_found = re.findall(r'\{(\w+)\}', prompt)
        template_vars.extend(vars_found)
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "template_variables": template_vars,
            "length": len(prompt),
            "estimated_tokens": len(prompt.split()) * 1.3  # Rough estimate
        }
    
    def export_prompts(self, file_path: str) -> bool:
        """
        Export all prompts to a JSON file.
        
        Args:
            file_path: Path to save the prompts file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                "prompts": self.prompts,
                "metadata": {
                    **self.prompt_metadata,
                    "last_updated": self.prompt_metadata["last_updated"].isoformat()
                },
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Prompts exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting prompts: {e}")
            return False
    
    def import_prompts(self, file_path: str, updated_by: str = "import") -> bool:
        """
        Import prompts from a JSON file.
        
        Args:
            file_path: Path to the prompts file
            updated_by: Who imported the prompts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Prompts file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if "prompts" in import_data:
                self.prompts = import_data["prompts"]
                
                # Update metadata
                self.prompt_metadata["last_updated"] = datetime.now()
                self.prompt_metadata["updated_by"] = updated_by
                
                logger.info(f"Prompts imported from: {file_path}")
                return True
            else:
                logger.error("Invalid prompts file format")
                return False
                
        except Exception as e:
            logger.error(f"Error importing prompts: {e}")
            return False
    
    def reset_to_defaults(self, updated_by: str = "system") -> bool:
        """
        Reset all prompts to default values.
        
        Args:
            updated_by: Who reset the prompts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.prompts = self._initialize_default_prompts()
            
            # Update metadata
            self.prompt_metadata["last_updated"] = datetime.now()
            self.prompt_metadata["updated_by"] = updated_by
            
            logger.info(f"Prompts reset to defaults by {updated_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting prompts: {e}")
            return False
    
    def get_prompt_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current prompts."""
        stats = {
            "total_prompts": 0,
            "prompts_by_content_type": {},
            "average_prompt_length": 0,
            "total_template_variables": 0,
            "last_updated": self.prompt_metadata.get("last_updated"),
            "updated_by": self.prompt_metadata.get("updated_by")
        }
        
        total_length = 0
        total_vars = 0
        
        for content_type, prompts in self.prompts.items():
            stats["prompts_by_content_type"][content_type] = len(prompts)
            stats["total_prompts"] += len(prompts)
            
            for prompt in prompts.values():
                total_length += len(prompt)
                # Count template variables
                import re
                vars_found = len(re.findall(r'\{(\w+)\}', prompt))
                total_vars += vars_found
        
        if stats["total_prompts"] > 0:
            stats["average_prompt_length"] = total_length // stats["total_prompts"]
        
        stats["total_template_variables"] = total_vars
        
        return stats


# Global prompts instance
_ai_enrichment_prompts: Optional[AIEnrichmentPrompts] = None


def get_ai_enrichment_prompts() -> AIEnrichmentPrompts:
    """Get the global AI enrichment prompts instance."""
    global _ai_enrichment_prompts
    if _ai_enrichment_prompts is None:
        _ai_enrichment_prompts = AIEnrichmentPrompts()
    return _ai_enrichment_prompts


def reload_ai_enrichment_prompts() -> AIEnrichmentPrompts:
    """Reload AI enrichment prompts (reset to defaults)."""
    global _ai_enrichment_prompts
    _ai_enrichment_prompts = AIEnrichmentPrompts()
    return _ai_enrichment_prompts


# Convenience functions for getting specific prompts
def get_article_prompt(prompt_type: PromptType, **kwargs) -> str:
    """Get article enrichment prompt."""
    return get_ai_enrichment_prompts().get_prompt(ContentType.ARTICLE, prompt_type, **kwargs)


def get_post_prompt(prompt_type: PromptType, **kwargs) -> str:
    """Get post enrichment prompt."""
    return get_ai_enrichment_prompts().get_prompt(ContentType.POST, prompt_type, **kwargs)


def get_comment_prompt(prompt_type: PromptType, **kwargs) -> str:
    """Get comment enrichment prompt."""
    return get_ai_enrichment_prompts().get_prompt(ContentType.COMMENT, prompt_type, **kwargs)
