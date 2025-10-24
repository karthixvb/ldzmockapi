"""
GPU-accelerated image compositing using PyTorch + CUDA 12
Note: This provides marginal speedup for simple compositing operations
Best used for batch processing or complex transformations
"""
import io
import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from PIL import Image
import requests
import numpy as np
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
import cv2

class GPUImageCompositor:
    """GPU-accelerated image compositor using PyTorch + CUDA"""
    
    def __init__(self, device: str = None, max_workers: int = 4):
        """
        Initialize GPU compositor
        
        Args:
            device: 'cuda' or 'cpu'. If None, auto-detect
            max_workers: Number of worker threads for I/O operations
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.max_workers = max_workers
        self.session = requests.Session()
        
        print(f"🚀 GPU Compositor initialized on: {self.device}")
        if self.device.type == 'cuda':
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
            print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    def load_image_from_url(self, url: str) -> Image.Image:
        """Load image from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return img.convert('RGBA')
        except Exception as e:
            raise Exception(f"Failed to load image from URL {url}: {str(e)}")
    
    def pil_to_tensor(self, img: Image.Image) -> torch.Tensor:
        """Convert PIL Image to PyTorch tensor on GPU"""
        # Convert to numpy array
        img_array = np.array(img)
        # Convert to tensor and move to GPU
        tensor = torch.from_numpy(img_array).float() / 255.0
        # Change from HWC to CHW format
        tensor = tensor.permute(2, 0, 1)
        return tensor.to(self.device)
    
    def tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """Convert PyTorch tensor to PIL Image"""
        # Move to CPU and convert to numpy
        tensor = tensor.cpu()
        # Change from CHW to HWC format
        tensor = tensor.permute(1, 2, 0)
        # Convert to uint8
        img_array = (tensor * 255).byte().numpy()
        return Image.fromarray(img_array, mode='RGBA')
    
    def resize_tensor(
        self, 
        tensor: torch.Tensor, 
        width: int, 
        height: int, 
        maintain_aspect: bool = True
    ) -> torch.Tensor:
        """
        Resize tensor using GPU-accelerated interpolation
        
        Args:
            tensor: Input tensor (C, H, W)
            width: Target width
            height: Target height
            maintain_aspect: Maintain aspect ratio
        
        Returns:
            Resized tensor
        """
        if not maintain_aspect:
            return TF.resize(tensor, [height, width], antialias=True)
        
        # Calculate aspect ratios
        _, h, w = tensor.shape
        img_aspect = w / h
        target_aspect = width / height
        
        # Fit image within bounds while maintaining aspect ratio
        if img_aspect > target_aspect:
            new_width = width
            new_height = int(width / img_aspect)
        else:
            new_height = height
            new_width = int(height * img_aspect)
        
        return TF.resize(tensor, [new_height, new_width], antialias=True)
    
    def rotate_tensor(self, tensor: torch.Tensor, angle: float) -> torch.Tensor:
        """Rotate tensor using GPU"""
        if angle == 0:
            return tensor
        return TF.rotate(tensor, angle, expand=True)
    
    def apply_opacity_tensor(self, tensor: torch.Tensor, opacity: float) -> torch.Tensor:
        """Apply opacity to tensor"""
        if opacity >= 1.0:
            return tensor
        
        # Multiply alpha channel by opacity
        tensor[3, :, :] *= opacity
        return tensor
    
    def composite_gpu(
        self,
        base_tensor: torch.Tensor,
        overlay_tensor: torch.Tensor,
        x: int,
        y: int,
        width: int,
        height: int,
        rotation: float = 0,
        opacity: float = 1.0,
        center: bool = False
    ) -> torch.Tensor:
        """
        Composite overlay onto base using GPU operations
        
        Args:
            base_tensor: Base image tensor (C, H, W)
            overlay_tensor: Overlay image tensor (C, H, W)
            x, y: Position
            width, height: Design area size
            rotation: Rotation angle
            opacity: Opacity value
            center: Center the design
        
        Returns:
            Composited tensor
        """
        # Resize overlay
        resized_overlay = self.resize_tensor(overlay_tensor, width, height, maintain_aspect=True)
        
        # Apply rotation
        if rotation != 0:
            resized_overlay = self.rotate_tensor(resized_overlay, rotation)
        
        # Apply opacity
        if opacity < 1.0:
            resized_overlay = self.apply_opacity_tensor(resized_overlay, opacity)
        
        # Calculate position
        _, overlay_h, overlay_w = resized_overlay.shape
        paste_x = x
        paste_y = y
        
        if center:
            paste_x = int(x + (width - overlay_w) / 2)
            paste_y = int(y + (height - overlay_h) / 2)
        
        # Create result tensor
        result = base_tensor.clone()
        
        # Ensure coordinates are within bounds
        _, base_h, base_w = base_tensor.shape
        paste_x = max(0, min(paste_x, base_w - overlay_w))
        paste_y = max(0, min(paste_y, base_h - overlay_h))
        
        # Alpha compositing
        alpha = resized_overlay[3:4, :, :]  # Alpha channel
        rgb_overlay = resized_overlay[:3, :, :]
        rgb_base = result[:3, paste_y:paste_y+overlay_h, paste_x:paste_x+overlay_w]
        
        # Blend: result = overlay * alpha + base * (1 - alpha)
        result[:3, paste_y:paste_y+overlay_h, paste_x:paste_x+overlay_w] = \
            rgb_overlay * alpha + rgb_base * (1 - alpha)
        
        # Update alpha channel
        result[3:4, paste_y:paste_y+overlay_h, paste_x:paste_x+overlay_w] = \
            torch.maximum(result[3:4, paste_y:paste_y+overlay_h, paste_x:paste_x+overlay_w], alpha)
        
        return result
    
    def composite_batch_gpu(
        self,
        mockup_urls: List[str],
        design_url: str,
        design_areas: List[Dict],
        options: Dict = None
    ) -> List[bytes]:
        """
        Batch composite using GPU
        
        Args:
            mockup_urls: List of mockup URLs
            design_url: Design URL
            design_areas: List of design areas
            options: Options dict
        
        Returns:
            List of composited image bytes
        """
        options = options or {}
        
        # Load design image once
        design_pil = self.load_image_from_url(design_url)
        design_tensor = self.pil_to_tensor(design_pil)
        
        # Load all mockups in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            mockup_pils = list(executor.map(self.load_image_from_url, mockup_urls))
        
        # Convert mockups to tensors
        mockup_tensors = [self.pil_to_tensor(img) for img in mockup_pils]
        
        # Composite all on GPU
        results = []
        for mockup_tensor, design_area in zip(mockup_tensors, design_areas):
            result_tensor = self.composite_gpu(
                mockup_tensor,
                design_tensor,
                int(design_area['x']),
                int(design_area['y']),
                int(design_area['width']),
                int(design_area['height']),
                design_area.get('rotation', 0),
                design_area.get('opacity', 1.0),
                center=options.get('centerDesign', False)
            )
            
            # Convert back to PIL and then to bytes
            result_pil = self.tensor_to_pil(result_tensor)
            img_bytes = io.BytesIO()
            result_pil.save(img_bytes, format='PNG', optimize=False)
            img_bytes.seek(0)
            results.append(img_bytes.getvalue())
        
        return results


def composite_image_gpu(mockup_url: str, design_url: str, design_area: Dict, options: Dict = None) -> bytes:
    """
    GPU-accelerated composite function
    
    Args:
        mockup_url: Mockup image URL
        design_url: Design image URL
        design_area: Design area specification
        options: Options dict
    
    Returns:
        Composited image bytes
    """
    options = options or {}
    compositor = GPUImageCompositor()
    
    # Load images
    mockup_pil = compositor.load_image_from_url(mockup_url)
    design_pil = compositor.load_image_from_url(design_url)
    
    # Convert to tensors
    mockup_tensor = compositor.pil_to_tensor(mockup_pil)
    design_tensor = compositor.pil_to_tensor(design_pil)
    
    # Composite on GPU
    result_tensor = compositor.composite_gpu(
        mockup_tensor,
        design_tensor,
        int(design_area['x']),
        int(design_area['y']),
        int(design_area['width']),
        int(design_area['height']),
        design_area.get('rotation', 0),
        design_area.get('opacity', 1.0),
        center=options.get('centerDesign', False)
    )
    
    # Convert back to PIL
    result_pil = compositor.tensor_to_pil(result_tensor)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    result_pil.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()