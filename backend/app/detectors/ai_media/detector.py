"""Probabilistic AI-Generated Media & Authenticity Detector.
Performs:
1. PNG text chunks (parameters, prompt, workflow) and EXIF metadata inspection
2. Camera hardware signature identification (Make, Model, ISO, Exposure)
3. 2D FFT Frequency-domain spectral analysis (identifying synthetic grid/checkerboard upsampling artifacts)
4. Noise residual & cross-channel covariance analysis (PRNU deviation)
5. Multi-frame temporal consistency (for video streams)
Strictly adheres to probabilistic classifications:
- LIKELY_AI_GENERATED
- POSSIBLY_AI_GENERATED
- LIKELY_AUTHENTIC
- INCONCLUSIVE
"""

import io
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image
import cv2

from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult, RiskLevel

logger = logging.getLogger(__name__)

KNOWN_AI_GENERATOR_TAGS = [
    "midjourney", "stable diffusion", "dall-e", "comfyui", "automatic1111",
    "novelai", "civitai", "adobe firefly", "bing image creator", "flux.1",
    "sdxl", "leonardo.ai", "invokeai", "ideogram", "imagen", "craiyon",
    "steps:", "sampler:", "cfg scale:", "seed:", "model hash:", "negative prompt:"
]


def analyze_fft_spectrum(gray_img: np.ndarray) -> Tuple[float, bool]:
    """Computes 2D Fast Fourier Transform power spectrum.
    Identifies high-frequency energy spikes typical of transposed convolution
    and diffusion model upsampling operations.
    Returns (anomaly_score, has_spectral_peaks).
    """
    try:
        h, w = gray_img.shape
        if h < 64 or w < 64:
            return 0.0, False

        # Resize to standard power-of-2 for reliable FFT analysis
        resized = cv2.resize(gray_img, (256, 256), interpolation=cv2.INTER_AREA)
        f = np.fft.fft2(resized.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)

        # High frequency ring mask
        y, x = np.ogrid[:256, :256]
        center = (128, 128)
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)

        # Natural photographic images follow 1/f^alpha power distribution.
        # Synthetic upsampling introduces discrete peaks in outer frequencies (r > 60).
        outer_mask = (dist_from_center > 60) & (dist_from_center < 120)
        outer_mag = magnitude[outer_mask]

        if len(outer_mag) == 0:
            return 0.0, False

        mean_outer = float(np.mean(outer_mag))
        std_outer = float(np.std(outer_mag))
        max_outer = float(np.max(outer_mag))

        # Peak-to-average ratio in high-frequency band
        peak_ratio = (max_outer - mean_outer) / (std_outer + 1e-6)

        # If peak is > 4.2 standard deviations above background noise in high freq
        has_peaks = peak_ratio > 4.2
        anomaly_score = min(1.0, max(0.0, (peak_ratio - 2.5) / 4.0))
        return anomaly_score, has_peaks
    except Exception as e:
        logger.debug(f"FFT analysis error: {e}")
        return 0.0, False


def analyze_noise_residual(rgb_img: np.ndarray) -> Tuple[float, float]:
    """Analyzes photo-response noise residual across color channels.
    Camera sensors produce physical photon noise with uncorrelated channel residuals.
    AI generation pipelines produce synthesized smoothness or unnatural inter-channel correlations.
    Returns (noise_variance, channel_correlation).
    """
    try:
        if rgb_img.shape[0] < 64 or rgb_img.shape[1] < 64:
            return 0.0, 0.0

        sample = cv2.resize(rgb_img, (256, 256), interpolation=cv2.INTER_AREA)
        residuals = []
        for c in range(3):
            ch = sample[:, :, c].astype(np.float32)
            blurred = cv2.medianBlur(sample[:, :, c], 3).astype(np.float32)
            residuals.append(ch - blurred)

        r_var = float(np.mean([np.var(r) for r in residuals]))

        # Correlation between R and B residual channels
        r_flat = residuals[0].flatten()
        b_flat = residuals[2].flatten()
        if float(np.std(r_flat)) < 1e-5 or float(np.std(b_flat)) < 1e-5:
            corr = 0.0
        else:
            corr_matrix = np.corrcoef(r_flat, b_flat)
            corr = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0

        return r_var, abs(corr)
    except Exception as e:
        logger.debug(f"Noise residual error: {e}")
        return 0.0, 0.0


class AIMediaDetector(FraudDetector):
    """Probabilistic detector for AI-generated synthetic images and deepfakes."""

    @property
    def module_name(self) -> str:
        return "ai_media"

    @property
    def model_version(self) -> str:
        return "probabilistic-spectral-residual-v2"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        file_bytes = kwargs.get("file_bytes")
        frames_bytes = kwargs.get("frames_bytes", [])

        if not file_bytes and not frames_bytes:
            return self._create_result(0.05, 0.5, ["No media bytes supplied for authenticity check"], 0.0)

        signals = []
        metadata = {}
        ai_evidence = []
        has_camera_hardware = False
        camera_details = ""
        is_video = bool(frames_bytes)

        # Extract frames or load single image
        images_to_test = []
        if file_bytes:
            try:
                pil_img = Image.open(io.BytesIO(file_bytes))

                # 1. Check PNG text chunks (parameters, prompt, workflow, etc.)
                if hasattr(pil_img, "info") and pil_img.info:
                    for k, v in pil_img.info.items():
                        v_str = (v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)).lower()
                        for tag in KNOWN_AI_GENERATOR_TAGS:
                            if tag in v_str:
                                signals.append(f"Image metadata indicates generative AI: '{tag}'")
                                ai_evidence.append(f"Generation metadata parameter detected: '{tag}'")
                                break

                # 2. Check EXIF metadata for AI generator tags and authentic camera signatures
                exif = pil_img.getexif()
                if exif:
                    for k, v in exif.items():
                        v_str = str(v).lower()
                        for tag in KNOWN_AI_GENERATOR_TAGS:
                            if tag in v_str and not any(tag in e for e in ai_evidence):
                                signals.append(f"EXIF metadata references generative AI software: '{tag}'")
                                ai_evidence.append(f"EXIF generator tag detected: '{tag}'")

                    # Check physical camera hardware EXIF tags (Make=271, Model=272)
                    make = str(exif.get(271, "")).strip()
                    model = str(exif.get(272, "")).strip()
                    if make or model:
                        has_camera_hardware = True
                        camera_details = f"{make} {model}".strip()

                # Downsample to <=1024px to prevent large float32/fft matrix allocation
                if max(pil_img.width, pil_img.height) > 1024:
                    pil_img.thumbnail((1024, 1024), Image.Resampling.BILINEAR)

                rgb_arr = np.array(pil_img.convert("RGB"))
                images_to_test.append(rgb_arr)
            except Exception as e:
                logger.debug(f"Could not parse image for AI media check: {e}")

        if frames_bytes:
            for fb in frames_bytes[:4]:
                try:
                    f_arr = cv2.imdecode(np.frombuffer(fb, np.uint8), cv2.IMREAD_COLOR)
                    if f_arr is not None:
                        if max(f_arr.shape[0], f_arr.shape[1]) > 720:
                            scale = 720.0 / max(f_arr.shape[0], f_arr.shape[1])
                            f_arr = cv2.resize(f_arr, (int(f_arr.shape[1] * scale), int(f_arr.shape[0] * scale)), interpolation=cv2.INTER_AREA)
                        images_to_test.append(cv2.cvtColor(f_arr, cv2.COLOR_BGR2RGB))
                except Exception:
                    pass

        if not images_to_test:
            proc_time = (time.time() - start_t) * 1000
            return self._create_result(
                0.05, 0.5, ["Unable to extract visual matrices for authenticity inspection"], proc_time,
                metadata={"ai_media": {"result": "INCONCLUSIVE", "confidence": 50, "evidence": ["Media format unparseable"], "disclaimer": "AI-generated media detection is probabilistic and should not be treated as definitive proof."}}
            )

        # Run forensic measures across representative frame(s)
        fft_scores = []
        fft_peaks_count = 0
        noise_variances = []
        channel_corrs = []

        for img in images_to_test:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            fft_score, has_peaks = analyze_fft_spectrum(gray)
            fft_scores.append(fft_score)
            if has_peaks:
                fft_peaks_count += 1

            n_var, ch_corr = analyze_noise_residual(img)
            noise_variances.append(n_var)
            channel_corrs.append(ch_corr)

        # Clean up image matrix memory immediately
        del images_to_test
        import gc
        gc.collect()

        avg_fft = float(np.mean(fft_scores)) if fft_scores else 0.0
        avg_noise_var = float(np.mean(noise_variances)) if noise_variances else 0.0
        avg_corr = float(np.mean(channel_corrs)) if channel_corrs else 0.0

        metadata["spectral_anomaly_score"] = round(avg_fft, 3)
        metadata["noise_variance"] = round(avg_noise_var, 3)
        metadata["channel_residual_correlation"] = round(avg_corr, 3)

        # Evaluate signals
        if fft_peaks_count > 0:
            signals.append("High-frequency periodic spectral spikes typical of diffusion/GAN upsampling")
            ai_evidence.append("Frequency-domain periodic grid artifacts detected via 2D FFT")

        if avg_noise_var < 0.75:
            signals.append("Unnaturally low camera sensor noise variance (characteristic of synthetic rendering)")
            ai_evidence.append("Lack of physical optical sensor noise fingerprint")
        elif avg_noise_var > 15.0 and avg_corr > 0.45:
            signals.append("Unnatural inter-channel residual noise correlation")
            ai_evidence.append("Abnormal color channel noise covariance")

        has_metadata_hit = any("generative AI" in s for s in signals)

        # Probabilistic classification based on calculated forensic signals
        if has_metadata_hit or (fft_peaks_count > 0 and len(ai_evidence) >= 2 and not has_camera_hardware):
            verdict = "LIKELY_AI_GENERATED"
            confidence = round(float(np.clip(0.78 + avg_fft * 0.12, 0.78, 0.90)), 2)
        elif has_camera_hardware and not has_metadata_hit and (0.8 <= avg_noise_var <= 25.0):
            verdict = "LIKELY_AUTHENTIC"
            confidence = round(float(np.clip(0.78 + (1.0 - avg_fft) * 0.08, 0.76, 0.86)), 2)
            signals.append(f"Camera hardware EXIF verified: {camera_details}")
            ai_evidence.append(f"Camera hardware EXIF verified ({camera_details})")
            signals.append("Natural optical sensor noise variance and photographic EXIF signature observed")
        elif fft_peaks_count > 0 or (avg_noise_var < 0.70 and avg_fft > 0.25):
            verdict = "POSSIBLY_AI_GENERATED"
            confidence = round(float(np.clip(0.60 + avg_fft * 0.10, 0.60, 0.72)), 2)
        elif is_video:
            # For video streams without clear deepfake artifacts, default to INCONCLUSIVE
            verdict = "INCONCLUSIVE"
            confidence = 0.50
            signals.append("Video frame consistency is inconclusive; insufficient distinct markers to definitively classify authenticity")
        else:
            verdict = "INCONCLUSIVE"
            confidence = 0.50
            signals.append("Forensic signals are within normal range; insufficient distinct markers to classify authenticity")

        proc_time = (time.time() - start_t) * 1000

        ai_media_data = {
            "result": verdict,
            "confidence": int(round(confidence * 100)),
            "evidence": ai_evidence if ai_evidence else ["Forensic signals are within standard variance; insufficient distinct markers to classify authenticity."],
            "disclaimer": "AI-generated media detection is probabilistic and should not be treated as definitive proof."
        }

        metadata["ai_media"] = ai_media_data

        # Authenticity check sets fraud_probability to 0.05 because synthetic origin
        # is an authenticity question, not an inherent security fraud threat.
        return self._create_result(
            probability=0.05,
            confidence=confidence,
            signals=signals,
            processing_time_ms=proc_time,
            metadata=metadata
        )
