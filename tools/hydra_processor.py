"""
Using Hydra for configuration management.
Makes slot processing more consistent and configurable.
"""

from pathlib import Path
from typing import Any, Dict, List

# Would need: pip install hydra-core
import hydra
from omegaconf import DictConfig, OmegaConf

from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService


@hydra.main(version_base=None, config_path="../config", config_name="hydra_config")
def process_with_config(cfg: DictConfig) -> Dict[str, Any]:
    """Process slots using Hydra configuration."""
    
    print(f"🔧 Using configuration:")
    print(f"  Model: {cfg.model.provider} - {cfg.model.model_name}")
    print(f"  Processing: batch_size={cfg.processing.batch_size}, parallel={cfg.processing.parallel_slots}")
    print(f"  Validation: strict={cfg.validation.strict_mode}")
    
    # Initialize components with config
    llm_service = LLMService(
        provider=cfg.model.provider,
        model_name=cfg.model.model_name,
        temperature=cfg.model.temperature,
        max_tokens=cfg.model.max_tokens
    )
    
    processor = BatchProcessor(llm_service)
    
    # Apply configuration to processor
    processor.batch_size = cfg.processing.batch_size
    processor.parallel_slots = cfg.processing.parallel_slots
    processor.timeout_seconds = cfg.processing.timeout_seconds
    processor.retry_attempts = cfg.processing.retry_attempts
    
    # Validation settings
    if cfg.validation.strict_mode:
        processor.enable_strict_validation()
    
    # Example processing with config
    # (This would be called with actual parameters)
    result = {
        "config_used": OmegaConf.to_yaml(cfg),
        "status": "configured"
    }
    
    return result


class ConfigurableBatchProcessor(BatchProcessor):
    """BatchProcessor that uses Hydra configuration."""
    
    def __init__(self, cfg: DictConfig):
        """Initialize with configuration."""
        
        # Initialize LLM service from config
        llm_service = LLMService(
            provider=cfg.model.provider,
            model_name=cfg.model.model_name,
            temperature=cfg.model.temperature,
            max_tokens=cfg.model.max_tokens
        )
        
        super().__init__(llm_service)
        
        # Store configuration
        self.cfg = cfg
        
        # Apply processing settings
        self.batch_size = cfg.processing.batch_size
        self.parallel_slots = cfg.processing.parallel_slots
        self.timeout_seconds = cfg.processing.timeout_seconds
        self.retry_attempts = cfg.processing.retry_attempts
        
        # Validation settings
        self.strict_validation = cfg.validation.strict_mode
        self.min_word_count = cfg.validation.min_word_count
        
        # Cache settings
        self.cache_enabled = cfg.processing.cache_enabled
        if self.cache_enabled:
            from tools.redis_cache import SlotCacheManager
            self.cache = SlotCacheManager(cfg.cache.redis_url)
    
    def validate_slot_config(self, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate slots using configuration."""
        issues = []
        
        # Check required fields
        for slot in slots:
            for field in self.cfg.slot_structure.required_fields:
                if field not in slot or not slot[field]:
                    issues.append(f"Slot {slot.get('slot_number', 'unknown')}: Missing required field '{field}'")
        
        # Check slot limits
        if len(slots) > self.cfg.slot_structure.max_slots:
            issues.append(f"Too many slots: {len(slots)} > {self.cfg.slot_structure.max_slots}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        """Get file patterns from configuration."""
        return self.cfg.file_patterns
    
    def should_track_performance(self) -> bool:
        """Check if performance tracking is enabled."""
        return self.cfg.performance.track_metrics


# Example usage:
def create_processor_from_config(config_path: str = None) -> ConfigurableBatchProcessor:
    """Create processor from configuration file."""
    
    cfg = OmegaConf.load(config_path or "../config/hydra_config.yaml")
    return ConfigurableBatchProcessor(cfg)


# Command line usage:
# python tools/hydra_processor.py --config-name hydra_config model.provider=anthropic processing.batch_size=3
