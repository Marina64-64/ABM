"""
Client script for simulating customer API usage.
"""

import asyncio
import httpx
import time
from typing import Optional
import argparse
from loguru import logger


class RecaptchaAPIClient:
    """Client for interacting with reCAPTCHA solving API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def submit_task(
        self,
        sitekey: str,
        pageurl: str,
        proxy: Optional[str] = None
    ) -> Optional[str]:
        """
        Submit a reCAPTCHA solving task.
        
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            payload = {
                "sitekey": sitekey,
                "pageurl": pageurl
            }
            
            if proxy:
                payload["proxy"] = proxy
            
            logger.info(f"Submitting task for {pageurl}")
            response = await self.client.post(
                f"{self.base_url}/recaptcha/in",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("taskId")
                logger.success(f"Task submitted successfully: {task_id}")
                return task_id
            else:
                logger.error(f"Failed to submit task: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            return None
    
    async def get_result(self, task_id: str, max_wait: int = 60) -> Optional[dict]:
        """
        Get task result, polling until ready or timeout.
        
        Args:
            task_id: Task ID
            max_wait: Maximum time to wait in seconds
        
        Returns:
            Result dict with token if successful, None otherwise
        """
        try:
            start_time = time.time()
            check_interval = 2  # Check every 2 seconds
            
            logger.info(f"Waiting for task {task_id} to complete...")
            
            while time.time() - start_time < max_wait:
                response = await self.client.get(
                    f"{self.base_url}/recaptcha/res",
                    params={"taskId": task_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "ready":
                        logger.success(f"Task completed! Token: {data.get('token')[:50]}...")
                        return data
                    elif status == "error":
                        logger.error(f"Task failed: {data.get('error')}")
                        return data
                    else:
                        # Still processing
                        logger.info(f"Task status: {status}, waiting...")
                        await asyncio.sleep(check_interval)
                else:
                    logger.error(f"Error getting result: {response.status_code}")
                    return None
            
            logger.warning(f"Task timed out after {max_wait}s")
            return None
            
        except Exception as e:
            logger.error(f"Error getting result: {e}")
            return None
    
    async def solve_recaptcha(
        self,
        sitekey: str,
        pageurl: str,
        proxy: Optional[str] = None,
        max_wait: int = 60
    ) -> Optional[str]:
        """
        Complete flow: submit task and wait for result.
        
        Returns:
            reCAPTCHA token if successful, None otherwise
        """
        # Submit task
        task_id = await self.submit_task(sitekey, pageurl, proxy)
        if not task_id:
            return None
        
        # Wait for result
        result = await self.get_result(task_id, max_wait)
        if result and result.get("status") == "ready":
            return result.get("token")
        
        return None
    
    async def get_stats(self) -> Optional[dict]:
        """Get API statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/stats")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return None
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


async def main():
    """Main entry point for client simulation."""
    parser = argparse.ArgumentParser(description="reCAPTCHA API Client")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="API base URL")
    parser.add_argument("--sitekey", type=str, required=True, help="reCAPTCHA site key")
    parser.add_argument("--pageurl", type=str, required=True, help="Page URL with reCAPTCHA")
    parser.add_argument("--proxy", type=str, help="Proxy (optional)")
    parser.add_argument("--count", type=int, default=1, help="Number of tasks to run")
    args = parser.parse_args()
    
    # Setup logging
    logger.add("data/logs/client_{time}.log", rotation="10 MB")
    
    # Create client
    client = RecaptchaAPIClient(args.url)
    
    try:
        logger.info(f"Starting {args.count} reCAPTCHA solving task(s)")
        
        for i in range(args.count):
            logger.info(f"\n--- Task {i+1}/{args.count} ---")
            
            token = await client.solve_recaptcha(
                sitekey=args.sitekey,
                pageurl=args.pageurl,
                proxy=args.proxy,
                max_wait=60
            )
            
            if token:
                logger.success(f"Successfully solved reCAPTCHA!")
                logger.info(f"Token: {token}")
            else:
                logger.error(f"Failed to solve reCAPTCHA")
            
            # Small delay between tasks
            if i < args.count - 1:
                await asyncio.sleep(2)
        
        # Get statistics
        logger.info("\n--- API Statistics ---")
        stats = await client.get_stats()
        if stats:
            logger.info(f"Total tasks: {stats.get('total_tasks')}")
            logger.info(f"Success rate: {stats.get('success_rate')}%")
            logger.info(f"Average solve time: {stats.get('average_solve_time')}s")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
