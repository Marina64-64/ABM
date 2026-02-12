"""
Configuration management for Task 1 automation.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for automation settings."""
    
    def __init__(self):
        # Application settings
        self.app_name = os.getenv("APP_NAME", "reCAPTCHA Automation")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        
        # Browser settings
        self.browser_type = os.getenv("BROWSER_TYPE", "chromium")
        self.headless = os.getenv("HEADLESS", "True").lower() == "true"
        self.browser_timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))
        self.page_load_timeout = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))
        
        # Target site
        self.target_url = os.getenv("TARGET_SITE_URL", "https://cd.captchaaiplus.com/recaptcha-v3-2.php")
        
        # Automation settings
        self.automation_runs = int(os.getenv("AUTOMATION_RUNS", "250"))
        self.retry_attempts = int(os.getenv("RETRY_ATTEMPTS", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "5"))
        
        # Proxy settings
        self.proxy_ipv4_host = os.getenv("PROXY_IPV4_HOST", "")
        self.proxy_ipv4_port = os.getenv("PROXY_IPV4_PORT", "")
        self.proxy_ipv4_user = os.getenv("PROXY_IPV4_USER", "")
        self.proxy_ipv4_password = os.getenv("PROXY_IPV4_PASSWORD", "")
        
        self.proxy_ipv6_host = os.getenv("PROXY_IPV6_HOST", "")
        self.proxy_ipv6_port = os.getenv("PROXY_IPV6_PORT", "")
        self.proxy_ipv6_user = os.getenv("PROXY_IPV6_USER", "")
        self.proxy_ipv6_password = os.getenv("PROXY_IPV6_PASSWORD", "")
        
        # Proxy pool (comma-separated list)
        proxy_pool_str = os.getenv("PROXY_POOL", "")
        self.proxy_pool = [p.strip() for p in proxy_pool_str.split(",") if p.strip()]
        
        # Paths
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.data_dir / "logs"
        self.results_dir = self.data_dir / "results"
        self.output_dir = self.data_dir / "output"
        
        # Create directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", str(self.logs_dir / "app.log"))
    
    def get_proxy_config(self, proxy_type: str) -> Optional[dict]:
        """Get proxy configuration for specified type."""
        if proxy_type == "ipv4" and self.proxy_ipv4_host:
            return {
                "protocol": "http",
                "host": self.proxy_ipv4_host,
                "port": self.proxy_ipv4_port,
                "username": self.proxy_ipv4_user,
                "password": self.proxy_ipv4_password
            }
        elif proxy_type == "ipv6" and self.proxy_ipv6_host:
            return {
                "protocol": "http",
                "host": self.proxy_ipv6_host,
                "port": self.proxy_ipv6_port,
                "username": self.proxy_ipv6_user,
                "password": self.proxy_ipv6_password
            }
        return None
