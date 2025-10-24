import re
import time
from datetime import datetime

def clean_filename(text: str) -> str:
    """
    Clean text to create a safe filename
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text suitable for filenames
    
    Examples:
        "My'Design Image" -> "my-design-image"
        "Product Name 123!" -> "product-name-123"
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Replace multiple consecutive hyphens with single hyphen
    text = re.sub(r'-+', '-', text)
    
    return text

def generate_filename(prefix: str, variant_name: str, extension: str = 'png') -> str:
    """
    Generate a clean filename with timestamp
    
    Args:
        prefix: Filename prefix (e.g., product name)
        variant_name: Variant name
        extension: File extension (default: png)
    
    Returns:
        Clean filename with timestamp
    
    Examples:
        generate_filename("My Design", "Main View", "png")
        -> "my-design-main-view-1729761234567.png"
    """
    # Clean the prefix and variant name
    clean_prefix = clean_filename(prefix)
    clean_variant = clean_filename(variant_name)
    
    # Generate timestamp (milliseconds)
    timestamp = int(time.time() * 1000)
    
    # Combine parts
    filename = f"{clean_prefix}-{clean_variant}-{timestamp}.{extension}"
    
    return filename

def get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds"""
    return int(time.time() * 1000)