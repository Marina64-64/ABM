"""
Task 3: DOM Scraping
Extract images and text from web pages.
"""

import asyncio
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional
import argparse

from playwright.async_api import async_playwright, Page
from loguru import logger

from .image_extractor import ImageExtractor


class DOMScraper:
    """DOM scraper for extracting images and text."""
    
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_extractor = ImageExtractor()
    
    async def scrape_page(self, url: str) -> Dict:
        """
        Scrape a page for images and text.
        
        Args:
            url: URL to scrape
        
        Returns:
            Dict with all_images, visible_images, and text_instructions
        """
        logger.info(f"Starting to scrape {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Apply stealth
            from playwright_stealth import Stealth
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)
            
            try:
                # Navigate to page
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2)  # Let page fully render
                
                # Extract all images
                logger.info("Extracting all images...")
                all_images = await self.extract_all_images(page)
                
                # Extract visible images only
                logger.info("Extracting visible images...")
                visible_images = await self.extract_visible_images(page)
                
                # Extract visible text
                logger.info("Extracting visible text...")
                text_instructions = await self.extract_visible_text(page)
                
                result = {
                    "url": url,
                    "all_images": all_images,
                    "visible_images": visible_images,
                    "text_instructions": text_instructions
                }
                
                logger.success(f"Scraping complete: {len(all_images)} total images, {len(visible_images)} visible")
                
                return result
                
            finally:
                await context.close()
                await browser.close()
    
    async def extract_all_images(self, page: Page) -> List[Dict]:
        """Extract all images from page as base64."""
        images = []
        
        # Get all img elements
        img_elements = await page.query_selector_all("img")
        
        for idx, img in enumerate(img_elements):
            try:
                # Get image source
                src = await img.get_attribute("src")
                alt = await img.get_attribute("alt") or ""
                
                if not src:
                    continue
                
                # Convert to base64
                base64_data = await self.image_extractor.get_image_as_base64(page, src)
                
                if base64_data:
                    images.append({
                        "index": idx,
                        "src": src,
                        "alt": alt,
                        "base64": base64_data,
                        "type": "img"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to extract image {idx}: {e}")
        
        # Get canvas elements
        canvas_elements = await page.query_selector_all("canvas")
        for idx, canvas in enumerate(canvas_elements):
            try:
                canvas_data = await self.image_extractor.get_canvas_as_base64(page, canvas)
                if canvas_data:
                    images.append({
                        "index": len(images),
                        "src": "canvas",
                        "alt": "",
                        "base64": canvas_data,
                        "type": "canvas"
                    })
            except Exception as e:
                logger.warning(f"Failed to extract canvas {idx}: {e}")
        
        # Get SVG elements
        svg_elements = await page.query_selector_all("svg")
        for idx, svg in enumerate(svg_elements):
            try:
                svg_data = await self.image_extractor.get_svg_as_base64(page, svg)
                if svg_data:
                    images.append({
                        "index": len(images),
                        "src": "svg",
                        "alt": "",
                        "base64": svg_data,
                        "type": "svg"
                    })
            except Exception as e:
                logger.warning(f"Failed to extract SVG {idx}: {e}")
        
        logger.info(f"Extracted {len(images)} total images")
        return images
    
    async def extract_visible_images(self, page: Page) -> List[Dict]:
        """Extract only visible images."""
        all_images_data = await self.extract_all_images(page)
        visible_images = []
        
        # Re-query elements to check visibility
        img_elements = await page.query_selector_all("img")
        
        for idx, img in enumerate(img_elements):
            try:
                is_visible = await self.image_extractor.is_element_visible(page, img)
                
                if is_visible and idx < len(all_images_data):
                    visible_images.append(all_images_data[idx])
                    
            except Exception as e:
                logger.warning(f"Failed to check visibility for image {idx}: {e}")
        
        logger.info(f"Found {len(visible_images)} visible images")
        return visible_images
    
    async def extract_visible_text(self, page: Page) -> str:
        """Extract visible text instructions from page."""
        try:
            # Extract all visible text
            text = await page.evaluate("""
                () => {
                    function isVisible(element) {
                        if (!element) return false;
                        const style = window.getComputedStyle(element);
                        return style.display !== 'none' &&
                               style.visibility !== 'hidden' &&
                               style.opacity !== '0' &&
                               element.offsetWidth > 0 &&
                               element.offsetHeight > 0;
                    }
                    
                    function getVisibleText(element) {
                        let text = '';
                        
                        for (let node of element.childNodes) {
                            if (node.nodeType === Node.TEXT_NODE) {
                                const content = node.textContent.trim();
                                if (content && isVisible(element)) {
                                    text += content + ' ';
                                }
                            } else if (node.nodeType === Node.ELEMENT_NODE) {
                                if (isVisible(node)) {
                                    text += getVisibleText(node);
                                }
                            }
                        }
                        
                        return text;
                    }
                    
                    return getVisibleText(document.body);
                }
            """)
            
            # Clean up text
            text = " ".join(text.split())
            logger.info(f"Extracted {len(text)} characters of visible text")
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract visible text: {e}")
            return ""
    
    def save_results(self, result: Dict):
        """Save scraping results to files."""
        # Save all images
        all_images_file = self.output_dir / "allimages.json"
        with open(all_images_file, 'w') as f:
            json.dump(result["all_images"], f, indent=2)
        logger.info(f"Saved all images to {all_images_file}")
        
        # Save visible images only
        visible_images_file = self.output_dir / "visible_images_only.json"
        with open(visible_images_file, 'w') as f:
            json.dump(result["visible_images"], f, indent=2)
        logger.info(f"Saved visible images to {visible_images_file}")
        
        # Save text instructions
        text_file = self.output_dir / "text_instructions.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(result["text_instructions"])
        logger.info(f"Saved text instructions to {text_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DOM Scraper")
    parser.add_argument("--url", type=str, required=True, help="URL to scrape")
    parser.add_argument("--output", type=str, default="data/output", help="Output directory")
    args = parser.parse_args()
    
    # Setup logging
    logger.add("data/logs/scraper_{time}.log", rotation="10 MB")
    
    # Create scraper
    scraper = DOMScraper(args.output)
    
    # Scrape page
    result = await scraper.scrape_page(args.url)
    
    # Save results
    scraper.save_results(result)
    
    logger.success("Scraping complete!")


if __name__ == "__main__":
    asyncio.run(main())
