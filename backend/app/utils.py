import re

def convert_to_liters(amount, unit):
    if unit == 'ml': return amount / 1000
    if unit == 'cl': return amount / 100
    return amount

def parse_volume_from_text(text: str) -> float:
    if not text: return 0.0
    text = str(text).lower().replace(',', '.')
    match_multi = re.search(r'(\d+)\s*x\s*([\d\.]+)\s*(l|cl|ml)', text)
    if match_multi:
        count = int(match_multi.group(1))
        size = float(match_multi.group(2))
        unit = match_multi.group(3)
        total = count * size
        return convert_to_liters(total, unit)
    match_single = re.search(r'(?<!x)\s*([\d\.]+)\s*(l|cl|ml)', text)
    if match_single:
        size = float(match_single.group(1))
        unit = match_single.group(2)
        return convert_to_liters(size, unit)
    return 0.0

def parse_unit_count(text: str) -> int:
    """Parse the number of units (cans/bottles) from text like '6 x 330 ml' or '12 x 250 ml'"""
    if not text:
        return 1
    text = str(text).lower()
    match = re.search(r'(\d+)\s*x\s*[\d\.]+\s*(l|cl|ml)', text)
    if match:
        return int(match.group(1))
    return 1

def parse_unit_size(text: str) -> tuple:
    """Parse unit size and unit type from text. Returns (size, unit) like (330.0, 'ML') or (1.5, 'L')"""
    if not text:
        return (0.0, '')
    text = str(text).lower().replace(',', '.')
    
    # Check for multi-pack format like "6 x 330 ml"
    match_multi = re.search(r'\d+\s*x\s*([\d\.]+)\s*(l|cl|ml)', text)
    if match_multi:
        size = float(match_multi.group(1))
        unit = match_multi.group(2).upper()
        return (size, unit)
    
    # Check for single format like "1.5 L" or "330ml"
    match_single = re.search(r'(?<!x)\s*([\d\.]+)\s*(l|cl|ml)', text)
    if match_single:
        size = float(match_single.group(1))
        unit = match_single.group(2).upper()
        return (size, unit)
    
    return (0.0, '')

def calculate_price_per_liter(price: float, volume_str: str, name: str) -> float:
    liters = parse_volume_from_text(volume_str)
    if liters == 0:
        liters = parse_volume_from_text(name)
    if liters == 0: return 0.0
    return round(price / liters, 2)

def extract_price_from_text(price_text: str) -> float:
    """
    Extract numeric price from text string.
    Handles common formats: €12.99, 12,99€, 12.99, etc.
    
    Args:
        price_text: Text containing a price
        
    Returns:
        Extracted price as float, or 0.0 if parsing fails
    """
    if not price_text:
        return 0.0
    
    # Clean up the text
    price_clean = price_text.replace('\n', '').replace('€', '').replace(',', '.').strip()
    
    try:
        # Extract just the numeric value using regex
        price_match = re.search(r'(\d+[.,]\d+|\d+)', price_clean)
        if price_match:
            return float(price_match.group(1).replace(',', '.'))
    except (ValueError, AttributeError):
        pass
    
    return 0.0

def parse_price_from_element_text(element_text: str) -> float:
    """
    Parse price from HTML element text.
    Removes currency symbols and converts to float.
    
    Args:
        element_text: Text from HTML element containing price
        
    Returns:
        Parsed price as float, or 0.0 if parsing fails
    """
    if not element_text:
        return 0.0
    
    # Remove currency symbols and convert to float
    price_txt = re.sub(r'[^\d,.]', '', element_text)
    price_txt = price_txt.replace(',', '.')
    try:
        return float(price_txt)
    except ValueError:
        return 0.0

def complete_url(url: str, base_url: str) -> str:
    """
    Complete a relative URL to an absolute URL.
    
    Args:
        url: URL to complete (may be relative or absolute)
        base_url: Base URL to use (e.g., "https://www.example.com")
        
    Returns:
        Complete absolute URL
    """
    if not url:
        return ""
    
    if url.startswith('http'):
        return url
    elif url.startswith('//'):
        return f"https:{url}"
    elif url.startswith('/'):
        return f"{base_url.rstrip('/')}{url}"
    else:
        return f"{base_url.rstrip('/')}/{url}"


def log_scraped_html_debug(logger, store_name: str, response_text: str, soup, cards_found: int):
    """
    Log detailed HTML debugging information when DEBUG_MODE is enabled.
    
    Args:
        logger: Logger instance to use
        store_name: Name of the store being scraped
        response_text: Raw HTML response text
        soup: BeautifulSoup object
        cards_found: Number of product cards found
    """
    import os
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    if not DEBUG_MODE:
        return
    
    # Log HTML content length
    logger.debug(f"  {store_name}: HTML content length: {len(response_text)} characters")
    
    # Log body text content
    body = soup.find('body')
    if body:
        body_text = body.get_text(strip=True, separator=' ')
        logger.debug(f"  {store_name}: Page body text (first 500 chars): {body_text[:500]}")
        logger.debug(f"  {store_name}: Page body text (last 500 chars): {body_text[-500:]}")
    else:
        logger.debug(f"  {store_name}: No <body> tag found in HTML")
    
    # Check for JavaScript-rendered content indicators
    js_indicators = ['window.__', 'React', 'Vue', 'Angular', '__NEXT_DATA__']
    if any(indicator in response_text for indicator in js_indicators):
        logger.debug(f"  {store_name}: ⚠️  Site appears to use JavaScript rendering")
    
    # If no cards found, log HTML structure for debugging
    if cards_found == 0:
        all_elements = soup.find_all(True, limit=20)
        element_tags = [f"<{el.name}>" for el in all_elements]
        logger.debug(f"  {store_name}: First 20 HTML elements found: {', '.join(element_tags)}")
        logger.debug(f"  {store_name}: Raw HTML structure (first 1000 chars): {response_text[:1000]}")
