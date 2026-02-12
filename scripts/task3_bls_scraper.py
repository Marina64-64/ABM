"""
Task 3: BLS Spain Global Scraper
Specific implementation for scraping the BLS Spain CAPTCHA page.
"""

import asyncio
import os
from src.task3_scraping.dom_scraper import DOMScraper
from loguru import logger

async def run_bls_scraper():
    # Target URL from requirements
    target_url = "https://egypt.blsspainglobal.com/Global/CaptchaPublic/GenerateCaptcha?data=4CDiA9odF2%2b%2bsWCkAU8htqZkgDyUa5SR6waINtJfg1ThGb6rPIIpxNjefP9UkAaSp%2fGsNNuJJi5Zt1nbVACkDRusgqfb418%2bScFkcoa1F0I%3d"
    
    # Initialize scraper (output to root or data/output)
    scraper = DOMScraper(output_dir=".")
    
    try:
        logger.info(f"Starting Task 3 scraping for: {target_url}")
        
        # Scrape the page
        result = await scraper.scrape_page(target_url)
        
        # Save results (will create allimages.json and visible_images_only.json in current dir)
        scraper.save_results(result)
        
        logger.success("Task 3 completed successfully!")
        logger.info(f"All images saved to: {os.path.abspath('allimages.json')}")
        logger.info(f"Visible images saved to: {os.path.abspath('visible_images_only.json')}")
        logger.info(f"Visible text saved to: {os.path.abspath('text_instructions.txt')}")

    except Exception as e:
        logger.error(f"Task 3 failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_bls_scraper())
