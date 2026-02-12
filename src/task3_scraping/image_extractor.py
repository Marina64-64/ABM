"""
Image extraction utilities for DOM scraping.
"""

import base64
import io
from typing import Optional
from playwright.async_api import Page, ElementHandle
from loguru import logger


class ImageExtractor:
    """Utilities for extracting and processing images."""
    
    async def get_image_as_base64(self, page: Page, src: str) -> Optional[str]:
        """
        Get image as base64 string.
        
        Args:
            page: Playwright page
            src: Image source URL
        
        Returns:
            Base64 encoded image data or None
        """
        try:
            # If already base64
            if src.startswith("data:image"):
                # Extract base64 part
                if ";base64," in src:
                    return src.split(";base64,")[1]
                return None
            
            # Fetch image and convert to base64
            image_data = await page.evaluate("""
                async (src) => {
                    try {
                        const response = await fetch(src);
                        const blob = await response.blob();
                        return new Promise((resolve) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    } catch (e) {
                        return null;
                    }
                }
            """, src)
            
            if image_data and ";base64," in image_data:
                return image_data.split(";base64,")[1]
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get image as base64: {e}")
            return None
    
    async def get_canvas_as_base64(self, page: Page, canvas: ElementHandle) -> Optional[str]:
        """
        Get canvas element as base64 PNG.
        
        Args:
            page: Playwright page
            canvas: Canvas element handle
        
        Returns:
            Base64 encoded PNG data or None
        """
        try:
            canvas_data = await page.evaluate("""
                (canvas) => {
                    try {
                        return canvas.toDataURL('image/png');
                    } catch (e) {
                        return null;
                    }
                }
            """, canvas)
            
            if canvas_data and ";base64," in canvas_data:
                return canvas_data.split(";base64,")[1]
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get canvas as base64: {e}")
            return None
    
    async def get_svg_as_base64(self, page: Page, svg: ElementHandle) -> Optional[str]:
        """
        Get SVG element as base64 PNG.
        
        Args:
            page: Playwright page
            svg: SVG element handle
        
        Returns:
            Base64 encoded PNG data or None
        """
        try:
            svg_data = await page.evaluate("""
                (svg) => {
                    try {
                        const serializer = new XMLSerializer();
                        const svgString = serializer.serializeToString(svg);
                        const base64 = btoa(unescape(encodeURIComponent(svgString)));
                        return base64;
                    } catch (e) {
                        return null;
                    }
                }
            """, svg)
            
            return svg_data
            
        except Exception as e:
            logger.debug(f"Failed to get SVG as base64: {e}")
            return None
    
    async def is_element_visible(self, page: Page, element: ElementHandle) -> bool:
        """
        Check if element is visible in viewport.
        
        Args:
            page: Playwright page
            element: Element to check
        
        Returns:
            True if visible, False otherwise
        """
        try:
            is_visible = await page.evaluate("""
                (element) => {
                    if (!element) return false;
                    
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    
                    // Check if element has dimensions
                    if (rect.width === 0 || rect.height === 0) {
                        return false;
                    }
                    
                    // Check CSS visibility
                    if (style.display === 'none' ||
                        style.visibility === 'hidden' ||
                        style.opacity === '0') {
                        return false;
                    }
                    
                    // Check if in viewport
                    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
                    const windowWidth = window.innerWidth || document.documentElement.clientWidth;
                    
                    const vertInView = (rect.top <= windowHeight) && ((rect.top + rect.height) >= 0);
                    const horInView = (rect.left <= windowWidth) && ((rect.left + rect.width) >= 0);
                    
                    return vertInView && horInView;
                }
            """, element)
            
            return is_visible
            
        except Exception as e:
            logger.debug(f"Failed to check element visibility: {e}")
            return False
    
    async def get_element_screenshot(self, element: ElementHandle) -> Optional[str]:
        """
        Take screenshot of element and return as base64.
        
        Args:
            element: Element to screenshot
        
        Returns:
            Base64 encoded PNG or None
        """
        try:
            screenshot_bytes = await element.screenshot()
            base64_data = base64.b64encode(screenshot_bytes).decode('utf-8')
            return base64_data
        except Exception as e:
            logger.debug(f"Failed to screenshot element: {e}")
            return None
    
    def decode_base64_image(self, base64_str: str) -> Optional[bytes]:
        """
        Decode base64 string to image bytes.
        
        Args:
            base64_str: Base64 encoded image
        
        Returns:
            Image bytes or None
        """
        try:
            return base64.b64decode(base64_str)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return None
    
    def save_base64_image(self, base64_str: str, output_path: str):
        """
        Save base64 image to file.
        
        Args:
            base64_str: Base64 encoded image
            output_path: Path to save image
        """
        try:
            image_bytes = self.decode_base64_image(base64_str)
            if image_bytes:
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                logger.info(f"Saved image to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
