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
