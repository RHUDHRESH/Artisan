"""
Simple proxy pool management for web scraping
"""
import asyncio
import aiohttp
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


@dataclass
class ProxyConfig:
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class Proxy:
    config: ProxyConfig
    success_count: int = 0
    fail_count: int = 0
    last_used: Optional[datetime] = None
    is_healthy: bool = True
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return (self.success_count / total * 100) if total > 0 else 0.0
    
    @property
    def proxy_url(self) -> str:
        if self.config.username and self.config.password:
            return f"{self.config.proxy_type.value}://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}"
        return f"{self.config.proxy_type.value}://{self.config.host}:{self.config.port}"


class SimpleProxyPool:
    def __init__(self):
        self.proxies: List[Proxy] = []
        self.current_index = 0
    
    def add_proxy(self, config: ProxyConfig) -> None:
        proxy = Proxy(config=config)
        self.proxies.append(proxy)
    
    def get_best_proxy(self) -> Optional[Proxy]:
        available = [p for p in self.proxies if p.is_healthy]
        if not available:
            return None
        
        # Sort by success rate
        available.sort(key=lambda p: p.success_rate, reverse=True)
        return available[0]
    
    def get_random_proxy(self) -> Optional[Proxy]:
        available = [p for p in self.proxies if p.is_healthy]
        return random.choice(available) if available else None
    
    def update_proxy(self, proxy: Proxy, success: bool) -> None:
        if success:
            proxy.success_count += 1
            proxy.is_healthy = True
        else:
            proxy.fail_count += 1
            if proxy.fail_count > 3:
                proxy.is_healthy = False
        proxy.last_used = datetime.now()
