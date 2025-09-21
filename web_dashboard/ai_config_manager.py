"""
AI Configuration Manager for Web Dashboard

This module provides API endpoints and management functions for controlling
AI enrichment configuration and prompts through the web dashboard.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Blueprint, request, jsonify, render_template_string

from config.ai_enrichment_config import (
    get_ai_enrichment_config, reload_ai_enrichment_config,
    ContentType, ProcessingMode, ModelProvider
)
from config.ai_enrichment_prompts import (
    get_ai_enrichment_prompts, reload_ai_enrichment_prompts,
    PromptType
)

logger = logging.getLogger(__name__)

# Create Blueprint for AI configuration routes
ai_config_bp = Blueprint('ai_config', __name__, url_prefix='/api/ai-config')

@ai_config_bp.route('/status', methods=['GET'])
def get_ai_config_status():
    """Get current AI configuration status."""
    try:
        config = get_ai_enrichment_config()
        prompts = get_ai_enrichment_prompts()
        
        return jsonify({
            'success': True,
            'data': {
                'config': {
                    'enabled': config.enabled,
                    'debug_mode': config.debug_mode,
                    'config_version': config.config_version,
                    'last_updated': config.last_updated.isoformat() if config.last_updated else None
                },
                'content_types': {
                    'articles': {
                        'enabled': config.articles.enabled,
                        'processing_mode': config.articles.processing_mode.value,
                        'batch_size': config.articles.batch_size,
                        'max_items_per_run': config.articles.max_items_per_run
                    },
                    'posts': {
                        'enabled': config.posts.enabled,
                        'processing_mode': config.posts.processing_mode.value,
                        'batch_size': config.posts.batch_size,
                        'max_items_per_run': config.posts.max_items_per_run
                    },
                    'comments': {
                        'enabled': config.comments.enabled,
                        'processing_mode': config.comments.processing_mode.value,
                        'batch_size': config.comments.batch_size,
                        'max_items_per_run': config.comments.max_items_per_run
                    }
                },
                'model': {
                    'provider': config.model.provider.value,
                    'model_name': config.model.model_name,
                    'temperature': config.model.temperature,
                    'max_tokens': config.model.max_tokens,
                    'ollama_url': config.model.ollama_url
                },
                'rate_limiting': {
                    'requests_per_minute': config.rate_limiting.requests_per_minute,
                    'articles_per_minute': config.rate_limiting.articles_per_minute,
                    'posts_per_minute': config.rate_limiting.posts_per_minute,
                    'comments_per_minute': config.rate_limiting.comments_per_minute
                },
                'prompts': {
                    'statistics': prompts.get_prompt_statistics(),
                    'metadata': prompts.get_prompt_metadata()
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting AI config status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/config', methods=['GET'])
def get_full_config():
    """Get full AI configuration."""
    try:
        config = get_ai_enrichment_config()
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting full config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/config', methods=['POST'])
def update_config():
    """Update AI configuration."""
    try:
        config_data = request.get_json()
        if not config_data:
            return jsonify({'success': False, 'error': 'No configuration data provided'}), 400
        
        config = get_ai_enrichment_config()
        config.update_from_dict(config_data)
        config.updated_by = "dashboard_user"
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully',
            'data': {
                'last_updated': config.last_updated.isoformat(),
                'updated_by': config.updated_by
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/config/content-type/<content_type>', methods=['GET'])
def get_content_type_config(content_type):
    """Get configuration for a specific content type."""
    try:
        config = get_ai_enrichment_config()
        
        if content_type not in ['articles', 'posts', 'comments']:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400
        
        content_config = getattr(config, content_type)
        
        return jsonify({
            'success': True,
            'data': content_config.dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting content type config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/config/content-type/<content_type>', methods=['POST'])
def update_content_type_config(content_type):
    """Update configuration for a specific content type."""
    try:
        if content_type not in ['articles', 'posts', 'comments']:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400
        
        config_data = request.get_json()
        if not config_data:
            return jsonify({'success': False, 'error': 'No configuration data provided'}), 400
        
        config = get_ai_enrichment_config()
        content_config = getattr(config, content_type)
        
        # Update individual fields
        for key, value in config_data.items():
            if hasattr(content_config, key):
                setattr(content_config, key, value)
        
        config.last_updated = datetime.now()
        config.updated_by = "dashboard_user"
        
        return jsonify({
            'success': True,
            'message': f'{content_type.title()} configuration updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating content type config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts', methods=['GET'])
def get_all_prompts():
    """Get all AI prompts."""
    try:
        prompts = get_ai_enrichment_prompts()
        return jsonify({
            'success': True,
            'data': {
                'prompts': prompts.get_all_prompts(),
                'metadata': prompts.get_prompt_metadata(),
                'statistics': prompts.get_prompt_statistics()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts/<content_type>/<prompt_type>', methods=['GET'])
def get_specific_prompt(content_type, prompt_type):
    """Get a specific prompt."""
    try:
        prompts = get_ai_enrichment_prompts()
        
        # Validate content type and prompt type
        if content_type not in [ct.value for ct in ContentType]:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400
        
        if prompt_type not in [pt.value for pt in PromptType]:
            return jsonify({'success': False, 'error': 'Invalid prompt type'}), 400
        
        prompt_text = prompts.get_prompt(ContentType(content_type), PromptType(prompt_type))
        validation = prompts.validate_prompt(prompt_text)
        
        return jsonify({
            'success': True,
            'data': {
                'prompt': prompt_text,
                'validation': validation
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting specific prompt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts/<content_type>/<prompt_type>', methods=['POST'])
def update_specific_prompt(content_type, prompt_type):
    """Update a specific prompt."""
    try:
        # Validate content type and prompt type
        if content_type not in [ct.value for ct in ContentType]:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400
        
        if prompt_type not in [pt.value for pt in PromptType]:
            return jsonify({'success': False, 'error': 'Invalid prompt type'}), 400
        
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt data provided'}), 400
        
        new_prompt = data['prompt']
        updated_by = data.get('updated_by', 'dashboard_user')
        
        prompts = get_ai_enrichment_prompts()
        
        # Validate the new prompt
        validation = prompts.validate_prompt(new_prompt)
        if not validation['is_valid']:
            return jsonify({
                'success': False,
                'error': 'Prompt validation failed',
                'validation': validation
            }), 400
        
        # Update the prompt
        success = prompts.update_prompt(
            ContentType(content_type),
            PromptType(prompt_type),
            new_prompt,
            updated_by
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Prompt updated successfully',
                'validation': validation
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update prompt'}), 500
        
    except Exception as e:
        logger.error(f"Error updating specific prompt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts/validate', methods=['POST'])
def validate_prompt():
    """Validate a prompt without saving it."""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'success': False, 'error': 'No prompt data provided'}), 400
        
        prompts = get_ai_enrichment_prompts()
        validation = prompts.validate_prompt(data['prompt'])
        
        return jsonify({
            'success': True,
            'data': validation
        })
        
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts/reset', methods=['POST'])
def reset_prompts_to_defaults():
    """Reset all prompts to default values."""
    try:
        data = request.get_json() or {}
        updated_by = data.get('updated_by', 'dashboard_user')
        
        prompts = get_ai_enrichment_prompts()
        success = prompts.reset_to_defaults(updated_by)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All prompts reset to defaults successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to reset prompts'}), 500
        
    except Exception as e:
        logger.error(f"Error resetting prompts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts/export', methods=['POST'])
def export_prompts():
    """Export all prompts to a file."""
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path', 'ai_prompts_export.json')
        
        prompts = get_ai_enrichment_prompts()
        success = prompts.export_prompts(file_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Prompts exported to {file_path}',
                'file_path': file_path
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to export prompts'}), 500
        
    except Exception as e:
        logger.error(f"Error exporting prompts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/prompts/import', methods=['POST'])
def import_prompts():
    """Import prompts from a file."""
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({'success': False, 'error': 'No file path provided'}), 400
        
        file_path = data['file_path']
        updated_by = data.get('updated_by', 'dashboard_user')
        
        prompts = get_ai_enrichment_prompts()
        success = prompts.import_prompts(file_path, updated_by)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Prompts imported from {file_path}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to import prompts'}), 500
        
    except Exception as e:
        logger.error(f"Error importing prompts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/reload', methods=['POST'])
def reload_ai_configuration():
    """Reload AI configuration and prompts."""
    try:
        # Reload configuration
        config = reload_ai_enrichment_config()
        prompts = reload_ai_enrichment_prompts()
        
        return jsonify({
            'success': True,
            'message': 'AI configuration and prompts reloaded successfully',
            'data': {
                'config_version': config.config_version,
                'prompts_version': prompts.get_prompt_metadata().get('version')
            }
        })
        
    except Exception as e:
        logger.error(f"Error reloading AI configuration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/test', methods=['POST'])
def test_ai_configuration():
    """Test AI configuration with sample content."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No test data provided'}), 400
        
        content_type = data.get('content_type', 'article')
        test_content = data.get('content', 'هذا نص تجريبي للاختبار')
        
        # Import and test the configurable service
        from ai_enrichment.services.configurable_enrichment_service import ConfigurableEnrichmentService
        
        service = ConfigurableEnrichmentService()
        result = service.enrich_content(
            content_id=0,  # Test ID
            content_type=ContentType(content_type),
            content=test_content,
            force_reprocess=True
        )
        
        return jsonify({
            'success': True,
            'data': {
                'test_result': {
                    'success': result.success,
                    'processing_time_ms': result.processing_time_ms,
                    'confidence': result.confidence,
                    'error': result.error
                },
                'service_status': service.get_service_status()
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing AI configuration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_config_bp.route('/options', methods=['GET'])
def get_configuration_options():
    """Get available configuration options and enums."""
    try:
        return jsonify({
            'success': True,
            'data': {
                'content_types': [ct.value for ct in ContentType],
                'processing_modes': [pm.value for pm in ProcessingMode],
                'model_providers': [mp.value for mp in ModelProvider],
                'prompt_types': [pt.value for pt in PromptType],
                'default_values': {
                    'batch_sizes': {
                        'articles': {'min': 1, 'max': 100, 'default': 10},
                        'posts': {'min': 1, 'max': 50, 'default': 15},
                        'comments': {'min': 1, 'max': 100, 'default': 25}
                    },
                    'confidence_thresholds': {'min': 0.0, 'max': 1.0, 'default': 0.7},
                    'processing_times': {'min': 10, 'max': 300, 'default': 60},
                    'rate_limits': {'min': 1, 'max': 300, 'default': 20}
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting configuration options: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


class AIConfigManager:
    """
    AI Configuration Manager for dashboard integration.
    
    Provides high-level management functions for AI enrichment
    configuration and prompts.
    """
    
    def __init__(self):
        """Initialize the AI config manager."""
        self.config = get_ai_enrichment_config()
        self.prompts = get_ai_enrichment_prompts()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for dashboard display."""
        return {
            'status': {
                'enabled': self.config.enabled,
                'debug_mode': self.config.debug_mode,
                'last_updated': self.config.last_updated.isoformat() if self.config.last_updated else None
            },
            'content_types': {
                content_type: {
                    'enabled': getattr(self.config, content_type).enabled,
                    'processing_mode': getattr(self.config, content_type).processing_mode.value,
                    'batch_size': getattr(self.config, content_type).batch_size,
                    'max_items_per_run': getattr(self.config, content_type).max_items_per_run,
                    'min_confidence': getattr(self.config, content_type).min_confidence_threshold
                }
                for content_type in ['articles', 'posts', 'comments']
            },
            'model_settings': {
                'provider': self.config.model.provider.value,
                'model_name': self.config.model.model_name,
                'temperature': self.config.model.temperature,
                'max_tokens': self.config.model.max_tokens
            },
            'rate_limiting': {
                'global_rpm': self.config.rate_limiting.requests_per_minute,
                'articles_rpm': self.config.rate_limiting.articles_per_minute,
                'posts_rpm': self.config.rate_limiting.posts_per_minute,
                'comments_rpm': self.config.rate_limiting.comments_per_minute
            },
            'prompts_info': self.prompts.get_prompt_statistics()
        }
    
    def update_batch_sizes(self, batch_sizes: Dict[str, int]) -> bool:
        """Update batch sizes for all content types."""
        try:
            for content_type, batch_size in batch_sizes.items():
                if hasattr(self.config, content_type):
                    content_config = getattr(self.config, content_type)
                    content_config.batch_size = batch_size
            
            self.config.last_updated = datetime.now()
            self.config.updated_by = "dashboard"
            return True
            
        except Exception as e:
            logger.error(f"Error updating batch sizes: {e}")
            return False
    
    def toggle_content_type(self, content_type: str, enabled: bool) -> bool:
        """Enable or disable a specific content type."""
        try:
            if hasattr(self.config, content_type):
                content_config = getattr(self.config, content_type)
                content_config.enabled = enabled
                
                self.config.last_updated = datetime.now()
                self.config.updated_by = "dashboard"
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error toggling content type: {e}")
            return False
    
    def update_rate_limits(self, rate_limits: Dict[str, int]) -> bool:
        """Update rate limiting settings."""
        try:
            for key, value in rate_limits.items():
                if hasattr(self.config.rate_limiting, key):
                    setattr(self.config.rate_limiting, key, value)
            
            self.config.last_updated = datetime.now()
            self.config.updated_by = "dashboard"
            return True
            
        except Exception as e:
            logger.error(f"Error updating rate limits: {e}")
            return False
