"""
Task 1: Automation Script
Automated reCAPTCHA solving with proxy support and statistics generation.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from loguru import logger

from .config import Config
from .proxy_manager import ProxyManager
from .statistics import StatisticsAnalyzer


class RecaptchaAutomation:
    """Main automation class for reCAPTCHA solving."""
    
    def __init__(self, config: Config):
        self.config = config
        self.proxy_manager = ProxyManager(config)
        self.results: List[Dict] = []
        self.browser: Optional[Browser] = None
        
    async def initialize_browser(self, proxy: Optional[Dict] = None):
        """Initialize browser with optional proxy."""
        playwright = await async_playwright().start()
        
        browser_args = {
            "headless": self.config.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        }
        
        if proxy:
            browser_args["proxy"] = {
                "server": f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}",
            }
            if proxy.get('username'):
                browser_args["proxy"]["username"] = proxy['username']
                browser_args["proxy"]["password"] = proxy['password']
        
        self.browser = await playwright.chromium.launch(**browser_args)
        return self.browser
    
    async def solve_recaptcha(self, page: Page, run_number: int) -> Dict:
        """
        Attempt to solve reCAPTCHA v3 on the page.
        """
        result = {
            "run": run_number,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "token": None,
            "score": None,
            "solve_time": None,
            "error": None,
            "proxy_type": None
        }
        
        start_time = time.time()
        
        try:
            # Navigate to target site
            logger.info(f"Run {run_number}: Navigating to {self.config.target_url}")
            await page.goto(self.config.target_url, wait_until="networkidle", timeout=30000)
            
            # Click the button to start v3 test
            logger.info(f"Run {run_number}: Clicking 'Run reCAPTCHA v3 test' button")
            await page.click("#btn")
            
            # Wait for the output text to appear and be stable
            # The output is a JSON string in #out
            await asyncio.sleep(2)  # Wait for API call
            
            # Wait for content in the #out element
            await page.wait_for_function('document.getElementById("out").textContent.includes("{")')
            
            # Extract output
            output_text = await page.inner_text("#out")
            logger.info(f"Run {run_number}: Raw output: {output_text}")
            
            try:
                data = json.loads(output_text)
                if data.get("success"):
                    result["success"] = True
                    result["token"] = data.get("token") or data.get("challenge_ts") # Use timestamp as fallback or just mark success
                    result["score"] = data.get("score")
                    result["solve_time"] = time.time() - start_time
                    logger.success(f"Run {run_number}: Solved. Score: {result['score']}")
                else:
                    result["error"] = f"API returned failure: {data}"
                    logger.warning(f"Run {run_number}: Solve failed - {data}")
            except json.JSONDecodeError:
                result["error"] = f"Invalid JSON in output: {output_text}"
                logger.error(f"Run {run_number}: Result parsing error")
                    
        except PlaywrightTimeout as e:
            result["error"] = f"Timeout: {str(e)}"
            logger.error(f"Run {run_number}: Timeout - {e}")
        except Exception as e:
            result["error"] = f"Error: {str(e)}"
            logger.error(f"Run {run_number}: Error - {e}")
        
        return result
    
    async def run_single_test(self, run_number: int, proxy_type: Optional[str] = None) -> Dict:
        """Run a single automation test."""
        proxy = None
        if proxy_type:
            proxy = self.proxy_manager.get_proxy(proxy_type)
        
        browser = await self.initialize_browser(proxy)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            result = await self.solve_recaptcha(page, run_number)
            result["proxy_type"] = proxy_type
            return result
        finally:
            await context.close()
            await browser.close()
    
    async def run_tests(self, num_runs: int, proxy_type: Optional[str] = None):
        """Run multiple automation tests."""
        logger.info(f"Starting {num_runs} automation runs with proxy type: {proxy_type or 'none'}")
        
        for i in range(1, num_runs + 1):
            try:
                result = await self.run_single_test(i, proxy_type)
                self.results.append(result)
                
                # Save intermediate results every 10 runs
                if i % 10 == 0:
                    self.save_results()
                    logger.info(f"Progress: {i}/{num_runs} runs completed")
                
                # Small delay between runs
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Run {i} failed with error: {e}")
                self.results.append({
                    "run": i,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e),
                    "proxy_type": proxy_type
                })
        
        # Final save
        self.save_results()
        logger.info(f"Completed all {num_runs} runs")
    
    def save_results(self):
        """Save results to JSON file."""
        output_file = Path(self.config.results_dir) / "automation_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
    
    def generate_statistics(self):
        """Generate statistics from results."""
        analyzer = StatisticsAnalyzer(self.results)
        stats = analyzer.generate_report()
        
        # Save statistics
        stats_file = Path(self.config.results_dir) / "statistics_report.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Print summary
        analyzer.print_summary()
        
        return stats


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="reCAPTCHA Automation Script")
    parser.add_argument("--runs", type=int, default=10, help="Number of test runs")
    parser.add_argument("--proxy-type", choices=["ipv4", "ipv6", "none"], default="none", help="Proxy type to use")
    parser.add_argument("--url", type=str, help="Target URL (overrides config)")
    args = parser.parse_args()
    
    # Initialize configuration
    config = Config()
    if args.url:
        config.target_url = args.url
    
    # Setup logging
    logger.add(
        Path(config.logs_dir) / "automation_{time}.log",
        rotation="100 MB",
        retention="10 days",
        level="INFO"
    )
    
    # Run automation
    automation = RecaptchaAutomation(config)
    
    proxy_type = None if args.proxy_type == "none" else args.proxy_type
    await automation.run_tests(args.runs, proxy_type)
    
    # Generate statistics
    automation.generate_statistics()
    
    logger.info("Automation complete!")


if __name__ == "__main__":
    asyncio.run(main())
