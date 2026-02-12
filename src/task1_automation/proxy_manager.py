"""
Proxy management for IPv4 and IPv6 proxies.
"""

import random
from typing import Dict, List, Optional
from loguru import logger

from .config import Config


class ProxyManager:
    """Manages proxy rotation and selection."""
    
    def __init__(self, config: Config):
        self.config = config
        self.proxy_pool: List[Dict] = []
        self._initialize_proxy_pool()
    
    def _initialize_proxy_pool(self):
        """Initialize proxy pool from configuration."""
        # Add IPv4 proxy if configured
        ipv4_proxy = self.config.get_proxy_config("ipv4")
        if ipv4_proxy:
            ipv4_proxy["type"] = "ipv4"
            self.proxy_pool.append(ipv4_proxy)
            logger.info(f"Added IPv4 proxy: {ipv4_proxy['host']}:{ipv4_proxy['port']}")
        
        # Add IPv6 proxy if configured
        ipv6_proxy = self.config.get_proxy_config("ipv6")
        if ipv6_proxy:
            ipv6_proxy["type"] = "ipv6"
            self.proxy_pool.append(ipv6_proxy)
            logger.info(f"Added IPv6 proxy: {ipv6_proxy['host']}:{ipv6_proxy['port']}")
        
        # Parse additional proxies from pool
        for proxy_str in self.config.proxy_pool:
            proxy = self._parse_proxy_string(proxy_str)
            if proxy:
                self.proxy_pool.append(proxy)
                logger.info(f"Added proxy from pool: {proxy['host']}:{proxy['port']}")
        
        if not self.proxy_pool:
            logger.warning("No proxies configured. Running without proxy support.")
    
    def _parse_proxy_string(self, proxy_str: str) -> Optional[Dict]:
        """
        Parse proxy string in format: protocol://user:pass@host:port
        or host:port
        """
        try:
            if "://" in proxy_str:
                # Full format: protocol://user:pass@host:port
                protocol, rest = proxy_str.split("://", 1)
                
                if "@" in rest:
                    auth, server = rest.split("@", 1)
                    username, password = auth.split(":", 1)
                    host, port = server.split(":", 1)
                else:
                    host, port = rest.split(":", 1)
                    username = password = None
            else:
                # Simple format: host:port
                protocol = "http"
                host, port = proxy_str.split(":", 1)
                username = password = None
            
            return {
                "protocol": protocol,
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "type": "pool"
            }
        except Exception as e:
            logger.error(f"Failed to parse proxy string '{proxy_str}': {e}")
            return None
    
    def get_proxy(self, proxy_type: Optional[str] = None) -> Optional[Dict]:
        """
        Get a proxy from the pool.
        
        Args:
            proxy_type: Specific proxy type to get ("ipv4", "ipv6", or None for random)
        
        Returns:
            Proxy configuration dict or None
        """
        if not self.proxy_pool:
            return None
        
        if proxy_type:
            # Filter by type
            matching_proxies = [p for p in self.proxy_pool if p.get("type") == proxy_type]
            if matching_proxies:
                return random.choice(matching_proxies)
            else:
                logger.warning(f"No {proxy_type} proxies available, using random proxy")
        
        # Return random proxy
        return random.choice(self.proxy_pool)
    
    def get_all_proxies(self) -> List[Dict]:
        """Get all available proxies."""
        return self.proxy_pool.copy()
    
    def get_proxies_by_type(self, proxy_type: str) -> List[Dict]:
        """Get all proxies of a specific type."""
        return [p for p in self.proxy_pool if p.get("type") == proxy_type]
    
    def format_proxy_url(self, proxy: Dict) -> str:
        """Format proxy dict as URL string."""
        if proxy.get("username"):
            return f"{proxy['protocol']}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        else:
            return f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
