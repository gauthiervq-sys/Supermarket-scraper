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
