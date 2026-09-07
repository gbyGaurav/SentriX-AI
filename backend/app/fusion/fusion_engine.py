from app.schemas.analysis import DetectorResult
from typing import List, Tuple

class FusionEngine:
    WEIGHTS = {
        'url_fraud': 1.0,
        'text_fraud': 0.95,
        'spam_fraud': 0.95,
        'qr_fraud': 0.85,
        'document_fraud': 0.9,
        'image_fraud': 0.8,
        'ai_media': 0.0,
        'video_fraud': 0.8,
        'audio_fraud': 0.7,
    }
    
    def fuse(self, results: List[DetectorResult]) -> Tuple[float, float]:
        if not results:
            return 0.0, 0.0

        # Authenticity check (ai_media) evaluates synthetic origin, NOT malicious security fraud.
        # Exclude ai_media from fraud threat calculations so innocent AI media is not penalized.
        fraud_results = [r for r in results if r.module != 'ai_media']
        
        if not fraud_results:
            # If only authenticity analysis ran, base security fraud risk is minimal (clean)
            return 0.05, 0.90
            
        if len(fraud_results) == 1:
            return fraud_results[0].fraud_probability, fraud_results[0].confidence
            
        total_weight = 0.0
        weighted_prob = 0.0
        weighted_conf = 0.0
        max_prob = 0.0
        
        for r in fraud_results:
            w = self.WEIGHTS.get(r.module, 0.5) * r.confidence
            weighted_prob += r.fraud_probability * w
            weighted_conf += r.confidence * w
            total_weight += w
            if r.fraud_probability > max_prob:
                max_prob = r.fraud_probability
            
        if total_weight == 0:
            return 0.0, 0.0
            
        avg_prob = weighted_prob / total_weight
        avg_conf = weighted_conf / total_weight

        # Prevent dilution when a specialized detector identifies a strong threat
        if max_prob >= 0.60:
            final_prob = max(avg_prob, max_prob * 0.92)
        else:
            final_prob = avg_prob

        return round(final_prob, 4), round(avg_conf, 4)

