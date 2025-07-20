import os
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Bot configuration settings"""
    # Discord settings
    discord_token: Optional[str] = None
    command_prefix: str = "!pause "
    
    # Toxicity detection settings
    toxicity_threshold: float = 0.7
    use_perspective_api: bool = False
    perspective_api_key: Optional[str] = None
    
    # Bot behavior settings
    default_locale: str = "en"
    prompt_timeout: int = 300  # 5 minutes
    cleanup_interval: int = 1800  # 30 minutes
    message_retention: int = 3600  # 1 hour
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "bot.log"
    
    # Database settings
    database_path: str = "bot_data.db"
    
    # Rate limiting
    max_prompts_per_user_per_hour: int = 10
    cooldown_between_prompts: int = 30  # seconds
    
    def __post_init__(self):
        """Load configuration from environment variables and config file"""
        self.load_from_env()
        self.load_from_file()
        self.validate()
        
    def load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'DISCORD_TOKEN': 'discord_token',
            'PERSPECTIVE_API_KEY': 'perspective_api_key',
            'TOXICITY_THRESHOLD': ('toxicity_threshold', float),
            'USE_PERSPECTIVE_API': ('use_perspective_api', bool),
            'DEFAULT_LOCALE': 'default_locale',
            'PROMPT_TIMEOUT': ('prompt_timeout', int),
            'LOG_LEVEL': 'log_level',
            'LOG_FILE': 'log_file',
            'DATABASE_PATH': 'database_path',
            'MAX_PROMPTS_PER_HOUR': ('max_prompts_per_user_per_hour', int),
            'COOLDOWN_SECONDS': ('cooldown_between_prompts', int)
        }
        
        for env_var, config_attr in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(config_attr, tuple):
                    attr_name, attr_type = config_attr
                    try:
                        if attr_type == bool:
                            value = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            value = attr_type(value)
                        setattr(self, attr_name, value)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {env_var}: {value} ({e})")
                else:
                    setattr(self, config_attr, value)
                    
    def load_from_file(self, config_path: str = "config.json"):
        """Load configuration from JSON file"""
        config_file = Path(config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                        
                logger.info(f"Configuration loaded from {config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load config file {config_path}: {e}")
                
    def save_to_file(self, config_path: str = "config.json"):
        """Save current configuration to JSON file"""
        config_file = Path(config_path)
        
        try:
            # Don't save sensitive information
            config_dict = asdict(self)
            sensitive_keys = ['discord_token', 'perspective_api_key']
            for key in sensitive_keys:
                if key in config_dict:
                    config_dict[key] = None
                    
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            logger.info(f"Configuration saved to {config_path}")
        except IOError as e:
            logger.error(f"Could not save config file {config_path}: {e}")
            
    def validate(self):
        """Validate configuration settings"""
        errors = []
        
        # Required settings
        if not self.discord_token:
            errors.append("DISCORD_TOKEN is required")
            
        # Validate ranges
        if not 0.0 <= self.toxicity_threshold <= 1.0:
            errors.append("toxicity_threshold must be between 0.0 and 1.0")
            
        if self.prompt_timeout < 60:
            errors.append("prompt_timeout must be at least 60 seconds")
            
        if self.max_prompts_per_user_per_hour < 1:
            errors.append("max_prompts_per_user_per_hour must be at least 1")
            
        if self.cooldown_between_prompts < 0:
            errors.append("cooldown_between_prompts cannot be negative")
            
        # Validate Perspective API settings
        if self.use_perspective_api and not self.perspective_api_key:
            errors.append("perspective_api_key is required when use_perspective_api is True")
            
        # Validate locale
        supported_locales = ['en', 'vi', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh', 'ru', 'ar', 'hi', 'pt', 'nl']
        if self.default_locale not in supported_locales:
            logger.warning(f"Unsupported locale '{self.default_locale}', falling back to 'en'")
            self.default_locale = 'en'
            
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)
            
        logger.info("Configuration validation passed")
        
    def get_perspective_config(self) -> Dict[str, Any]:
        """Get configuration for Perspective API engine"""
        return {
            'api_key': self.perspective_api_key,
            'timeout': 10,
            'threshold': self.toxicity_threshold
        }
        
    def get_onnx_config(self) -> Dict[str, Any]:
        """Get configuration for ONNX engine"""
        return {
            'threshold': self.toxicity_threshold,
            'max_sequence_length': 512
        }
        
    def setup_logging(self):
        """Configure logging based on settings"""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if self.log_file:
            try:
                file_handler = logging.FileHandler(self.log_file)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except IOError as e:
                logger.warning(f"Could not create log file {self.log_file}: {e}")
                
        logger.info(f"Logging configured: level={self.log_level}, file={self.log_file}")

def load_config() -> BotConfig:
    """Load and return bot configuration"""
    return BotConfig()

def create_default_config_file():
    """Create a default configuration file with example values"""
    config = BotConfig()
    config.discord_token = "YOUR_DISCORD_TOKEN_HERE"
    config.perspective_api_key = "YOUR_PERSPECTIVE_API_KEY_HERE"
    config.use_perspective_api = False
    
    config.save_to_file("config.example.json")
    print("Created config.example.json - copy this to config.json and fill in your tokens")

if __name__ == "__main__":
    create_default_config_file()