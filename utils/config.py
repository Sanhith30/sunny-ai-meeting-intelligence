"""
Configuration Loader
Handles loading and validating configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict
import yaml


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Expand environment variables
    config = _expand_env_vars(config)
    
    # Validate required sections
    _validate_config(config)
    
    return config


def _expand_env_vars(config: Any) -> Any:
    """Recursively expand environment variables in config values."""
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Expand ${VAR} patterns
        if config.startswith("${") and config.endswith("}"):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration has required sections."""
    required_sections = ["general", "meeting", "audio", "transcription", "summarization"]
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "general": {
            "bot_name": "Sunny AI – Assistant",
            "log_level": "INFO",
            "output_dir": "./outputs",
            "temp_dir": "./temp"
        },
        "meeting": {
            "max_duration_minutes": 180,
            "waiting_room_timeout_seconds": 300,
            "end_detection_interval_seconds": 10,
            "auto_leave_on_end": True
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "format": "wav",
            "chunk_duration_seconds": 30
        },
        "transcription": {
            "model_size": "medium",
            "language": "en",
            "device": "cpu",
            "compute_type": "int8"
        },
        "summarization": {
            "ollama_base_url": "http://localhost:11434",
            "model": "llama3",
            "max_tokens": 2048,
            "temperature": 0.3,
            "chunk_size_tokens": 4000,
            "overlap_tokens": 200
        },
        "pdf": {
            "font_family": "Helvetica",
            "title_font_size": 18,
            "heading_font_size": 14,
            "body_font_size": 11,
            "margin": 50
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "subject_template": "Meeting Summary - {date} - {platform}"
        },
        "browser": {
            "headless": False,
            "timeout_ms": 30000
        }
    }
