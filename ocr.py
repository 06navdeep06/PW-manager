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
            
            # Try multiple OCR configurations for better text extraction
            configs = [
                '--oem 3 --psm 6',  # Uniform block of text (default)
                '--oem 3 --psm 3',  # Fully automatic page segmentation
                '--oem 3 --psm 4',  # Single column of text
                '--oem 3 --psm 7',  # Single text line
                '--oem 3 --psm 8',  # Single word
                '--oem 3 --psm 11', # Sparse text
                '--oem 3 --psm 12', # Sparse text with OSD
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config in configs:
                try:
                    # Extract text with current configuration
                    text = pytesseract.image_to_string(image, config=config)
                    
                    if text and text.strip():
                        # Try to get confidence score if possible
                        try:
                            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                            
                            # Choose text with highest confidence and reasonable length
                            if (avg_confidence > best_confidence and len(text.strip()) > len(best_text.strip())) or (not best_text and text.strip()):
                                best_text = text
                                best_confidence = avg_confidence
                        except:
                            # If confidence calculation fails, just use text length as metric
                            if len(text.strip()) > len(best_text.strip()):
                                best_text = text
                                
                except Exception as e:
                    logger.debug(f"OCR config {config} failed: {e}")
                    continue
            
            # Clean up the extracted text
            if best_text:
                # Remove excessive whitespace and clean up formatting
                lines = [line.strip() for line in best_text.split('\n') if line.strip()]
                best_text = '\n'.join(lines)
                
                # Remove common OCR artifacts
                best_text = best_text.replace('|', 'I').replace('0', 'O').replace('5', 'S')
                
            return best_text
            
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
