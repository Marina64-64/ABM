"""
reCAPTCHA solver implementation.
"""

import asyncio
import time
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger


class RecaptchaSolver:
    """Async reCAPTCHA solver using Playwright."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
    
    async def _initialize_browser(self, proxy: Optional[str] = None):
        """Initialize browser with optional proxy."""
        playwright = await async_playwright().start()
        
        browser_args = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
            ]
        }
        
        if proxy:
            # Parse proxy string: protocol://user:pass@host:port
            try:
                if "://" in proxy:
                    protocol, rest = proxy.split("://", 1)
                    if "@" in rest:
                        auth, server = rest.split("@", 1)
                        username, password = auth.split(":", 1)
                        host, port = server.split(":", 1)
                        
                        browser_args["proxy"] = {
                            "server": f"{protocol}://{host}:{port}",
                            "username": username,
                            "password": password
                        }
                    else:
                        browser_args["proxy"] = {"server": proxy}
            except Exception as e:
                logger.warning(f"Failed to parse proxy: {e}")
        
        return await playwright.chromium.launch(**browser_args)
    
    async def solve(
        self,
        sitekey: str,
        pageurl: str,
        proxy: Optional[str] = None,
        timeout: int = 60
    ) -> Dict:
        """
        Solve reCAPTCHA challenge.
        
        Args:
            sitekey: reCAPTCHA site key
            pageurl: URL of the page with reCAPTCHA
            proxy: Optional proxy string
            timeout: Maximum time to wait for solution (seconds)
        
        Returns:
            Dict with success status, token, solve_time, and error
        """
        result = {
            "success": False,
            "token": None,
            "solve_time": None,
            "error": None
        }
        
        start_time = time.time()
        browser = None
        
        try:
            logger.info(f"Starting to solve reCAPTCHA for {pageurl}")
            
            # Initialize browser
            browser = await self._initialize_browser(proxy)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Navigate to page
            await page.goto(pageurl, wait_until="networkidle", timeout=30000)
            
            # Wait for reCAPTCHA iframe
            await page.wait_for_selector("iframe[src*='recaptcha']", timeout=10000)
            
            # Get reCAPTCHA iframe
            recaptcha_frame = page.frame_locator("iframe[src*='recaptcha/api2/anchor']")
            
            # Click checkbox
            checkbox = recaptcha_frame.locator("#recaptcha-anchor")
            await checkbox.click()
            
            # Wait a bit for processing
            await asyncio.sleep(2)
            
            # Check if solved immediately (no challenge)
            is_checked = await checkbox.get_attribute("aria-checked")
            
            if is_checked == "true":
                # Extract token
                token = await self._extract_token(page)
                
                if token:
                    result["success"] = True
                    result["token"] = token
                    result["solve_time"] = time.time() - start_time
                    logger.success(f"Solved without challenge in {result['solve_time']:.2f}s")
                else:
                    result["error"] = "Token not found after checkbox click"
            else:
                # Challenge appeared - attempt to solve
                logger.info("Challenge detected, attempting to solve...")
                
                # Wait for challenge iframe
                try:
                    await page.wait_for_selector("iframe[src*='recaptcha/api2/bframe']", timeout=5000)
                    
                    # This is where advanced challenge solving would go
                    # For now, wait and check periodically
                    max_wait = timeout - (time.time() - start_time)
                    check_interval = 2
                    elapsed = 0
                    
                    while elapsed < max_wait:
                        await asyncio.sleep(check_interval)
                        elapsed += check_interval
                        
                        # Check if solved
                        token = await self._extract_token(page)
                        if token:
                            result["success"] = True
                            result["token"] = token
                            result["solve_time"] = time.time() - start_time
                            logger.success(f"Challenge solved in {result['solve_time']:.2f}s")
                            break
                    
                    if not result["success"]:
                        result["error"] = "Challenge timeout"
                        
                except Exception as e:
                    result["error"] = f"Challenge error: {str(e)}"
            
            await context.close()
            
        except Exception as e:
            result["error"] = f"Solver error: {str(e)}"
            logger.error(f"Error solving reCAPTCHA: {e}")
        finally:
            if browser:
                await browser.close()
        
        return result
    
    async def _extract_token(self, page: Page) -> Optional[str]:
        """Extract reCAPTCHA token from page."""
        try:
            token = await page.evaluate("""
                () => {
                    const response = document.querySelector('[name="g-recaptcha-response"]');
                    return response ? response.value : null;
                }
            """)
            return token if token else None
        except Exception as e:
            logger.error(f"Error extracting token: {e}")
            return None
    
    async def close(self):
        """Close browser if open."""
        if self.browser:
            await self.browser.close()
            self.browser = None
