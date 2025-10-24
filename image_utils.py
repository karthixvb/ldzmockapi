import io
from PIL import Image
import requests
from typing import List, Dict, Tuple
import math

class ImageCompositor:
    """Handles image compositing operations for mockups"""
    
    @staticmethod
    def load_image_from_url(url: str) -> Image.Image:
        """Load image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return img.convert('RGBA')
        except Exception as e:
            raise Exception(f"Failed to load image from URL {url}: {str(e)}")
    
    @staticmethod
    def load_image_from_file(file_path: str) -> Image.Image:
        """Load image from file path"""
        try:
            img = Image.open(file_path)
            return img.convert('RGBA')
        except Exception as e:
            raise Exception(f"Failed to load image from file {file_path}: {str(e)}")
    
    @staticmethod
    def resize_image(image: Image.Image, width: int, height: int, maintain_aspect: bool = True) -> Image.Image:
        """
        Resize image to fit within specified dimensions
        
        Args:
            image: Image to resize
            width: Target width
            height: Target height
            maintain_aspect: If True, maintain aspect ratio and fit within bounds
        
        Returns:
            Resized image
        """
        if not maintain_aspect:
            return image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        
        # Calculate aspect ratios
        img_aspect = image.width / image.height
        target_aspect = width / height
        
        # Fit image within bounds while maintaining aspect ratio
        if img_aspect > target_aspect:
            # Image is wider - fit to width
            new_width = int(width)
            new_height = int(width / img_aspect)
        else:
            # Image is taller - fit to height
            new_height = int(height)
            new_width = int(height * img_aspect)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def rotate_image(image: Image.Image, angle: float) -> Image.Image:
        """Rotate image by specified angle (in degrees)"""
        if angle == 0:
            return image
        return image.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    
    @staticmethod
    def apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
        """Apply opacity to image (0.0 to 1.0)"""
        if opacity >= 1.0:
            return image
        
        alpha = image.split()[-1]
        alpha = alpha.point(lambda p: int(p * opacity))
        image.putalpha(alpha)
        return image
    
    @staticmethod
    def composite_images(
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
        Composite overlay image onto base image at specified position
        
        Args:
            base_image: Base/background image
            overlay_image: Image to overlay
            x: X position (top-left of design area)
            y: Y position (top-left of design area)
            width: Width of design area
            height: Height of design area
            rotation: Rotation angle in degrees
            opacity: Opacity value (0.0 to 1.0)
            center: If True, center the design within the area
        
        Returns:
            Composited image
        """
        # Resize overlay to fit within the design area while maintaining aspect ratio
        resized_overlay = ImageCompositor.resize_image(overlay_image, width, height, maintain_aspect=True)
        
        # Apply rotation
        if rotation != 0:
            resized_overlay = ImageCompositor.rotate_image(resized_overlay, rotation)
        
        # Apply opacity
        if opacity < 1.0:
            resized_overlay = ImageCompositor.apply_opacity(resized_overlay, opacity)
        
        # Create a new image for compositing
        result = base_image.copy()
        
        # Calculate position
        paste_x = int(x)
        paste_y = int(y)
        
        # Center the design within the area if requested
        if center:
            paste_x = int(x + (width - resized_overlay.width) / 2)
            paste_y = int(y + (height - resized_overlay.height) / 2)
        
        # Paste the overlay
        if resized_overlay.mode == 'RGBA':
            result.paste(resized_overlay, (paste_x, paste_y), resized_overlay)
        else:
            result.paste(resized_overlay, (paste_x, paste_y))
        
        return result
    
    @staticmethod
    def composite_multiple(
        base_image: Image.Image,
        overlays: List[Dict]
    ) -> Image.Image:
        """
        Composite multiple overlay images onto base image
        
        Args:
            base_image: Base/background image
            overlays: List of overlay specifications with keys:
                - image: PIL Image object
                - x: X position
                - y: Y position
                - width: Width
                - height: Height
                - rotation: Rotation angle (optional)
                - opacity: Opacity (optional)
        
        Returns:
            Composited image
        """
        result = base_image.copy()
        
        for overlay in overlays:
            result = ImageCompositor.composite_images(
                result,
                overlay['image'],
                overlay['x'],
                overlay['y'],
                overlay['width'],
                overlay['height'],
                overlay.get('rotation', 0),
                overlay.get('opacity', 1.0)
            )
        
        return result
    
    @staticmethod
    def save_image(image: Image.Image, file_path: str, format: str = 'PNG') -> str:
        """Save image to file"""
        try:
            image.save(file_path, format=format)
            return file_path
        except Exception as e:
            raise Exception(f"Failed to save image to {file_path}: {str(e)}")
    
    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
        """Convert image to bytes"""
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format)
            img_byte_arr.seek(0)
            return img_byte_arr.getvalue()
        except Exception as e:
            raise Exception(f"Failed to convert image to bytes: {str(e)}")
    
    @staticmethod
    def center_design(
        base_image: Image.Image,
        design_image: Image.Image,
        design_area: Dict
    ) -> Dict:
        """
        Calculate centered position for design within design area
        
        Args:
            base_image: Base image
            design_image: Design image
            design_area: Design area specification
        
        Returns:
            Updated design area with centered position
        """
        design_width = design_area['width']
        design_height = design_area['height']
        
        # Calculate centered position
        centered_x = design_area['x'] + (design_width - design_image.width) / 2
        centered_y = design_area['y'] + (design_height - design_image.height) / 2
        
        return {
            'x': centered_x,
            'y': centered_y,
            'width': design_image.width,
            'height': design_image.height,
            'rotation': design_area.get('rotation', 0),
            'opacity': design_area.get('opacity', 1.0)
        }

def composite_image(mockup_url: str, design_url: str, design_area: Dict, options: Dict = None) -> bytes:
    """
    Composite a design image onto a mockup
    
    Args:
        mockup_url: URL of the mockup image
        design_url: URL of the design image
        design_area: Design area specification with x, y, width, height, rotation, opacity
        options: Optional settings (centerDesign, etc.)
    
    Returns:
        Image bytes of the composited image
    """
    options = options or {}
    compositor = ImageCompositor()
    
    # Load images
    mockup = compositor.load_image_from_url(mockup_url)
    design = compositor.load_image_from_url(design_url)
    
    # Composite the images with centering option
    result = compositor.composite_images(
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
    
    # Convert to bytes
    return compositor.image_to_bytes(result)
