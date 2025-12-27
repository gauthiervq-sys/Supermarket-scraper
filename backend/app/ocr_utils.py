"""
OCR utilities for extracting text from images, particularly for price extraction
from websites that embed prices in images to prevent scraping.
"""
import re
import logging
from io import BytesIO
from typing import Optional
import base64

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR libraries not available. Install pytesseract and Pillow to enable OCR functionality.")


def parse_price_text(price_text: str) -> Optional[float]:
    """
    Parse price from text string (extracted from DOM or OCR).
    Handles common price formats: €12.99, 12,99€, 12.99, etc.
    
    This function handles both simple text prices from DOM elements and
    potentially noisy OCR text from images.
    
    Args:
        price_text: Text that may contain a price
        
    Returns:
        Extracted price as float, or None if parsing failed
    """
    if not price_text:
        return None
    
    # Try simple parsing first (for clean DOM text)
    try:
        # Clean up the text
        cleaned = price_text.replace('\n', '').replace('€', '').replace(' ', '').strip()
        
        # Skip if contains letters (except €)
        if any(c.isalpha() for c in cleaned):
            return None
        
        # Handle European format (comma as decimal separator)
        # Only replace comma if it appears to be a decimal separator (has 2 digits after it)
        if ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # This looks like a decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Might be a thousands separator, skip it
                cleaned = cleaned.replace(',', '')
        
        # Parse as float
        price = float(cleaned)
        return price if price > 0 else None
    except (ValueError, AttributeError):
        pass
    
    # If simple parsing failed, try regex patterns (for noisy OCR text)
    text = price_text.strip()
    
    # Pattern 1: €12.99 or 12.99€ (with decimal point for cents)
    match = re.search(r'€?\s*(\d+)\.(\d{2})(?!\d)\s*€?', text)
    if match:
        try:
            euros = int(match.group(1))
            cents = int(match.group(2))
            if 0 <= cents <= 99:
                return float(f"{euros}.{cents:02d}")
        except (ValueError, IndexError):
            pass
    
    # Pattern 2: 12,99€ or €12,99 (with comma for cents - European format)
    match = re.search(r'€?\s*(\d+),(\d{2})(?!\d)\s*€?', text)
    if match:
        try:
            euros = int(match.group(1))
            cents = int(match.group(2))
            if 0 <= cents <= 99:
                return float(f"{euros}.{cents:02d}")
        except (ValueError, IndexError):
            pass
    
    # Pattern 3: Whole euros only (€12 or 12€)
    match = re.search(r'€?\s*(\d+)(?!\d*[.,]\d)\s*€?', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    return None


def extract_price_from_image(image_data: bytes) -> Optional[float]:
    """
    Extract price from an image using OCR.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Extracted price as float, or None if extraction failed
    """
    if not OCR_AVAILABLE:
        return None
    
    try:
        # Load image from bytes
        image = Image.open(BytesIO(image_data))
        
        # Convert to grayscale for better OCR accuracy
        image = image.convert('L')
        
        # Try multiple OCR configurations for better accuracy
        # PSM 7: Treat image as single text line (best for simple price tags)
        # PSM 8: Treat image as single word (fallback)
        configs = [
            '--psm 7 -c tessedit_char_whitelist=0123456789.,€',
            '--psm 8 -c tessedit_char_whitelist=0123456789.,€',
            '--psm 6 -c tessedit_char_whitelist=0123456789.,€',  # Single uniform block of text
        ]
        
        for config in configs:
            text = pytesseract.image_to_string(image, config=config)
            price = parse_price_text(text)
            if price:
                return price
        
        return None
    except Exception as e:
        logger.debug(f"OCR extraction failed: {e}")
        return None


def extract_price_from_base64(base64_str: str) -> Optional[float]:
    """
    Extract price from a base64-encoded image.
    
    Args:
        base64_str: Base64-encoded image string
        
    Returns:
        Extracted price as float, or None if extraction failed
    """
    if not OCR_AVAILABLE:
        return None
    
    try:
        # Remove data URL prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',', 1)[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_str)
        return extract_price_from_image(image_data)
    except Exception as e:
        logger.debug(f"Base64 OCR extraction failed: {e}")
        return None


async def extract_price_from_element(page, element) -> Optional[float]:
    """
    Extract price from a DOM element that may contain an image with embedded price.
    
    Args:
        page: Playwright page object
        element: Playwright element handle
        
    Returns:
        Extracted price as float, or None if extraction failed
    """
    if not OCR_AVAILABLE:
        return None
    
    try:
        # Take screenshot of the element
        screenshot = await element.screenshot()
        return extract_price_from_image(screenshot)
    except Exception as e:
        logger.debug(f"Element OCR extraction failed: {e}")
        return None



async def try_ocr_price_extraction(page, price_element) -> Optional[float]:
    """
    Attempt to extract price using OCR as a fallback when normal text extraction fails.
    
    This function should be called when:
    1. Price element exists but inner_text() returns empty or non-numeric value
    2. Price appears to be embedded in an image
    
    Args:
        page: Playwright page object
        price_element: Playwright element handle that may contain image-based price
        
    Returns:
        Extracted price as float, or None if extraction failed
    """
    if not OCR_AVAILABLE:
        logger.debug("OCR not available, skipping image price extraction")
        return None
    
    try:
        # First, check if there's an image within the price element
        img = await price_element.query_selector('img')
        if img:
            logger.debug("Found image in price element, attempting OCR")
            price = await extract_price_from_element(page, img)
            if price:
                return price
        
        # If no image found or OCR failed, try OCR on the entire price element
        logger.debug("Attempting OCR on entire price element")
        price = await extract_price_from_element(page, price_element)
        return price
    except Exception as e:
        logger.debug(f"OCR price extraction failed: {e}")
        return None
