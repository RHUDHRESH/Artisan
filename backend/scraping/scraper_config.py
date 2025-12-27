"""
Enhanced web scraper configuration and utilities
"""
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from backend.scraping.web_scraper import ProxyConfig, ScrapingConfig
import json


@dataclass
class WebScraperSettings:
    """Settings for web scraper configuration"""
    
    # API Keys
    tavily_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None
    
    # Proxy Configuration
    proxy_list: List[ProxyConfig] = None
    
    # Performance Settings
    default_config: ScrapingConfig = None
    
    # Cache Settings
    cache_dir: str = "./data/cache"
    cache_enabled: bool = True
    default_cache_ttl: int = 3600  # 1 hour
    
    # Rate Limiting
    default_rate_limit: float = 0.5  # seconds between requests
    max_concurrent_requests: int = 5
    
    # Content Extraction
    max_content_length: int = 10000
    content_cleaning_enabled: bool = True
    
    # Monitoring
    enable_websocket_broadcasts: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize defaults after creation"""
        if self.proxy_list is None:
            self.proxy_list = []
        
        if self.default_config is None:
            self.default_config = ScrapingConfig(
                max_retries=3,
                retry_delay_base=1.0,
                rate_limit_delay=self.default_rate_limit,
                max_concurrent_requests=self.max_concurrent_requests,
                cache_enabled=self.cache_enabled
            )
    
    @classmethod
    def from_env(cls) -> 'WebScraperSettings':
        """Create settings from environment variables"""
        return cls(
            tavily_api_key=os.getenv('TAVILY_API_KEY'),
            serpapi_key=os.getenv('SERPAPI_KEY'),
            cache_dir=os.getenv('SCRAPER_CACHE_DIR', './data/cache'),
            cache_enabled=os.getenv('SCRAPER_CACHE_ENABLED', 'true').lower() == 'true',
            default_rate_limit=float(os.getenv('SCRAPER_RATE_LIMIT', '0.5')),
            max_concurrent_requests=int(os.getenv('SCRAPER_MAX_CONCURRENT', '5')),
            enable_websocket_broadcasts=os.getenv('SCRAPER_WEBSOCKET_ENABLED', 'true').lower() == 'true',
            log_level=os.getenv('SCRAPER_LOG_LEVEL', 'INFO')
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'WebScraperSettings':
        """Load settings from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Convert proxy configurations
            proxy_list = []
            for proxy_data in config_data.get('proxy_list', []):
                proxy_list.append(ProxyConfig(**proxy_data))
            
            return cls(
                tavily_api_key=config_data.get('tavily_api_key'),
                serpapi_key=config_data.get('serpapi_key'),
                proxy_list=proxy_list,
                cache_dir=config_data.get('cache_dir', './data/cache'),
                cache_enabled=config_data.get('cache_enabled', True),
                default_rate_limit=config_data.get('default_rate_limit', 0.5),
                max_concurrent_requests=config_data.get('max_concurrent_requests', 5),
                enable_websocket_broadcasts=config_data.get('enable_websocket_broadcasts', True),
                log_level=config_data.get('log_level', 'INFO')
            )
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load scraper config from {config_path}: {e}")
            return cls.from_env()
    
    def to_file(self, config_path: str) -> None:
        """Save settings to JSON file"""
        config_data = {
            'tavily_api_key': self.tavily_api_key,
            'serpapi_key': self.serpapi_key,
            'proxy_list': [
                {
                    'host': proxy.host,
                    'port': proxy.port,
                    'username': proxy.username,
                    'password': proxy.password,
                    'proxy_type': proxy.proxy_type
                }
                for proxy in self.proxy_list
            ],
            'cache_dir': self.cache_dir,
            'cache_enabled': self.cache_enabled,
            'default_rate_limit': self.default_rate_limit,
            'max_concurrent_requests': self.max_concurrent_requests,
            'enable_websocket_broadcasts': self.enable_websocket_broadcasts,
            'log_level': self.log_level
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)


def create_sample_config() -> WebScraperSettings:
    """Create a sample configuration for demonstration"""
    return WebScraperSettings(
        tavily_api_key="your_tavily_api_key_here",
        serpapi_key="your_serpapi_key_here",
        proxy_list=[
            ProxyConfig(
                host="proxy1.example.com",
                port=8080,
                username="user1",
                password="pass1",
                proxy_type="http"
            ),
            ProxyConfig(
                host="proxy2.example.com", 
                port=1080,
                proxy_type="socks5"
            )
        ],
        default_rate_limit=1.0,
        max_concurrent_requests=3,
        cache_enabled=True,
        enable_websocket_broadcasts=True
    )


def validate_config(settings: WebScraperSettings) -> List[str]:
    """Validate scraper configuration and return list of issues"""
    issues = []
    
    # Check API keys
    if not settings.tavily_api_key and not settings.serpapi_key:
        issues.append("No API keys configured - web search will not work")
    
    # Check cache directory
    if settings.cache_enabled:
        try:
            os.makedirs(settings.cache_dir, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create cache directory {settings.cache_dir}: {e}")
    
    # Check rate limiting
    if settings.default_rate_limit < 0.1:
        issues.append("Rate limit too low - may cause API blocking")
    
    # Check concurrent requests
    if settings.max_concurrent_requests > 20:
        issues.append("High concurrent request count - may cause rate limiting")
    
    # Check proxy configuration
    for i, proxy in enumerate(settings.proxy_list):
        if not proxy.host or not proxy.port:
            issues.append(f"Proxy {i} has invalid host or port")
    
    return issues


def setup_logging(settings: WebScraperSettings) -> None:
    """Setup logging for the scraper"""
    import logging
    from loguru import logger
    
    # Remove default handlers
    logger.remove()
    
    # Add console handler with specified level
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    # Add file handler for scraper logs
    log_file = os.path.join(settings.cache_dir, "scraper.log")
    logger.add(
        log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days"
    )


# Example usage and configuration templates
SCRAPER_CONFIG_TEMPLATE = {
    "tavily_api_key": "your_tavily_api_key",
    "serpapi_key": "your_serpapi_key", 
    "proxy_list": [
        {
            "host": "proxy.example.com",
            "port": 8080,
            "username": "optional_username",
            "password": "optional_password",
            "proxy_type": "http"
        }
    ],
    "cache_dir": "./data/cache",
    "cache_enabled": True,
    "default_rate_limit": 0.5,
    "max_concurrent_requests": 5,
    "enable_websocket_broadcasts": True,
    "log_level": "INFO"
}


if __name__ == "__main__":
    # Create sample configuration file
    settings = create_sample_config()
    settings.to_file("./scraper_config.json")
    print("Sample configuration saved to scraper_config.json")
    
    # Validate configuration
    issues = validate_config(settings)
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid!")
