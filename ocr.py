"""
OCR (Optical Character Recognition) Module
Handles text extraction from images using pytesseract.
"""

import asyncio
import logging
from typing import Optional
import io
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

class ImageOCR:
    """Handles OCR processing of images."""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the OCR processor.
        
        Args:
            tesseract_path: Path to tesseract executable (Windows only)
        """
        self.tesseract_path = tesseract_path
        
        # Set tesseract path if provided (mainly for Windows)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    async def extract_text(self, image_data: bytes) -> Optional[str]:
        """
        Extract text from image data using OCR.
        
        Args:
            image_data: Raw image data as bytes
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Run OCR in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                self._process_image_sync, 
                image_data
            )
            
            if text and text.strip():
                logger.info(f"OCR extracted {len(text)} characters")
                return text.strip()
            else:
                logger.warning("OCR returned empty text")
                return None
                
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return None
    
    def _process_image_sync(self, image_data: bytes) -> str:
        """
        Synchronous image processing for OCR.
        This runs in a thread pool to avoid blocking the event loop.
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR with optimized settings
            # Use different PSM modes for better accuracy
            config = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
            
            # Try with default config first
            text = pytesseract.image_to_string(image, config=config)
            
            # If no text found, try with different PSM mode
            if not text.strip():
                config = '--oem 3 --psm 3'  # Fully automatic page segmentation
                text = pytesseract.image_to_string(image, config=config)
            
            # If still no text, try with different PSM mode for single text line
            if not text.strip():
                config = '--oem 3 --psm 7'  # Single text line
                text = pytesseract.image_to_string(image, config=config)
            
            return text
            
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract OCR not found. Please install Tesseract OCR.")
            return ""
        except Exception as e:
            logger.error(f"Error in synchronous OCR processing: {e}")
            return ""
    
    async def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """
        Extract text from an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            return await self.extract_text(image_data)
        except Exception as e:
            logger.error(f"Error reading image file {file_path}: {e}")
            return None
    
    def get_supported_formats(self) -> list:
        """
        Get list of supported image formats.
        
        Returns:
            List of supported file extensions
        """
        return ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
    
    def is_supported_format(self, filename: str) -> bool:
        """
        Check if a file format is supported for OCR.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if format is supported, False otherwise
        """
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.get_supported_formats())
    
    async def get_image_info(self, image_data: bytes) -> dict:
        """
        Get basic information about an image.
        
        Args:
            image_data: Raw image data as bytes
            
        Returns:
            Dictionary with image information
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height
            }
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}
