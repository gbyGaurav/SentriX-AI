"""Document Fraud Detector.
Analyzes PDFs, DOCX, and TXT files for structural anomalies, suspicious metadata,
phishing URLs, and cascades extracted text and links into specialized detectors.
"""

import time
import re
from typing import Optional, Dict, Any, List
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult
from app.extraction.pdf import extract_pdf_data
from app.extraction.document import extract_docx_data
from app.extraction.ocr import extract_text_with_ocr


class DocumentDetector(FraudDetector):
    @property
    def module_name(self) -> str:
        return "document_fraud"

    @property
    def model_version(self) -> str:
        return "document-analyzer-v1"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        file_bytes = kwargs.get("file_bytes")
        filename = kwargs.get("filename", "").lower()

        if not file_bytes:
            return self._create_result(
                probability=0.0,
                confidence=1.0,
                signals=[],
                processing_time_ms=0.0,
                error="No document content provided"
            )

        extracted_text = ""
        extracted_urls = []
        metadata = {}
        suspicious_indicators = []
        score = 0.0

        # 1. Parse by format
        if filename.endswith(".pdf") or file_bytes.startswith(b"%PDF"):
            pdf_data = extract_pdf_data(file_bytes)
            extracted_text = pdf_data.get("text", "")
            extracted_urls = pdf_data.get("urls", [])
            metadata = pdf_data.get("metadata", {})
            suspicious_indicators.extend(pdf_data.get("suspicious_indicators", []))

            # Fallback OCR if scanned PDF (no selectable text but has images)
            if not extracted_text.strip() and pdf_data.get("image_bytes_list"):
                suspicious_indicators.append("Scanned PDF with no digital text stream; performing visual OCR inspection")
                for img_bytes in pdf_data["image_bytes_list"]:
                    ocr_text = extract_text_with_ocr(img_bytes)
                    if ocr_text:
                        extracted_text += "\n" + ocr_text

        elif filename.endswith(".docx") or file_bytes[:4] == b"PK\x03\x04":
            docx_data = extract_docx_data(file_bytes)
            extracted_text = docx_data.get("text", "")
            extracted_urls = docx_data.get("urls", [])
            metadata = docx_data.get("metadata", {})

        else:
            # Plain text fallback
            try:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                extracted_text = ""

        # 2. Structural & metadata anomaly evaluation
        signals = []
        signals.extend(suspicious_indicators)
        if suspicious_indicators:
            score += 0.2

        meta_author = (metadata.get("author") or "").lower()
        meta_creator = (metadata.get("creator") or "").lower()

        # Check for spoofed corporate or invoice titles with generic creators
        text_lower = extracted_text.lower()
        if any(w in text_lower for w in ["invoice", "payment receipt", "wire instructions", "billing statement"]):
            if not meta_author and not meta_creator:
                score += 0.25
                signals.append("Financial document lacks institutional author/creator signatures")

        # Urgency / payment pressure in document
        if any(w in text_lower for w in ["immediate payment required", "overdue notice", "remit funds immediately", "wire transfer instructions"]):
            score += 0.2
            signals.append("High-pressure payment demands detected in document body")

        # Sensitive account / credential queries
        if any(w in text_lower for w in ["ssn", "social security", "bank account number", "routing number", "pin", "password"]):
            score += 0.2
            signals.append("Document explicitly requests confidential personal/banking details")

        # Links embedded in document
        if len(extracted_urls) > 0:
            score += min(0.2, 0.05 * len(extracted_urls))
            signals.append(f"Document embeds {len(extracted_urls)} hyperlinks for external navigation")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000

        return self._create_result(
            probability=final_score,
            confidence=0.82,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "extracted_text": extracted_text[:1000] if extracted_text else "",
                "extracted_urls": extracted_urls,
                "metadata": metadata,
                "document_length": len(extracted_text),
            }
        )
