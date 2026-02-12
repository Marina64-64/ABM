"""
Unit tests for Task 1 automation components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.task1_automation.config import Config
from src.task1_automation.proxy_manager import ProxyManager
from src.task1_automation.statistics import StatisticsAnalyzer


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test config loads with defaults."""
        config = Config()
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.automation_runs == 250
    
    def test_proxy_config_ipv4(self):
        """Test IPv4 proxy configuration."""
        config = Config()
        config.proxy_ipv4_host = "proxy.example.com"
        config.proxy_ipv4_port = "8080"
        
        proxy = config.get_proxy_config("ipv4")
        assert proxy is not None
        assert proxy["host"] == "proxy.example.com"
        assert proxy["port"] == "8080"
    
    def test_proxy_config_none(self):
        """Test proxy config returns None when not configured."""
        config = Config()
        proxy = config.get_proxy_config("ipv4")
        assert proxy is None


class TestProxyManager:
    """Test proxy management."""
    
    def test_parse_proxy_string_full(self):
        """Test parsing full proxy string with auth."""
        config = Config()
        manager = ProxyManager(config)
        
        proxy = manager._parse_proxy_string("http://user:pass@proxy.com:8080")
        assert proxy["protocol"] == "http"
        assert proxy["host"] == "proxy.com"
        assert proxy["port"] == "8080"
        assert proxy["username"] == "user"
        assert proxy["password"] == "pass"
    
    def test_parse_proxy_string_simple(self):
        """Test parsing simple proxy string."""
        config = Config()
        manager = ProxyManager(config)
        
        proxy = manager._parse_proxy_string("proxy.com:8080")
        assert proxy["protocol"] == "http"
        assert proxy["host"] == "proxy.com"
        assert proxy["port"] == "8080"
        assert proxy["username"] is None
    
    def test_get_proxy_by_type(self):
        """Test getting proxy by type."""
        config = Config()
        config.proxy_ipv4_host = "ipv4.proxy.com"
        config.proxy_ipv4_port = "8080"
        
        manager = ProxyManager(config)
        proxy = manager.get_proxy("ipv4")
        
        assert proxy is not None
        assert proxy["type"] == "ipv4"
        assert proxy["host"] == "ipv4.proxy.com"


class TestStatisticsAnalyzer:
    """Test statistics analysis."""
    
    @pytest.fixture
    def sample_results(self):
        """Sample automation results."""
        return [
            {
                "run": 1,
                "success": True,
                "token": "token123",
                "solve_time": 10.5,
                "error": None,
                "proxy_type": "ipv4"
            },
            {
                "run": 2,
                "success": True,
                "token": "token456",
                "solve_time": 8.2,
                "error": None,
                "proxy_type": "ipv4"
            },
            {
                "run": 3,
                "success": False,
                "token": None,
                "solve_time": None,
                "error": "Timeout",
                "proxy_type": "ipv6"
            },
            {
                "run": 4,
                "success": True,
                "token": "token789",
                "solve_time": 15.3,
                "error": None,
                "proxy_type": None
            }
        ]
    
    def test_success_rate_calculation(self, sample_results):
        """Test success rate calculation."""
        analyzer = StatisticsAnalyzer(sample_results)
        success_rate = analyzer.calculate_success_rate()
        assert success_rate == 75.0  # 3 out of 4 successful
    
    def test_average_solve_time(self, sample_results):
        """Test average solve time calculation."""
        analyzer = StatisticsAnalyzer(sample_results)
        avg_time = analyzer.calculate_average_solve_time()
        expected = (10.5 + 8.2 + 15.3) / 3
        assert abs(avg_time - expected) < 0.01
    
    def test_error_distribution(self, sample_results):
        """Test error distribution analysis."""
        analyzer = StatisticsAnalyzer(sample_results)
        errors = analyzer.get_error_distribution()
        assert errors["Timeout"] == 1
    
    def test_proxy_performance(self, sample_results):
        """Test proxy performance analysis."""
        analyzer = StatisticsAnalyzer(sample_results)
        proxy_stats = analyzer.get_proxy_performance()
        
        assert "ipv4" in proxy_stats
        assert proxy_stats["ipv4"]["total_runs"] == 2
        assert proxy_stats["ipv4"]["success_rate"] == 100.0
    
    def test_time_distribution(self, sample_results):
        """Test time distribution buckets."""
        analyzer = StatisticsAnalyzer(sample_results)
        distribution = analyzer.get_time_distribution()
        
        assert distribution["5-10s"] == 1  # 8.2s
        assert distribution["10-15s"] == 1  # 10.5s
        assert distribution["15-20s"] == 1  # 15.3s
    
    def test_token_statistics(self, sample_results):
        """Test token extraction statistics."""
        analyzer = StatisticsAnalyzer(sample_results)
        token_stats = analyzer.get_token_statistics()
        
        assert token_stats["total_tokens_extracted"] == 3
        assert token_stats["unique_tokens"] == 3


@pytest.mark.asyncio
class TestAutomation:
    """Test automation components (requires mocking)."""
    
    async def test_browser_initialization(self):
        """Test browser initialization with proxy."""
        # This would require mocking Playwright
        # Placeholder for integration test
        pass
    
    async def test_token_extraction(self):
        """Test token extraction from page."""
        # This would require mocking Playwright page
        # Placeholder for integration test
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
