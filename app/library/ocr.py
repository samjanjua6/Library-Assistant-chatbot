import os
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global instances so they are loaded into memory once on startup
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR engine (CPU)...")
            # lang='en' downloads english models. 
            # use_angle_cls=True is good for rotated book covers or receipts.
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise e
    return _ocr_engine

def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Takes raw image bytes, saves to a temporary file,
    runs PaddleOCR to extract text, and returns a single concatenated string.
    """
    engine = get_ocr_engine()
    
    # PaddleOCR requires a file path (or numpy array).
    # Writing to a secure temporary file is the easiest way.
    fd, temp_path = tempfile.mkstemp(suffix=".png")
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(file_bytes)
        
        # Run inference
        result = engine.ocr(temp_path, cls=True)
        
        if not result or result[0] is None:
            return ""
        
        extracted_lines = []
        for line in result[0]:
            # line structure: [[box_coords], (text, confidence)]
            text = line[1][0]
            extracted_lines.append(text)
            
        return "\n".join(extracted_lines)
    except Exception as e:
        logger.error(f"Error during OCR extraction: {e}")
        return f"[OCR Failed: {str(e)}]"
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
