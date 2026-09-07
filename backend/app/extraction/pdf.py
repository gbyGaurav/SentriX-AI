"""PDF extraction module using PyMuPDF (fitz).
Extracts text, embedded links/URLs, metadata, and embedded images.
"""

import io
import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

URL_REGEX = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[a-zA-Z]{2,}'


def extract_pdf_data(pdf_bytes: bytes) -> Dict[str, Any]:
    """Extract text, URLs, metadata, and image bytes from PDF."""
    results = {
        "text": "",
        "urls": [],
        "metadata": {},
        "page_count": 0,
        "has_images": False,
        "image_bytes_list": [],
        "suspicious_indicators": [],
    }

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        results["page_count"] = len(doc)
        results["metadata"] = {k: v for k, v in doc.metadata.items() if v}

        all_text = []
        extracted_urls = set()

        for page_num in range(len(doc)):
            page = doc[page_num]
            # 1. Text extraction
            page_text = page.get_text()
            if page_text:
                all_text.append(page_text)
                # Find plain text URLs
                for u in re.findall(URL_REGEX, page_text):
                    extracted_urls.add(u.rstrip('.,;)'))

            # 2. Extract clickable links / URIs
            links = page.get_links()
            for link in links:
                uri = link.get("uri")
                if uri:
                    extracted_urls.add(uri.rstrip('.,;)'))

            # 3. Extract embedded images (first few for analysis)
            image_list = page.get_images(full=True)
            if image_list:
                results["has_images"] = True
                for img_info in image_list[:3]:  # sample up to 3 images
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    if base_image and "image" in base_image:
                        results["image_bytes_list"].append(base_image["image"])

        results["text"] = "\n".join(all_text)
        results["urls"] = list(extracted_urls)

        # Basic metadata checks
        meta = results["metadata"]
        producer = (meta.get("producer") or "").lower()
        creator = (meta.get("creator") or "").lower()
        if not producer and not creator:
            results["suspicious_indicators"].append("PDF contains stripped or missing producer/creator metadata")

    except Exception as e:
        logger.error(f"Error extracting PDF data: {e}", exc_info=True)
        results["error"] = str(e)

    return results
