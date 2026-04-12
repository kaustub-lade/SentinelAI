import json
import re
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression


FEATURE_NAMES = [
    "text_length",
    "url_count",
    "url_length",
    "url_dot_count",
    "url_has_at",
    "url_has_ip",
    "suspicious_keyword_count",
    "urgency_keyword_count",
    "sender_domain_suspicious",
    "subject_urgency",
    "exclamation_count",
    "digit_ratio",
]

SUSPICIOUS_KEYWORDS = [
    "verify",
    "suspended",
    "urgent",
    "login",
    "reset",
    "payment",
    "invoice",
    "security",
    "bank",
    "click",
]

URGENCY_KEYWORDS = ["urgent", "immediately", "asap", "now", "action required", "final notice"]

SUSPICIOUS_DOMAINS = ["paypa1", "amaz0n", "micros0ft", "goog1e", "secure-verify", "login-check"]


class PhishingModelService:
    def __init__(self) -> None:
        model_path = Path(__file__).resolve().parent.parent / "ml" / "phishing_model.joblib"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_path = model_path
        self.model: LogisticRegression | None = None

    def ensure_model(self) -> None:
        if self.model is not None:
            return
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
            return
        self.train_and_save(samples=2500)

    def train_and_save(self, samples: int = 2500) -> dict[str, Any]:
        rng = np.random.default_rng(42)
        X = []
        y = []

        for _ in range(samples):
            text_length = float(rng.uniform(0.02, 1.0))
            url_count = float(rng.uniform(0.0, 1.0))
            url_length = float(rng.uniform(0.0, 1.0)) if url_count > 0 else 0.0
            url_dot_count = float(rng.uniform(0.0, 1.0)) if url_count > 0 else 0.0
            url_has_at = int(rng.integers(0, 2)) if url_count > 0 else 0
            url_has_ip = int(rng.integers(0, 2)) if url_count > 0 else 0
            suspicious_keyword_count = float(rng.uniform(0.0, 1.0))
            urgency_keyword_count = float(rng.uniform(0.0, 1.0))
            sender_domain_suspicious = int(rng.integers(0, 2))
            subject_urgency = int(rng.integers(0, 2))
            exclamation_count = float(rng.uniform(0.0, 1.0))
            digit_ratio = float(rng.uniform(0.0, 0.5))

            feature_row = [
                text_length,
                url_count,
                url_length,
                url_dot_count,
                url_has_at,
                url_has_ip,
                suspicious_keyword_count,
                urgency_keyword_count,
                sender_domain_suspicious,
                subject_urgency,
                exclamation_count,
                digit_ratio,
            ]
            X.append(feature_row)

            risk_score = (
                0.20 * min(url_count, 1)
                + 0.18 * min(suspicious_keyword_count, 1)
                + 0.18 * min(urgency_keyword_count, 1)
                + 0.14 * sender_domain_suspicious
                + 0.10 * subject_urgency
                + 0.08 * url_has_ip
                + 0.06 * url_has_at
                + 0.06 * min(exclamation_count, 1)
                + 0.05 * min(digit_ratio / 0.4, 1)
            )

            noise = float(rng.normal(0, 0.08))
            y.append(1 if risk_score + noise >= 0.52 else 0)

        model = LogisticRegression(max_iter=3000, class_weight="balanced")
        model.fit(np.array(X), np.array(y))

        joblib.dump(model, self.model_path)
        self.model = model

        return {
            "samples": samples,
            "model_path": str(self.model_path),
            "status": "trained",
        }

    def analyze(
        self,
        email_content: str | None,
        sender_email: str | None,
        subject: str | None,
        url: str | None = None,
    ) -> dict[str, Any]:
        self.ensure_model()
        assert self.model is not None

        features = self._extract_features(email_content=email_content, sender_email=sender_email, subject=subject, url=url)
        vector = np.array([features[name] for name in FEATURE_NAMES], dtype=float).reshape(1, -1)
        phishing_probability = float(self.model.predict_proba(vector)[0][1])

        confidence = round(phishing_probability, 3)
        is_phishing = phishing_probability >= 0.5
        risk_level = self._risk_level(confidence)
        detected_indicators = self._indicators(features)
        recommendations = self._recommendations(is_phishing)

        analysis = {
            "model": "logistic_regression",
            "model_version": "v1",
            "features": features,
            "top_factors": self._top_factors(vector[0]),
        }

        return {
            "is_phishing": is_phishing,
            "confidence": confidence,
            "risk_level": risk_level,
            "detected_indicators": detected_indicators,
            "recommendations": recommendations,
            "analysis": analysis,
        }

    def _extract_features(
        self,
        email_content: str | None,
        sender_email: str | None,
        subject: str | None,
        url: str | None,
    ) -> dict[str, float]:
        text = (email_content or "").strip()
        subject_text = (subject or "").strip().lower()
        sender = (sender_email or "").lower()

        urls = []
        if url:
            urls.append(url)
        urls.extend(re.findall(r"https?://[^\s)\]>]+", text))

        combined_url = urls[0] if urls else ""
        lower_text = text.lower()

        suspicious_keyword_count = sum(lower_text.count(keyword) for keyword in SUSPICIOUS_KEYWORDS)
        urgency_keyword_count = sum(lower_text.count(keyword) for keyword in URGENCY_KEYWORDS)
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        sender_domain_suspicious = 1 if any(k in sender_domain for k in SUSPICIOUS_DOMAINS) else 0

        digit_count = sum(ch.isdigit() for ch in text)
        digit_ratio = (digit_count / len(text)) if text else 0.0

        return {
            "text_length": float(round(min(len(text) / 2000.0, 1.0), 4)),
            "url_count": float(round(min(len(urls) / 8.0, 1.0), 4)),
            "url_length": float(round(min(len(combined_url) / 140.0, 1.0), 4)),
            "url_dot_count": float(round(min(combined_url.count(".") / 8.0, 1.0), 4)),
            "url_has_at": float("@" in combined_url),
            "url_has_ip": float(bool(re.search(r"https?://\d+\.\d+\.\d+\.\d+", combined_url))),
            "suspicious_keyword_count": float(round(min(suspicious_keyword_count / 10.0, 1.0), 4)),
            "urgency_keyword_count": float(round(min(urgency_keyword_count / 6.0, 1.0), 4)),
            "sender_domain_suspicious": float(sender_domain_suspicious),
            "subject_urgency": float(any(k in subject_text for k in URGENCY_KEYWORDS)),
            "exclamation_count": float(round(min(text.count("!") / 10.0, 1.0), 4)),
            "digit_ratio": float(round(digit_ratio, 4)),
        }

    def _top_factors(self, vector: np.ndarray) -> list[dict[str, Any]]:
        assert self.model is not None
        coefs = self.model.coef_[0]
        contributions = []
        for i, name in enumerate(FEATURE_NAMES):
            contributions.append(
                {
                    "feature": name,
                    "value": float(vector[i]),
                    "weight": float(coefs[i]),
                    "impact": float(vector[i] * coefs[i]),
                }
            )
        contributions.sort(key=lambda item: abs(item["impact"]), reverse=True)
        return contributions[:5]

    @staticmethod
    def _risk_level(confidence: float) -> str:
        if confidence >= 0.85:
            return "Critical"
        if confidence >= 0.65:
            return "High"
        if confidence >= 0.45:
            return "Medium"
        return "Low"

    @staticmethod
    def _indicators(features: dict[str, float]) -> list[str]:
        indicators: list[str] = []
        if features["url_count"] > 0:
            indicators.append(f"Contains {int(features['url_count'])} URL(s)")
        if features["url_has_ip"]:
            indicators.append("URL contains direct IP address")
        if features["url_has_at"]:
            indicators.append("URL contains @ symbol")
        if features["suspicious_keyword_count"] >= 2:
            indicators.append("Suspicious security/payment keywords detected")
        if features["urgency_keyword_count"] >= 1:
            indicators.append("Urgency language detected")
        if features["sender_domain_suspicious"]:
            indicators.append("Sender domain resembles known spoof patterns")
        if features["digit_ratio"] > 0.2:
            indicators.append("High numeric character ratio in content")
        if features["exclamation_count"] >= 3:
            indicators.append("Excessive exclamation marks")
        return indicators

    @staticmethod
    def _recommendations(is_phishing: bool) -> list[str]:
        if not is_phishing:
            return [
                "Email looks low-risk, but verify sender identity before acting.",
                "Hover over links before clicking.",
            ]
        return [
            "Do not click links or download attachments.",
            "Do not share credentials or OTP codes.",
            "Report this message to the security team.",
            "Block sender/domain if policy allows.",
        ]


phishing_model_service = PhishingModelService()
