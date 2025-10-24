"""
Fast image compositing using optimized PIL operations
This version is optimized for speed without requiring PyTorch/CUDA
"""
import io
from PIL import Image
import requests
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
import math

class FastImageCompositor:
    """Optimized image compositor for faster processing"""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize compositor with thread pool
        
        Args:
            max_workers: Maximum number of worker threads for parallel processing
        """
        self.max_workers = max_workers
        self.session = requests.Session()  # Reuse HTTP connections
    
    def load_image_from_url(self, url: str) -> Image.Image:
        """Load image from URL with connection pooling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return img.convert('RGBA')
        except Exception as e:
            raise Exception(f"Failed to load image from URL {url}: {str(e)}")
    
    def load_images_parallel(self, urls: List[str]) -> List[Image.Image]:
        """Load multiple images in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            images = list(executor.map(self.load_image_from_url, urls))
        return images
    
    @staticmethod
    def resize_image_fast(image: Image.Image, width: int, height: int, maintain_aspect: bool = True) -> Image.Image:
        """
        Fast resize with optimized resampling
        Uses LANCZOS for quality, but can switch to BILINEAR for speed
        """
        if not maintain_aspect:
            # Use BILINEAR for faster processing when aspect ratio doesn't matter
            return image.resize((int(width), int(height)), Image.Resampling.BILINEAR)
        
        # Calculate aspect ratios
        img_aspect = image.width / image.height
        target_aspect = width / height
        
        # Fit image within bounds while maintaining aspect ratio
        if img_aspect > target_aspect:
            new_width = int(width)
            new_height = int(width / img_aspect)
        else:
            new_height = int(height)
            new_width = int(height * img_aspect)
        
        # Use LANCZOS for quality, BILINEAR for speed
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def composite_fast(
        base_image: Image.Image,
        overlay_image: Image.Image,
        x: float,
        y: float,
        width: float,
        height: float,
        rotation: float = 0,
        opacity: float = 1.0,
        center: bool = False
    ) -> Image.Image:
        """
        Fast composite operation
        """
        # Resize overlay to fit within the design area
        resized_overlay = FastImageCompositor.resize_image_fast(
            overlay_image, width, height, maintain_aspect=True
        )
        
        # Apply rotation if needed
        if rotation != 0:
            resized_overlay = resized_overlay.rotate(
                rotation, 
                expand=True, 
                resample=Image.Resampling.BILINEAR  # Faster than BICUBIC
            )
        
        # Apply opacity if needed
        if opacity < 1.0:
            alpha = resized_overlay.split()[-1]
            alpha = alpha.point(lambda p: int(p * opacity))
            resized_overlay.putalpha(alpha)
        
        # Calculate position
        paste_x = int(x)
        paste_y = int(y)
        
        # Center the design within the area if requested
        if center:
            paste_x = int(x + (width - resized_overlay.width) / 2)
            paste_y = int(y + (height - resized_overlay.height) / 2)
        
        # Create result (reuse base image to save memory)
        result = base_image.copy()
        
        # Paste overlay
        if resized_overlay.mode == 'RGBA':
            result.paste(resized_overlay, (paste_x, paste_y), resized_overlay)
        else:
            result.paste(resized_overlay, (paste_x, paste_y))
        
        return result
    
    @staticmethod
    def image_to_bytes_fast(image: Image.Image, format: str = 'PNG', optimize: bool = False) -> bytes:
        """
        Convert image to bytes with optional optimization
        
        Args:
            image: PIL Image
            format: Output format (PNG, JPEG, etc.)
            optimize: If True, optimize file size (slower but smaller)
        """
        img_byte_arr = io.BytesIO()
        
        if format.upper() == 'PNG':
            # PNG optimization options
            image.save(img_byte_arr, format=format, optimize=optimize, compress_level=6)
        elif format.upper() in ['JPEG', 'JPG']:
            # JPEG optimization
            image.save(img_byte_arr, format='JPEG', quality=90, optimize=optimize)
        else:
            image.save(img_byte_arr, format=format)
        
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
    
    def composite_batch(
        self,
        mockup_urls: List[str],
        design_url: str,
        design_areas: List[Dict],
        options: Dict = None
    ) -> List[bytes]:
        """
        Composite multiple mockups in parallel
        
        Args:
            mockup_urls: List of mockup image URLs
            design_url: Design image URL
            design_areas: List of design area specifications
            options: Optional settings
        
        Returns:
            List of composited image bytes
        """
        options = options or {}
        
        # Load design image once
        design = self.load_image_from_url(design_url)
        
        # Load all mockups in parallel
        mockups = self.load_images_parallel(mockup_urls)
        
        # Composite all images in parallel
        def composite_single(args):
            mockup, design_area = args
            result = self.composite_fast(
                mockup,
                design,
                design_area['x'],
                design_area['y'],
                design_area['width'],
                design_area['height'],
                design_area.get('rotation', 0),
                design_area.get('opacity', 1.0),
                center=options.get('centerDesign', False)
            )
            return self.image_to_bytes_fast(result, optimize=False)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(composite_single, zip(mockups, design_areas)))
        
        return results


def composite_image_fast(mockup_url: str, design_url: str, design_area: Dict, options: Dict = None) -> bytes:
    """
    Fast composite function - drop-in replacement for composite_image
    
    Args:
        mockup_url: URL of the mockup image
        design_url: URL of the design image
        design_area: Design area specification
        options: Optional settings
    
    Returns:
        Image bytes of the composited image
    """
    options = options or {}
    compositor = FastImageCompositor(max_workers=4)
    
    # Load images
    mockup = compositor.load_image_from_url(mockup_url)
    design = compositor.load_image_from_url(design_url)
    
    # Composite
    result = compositor.composite_fast(
        mockup,
        design,
        design_area['x'],
        design_area['y'],
        design_area['width'],
        design_area['height'],
        design_area.get('rotation', 0),
        design_area.get('opacity', 1.0),
        center=options.get('centerDesign', False)
    )
    
    # Convert to bytes (no optimization for speed)
    return compositor.image_to_bytes_fast(result, optimize=False)