from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Protocol


class AIProvider(Protocol):
    def generate_lookbook(self, context: dict) -> object: ...

    def generate_staff_guide(self, context: dict) -> object: ...


class AIProviderUnavailable(RuntimeError):
    pass


PURPOSE_TAGS = {
    "BUSINESS_TRIP": {"비즈니스", "출장", "여행", "노트북수납", "기내반입"},
    "GIFT": {"선물", "클래식", "데일리"},
    "SPECIAL_EVENT": {"파티", "클래식"},
    "SEASON_UPDATE": {"데일리", "캐주얼"},
    "FREE_SHOPPING": {"데일리", "캐주얼"},
    "OTHER": {"데일리"},
}


def ranked_candidates(context: dict) -> list[dict]:
    preferred_colors = set(context["customer"].get("preferred_colors", []))
    purpose_tags = PURPOSE_TAGS.get(context["visit_context"].get("purpose_code"), {"데일리"})

    def score(product: dict) -> tuple[int, int, str]:
        color_score = len(preferred_colors.intersection(product["colors"]))
        purpose_score = len(purpose_tags.intersection(product["tags"]))
        return (purpose_score * 3 + color_score * 2, product["quantity"], product["product_id"])

    return sorted(context["candidate_products"], key=score, reverse=True)


class RuleBasedAIProvider:
    """외부 AI가 없거나 실패했을 때 사용할 결정적 문장 생성 Provider."""

    def generate_lookbook(self, context: dict) -> object:
        customer = context["customer"]
        purpose = context["visit_context"].get("purpose_code") or "FREE_SHOPPING"
        looks = [
            {
                "product_id": product["product_id"],
                "styling": f"{customer['preferred_style']} 무드에 {product['name']}을 매치해 보세요.",
            }
            for product in ranked_candidates(context)[:3]
        ]
        return {
            "title": f"{purpose.replace('_', ' ').title()}을 위한 MCM 컬렉션",
            "intro": f"{customer['display_name']} 고객님을 위한 맞춤 아이템을 준비했습니다.",
            "looks": looks,
            "closing": "선별된 아이템을 매장에서 직접 확인해 보세요.",
        }

    def generate_staff_guide(self, context: dict) -> object:
        customer = context["customer"]
        purpose = context["visit_context"].get("purpose_code") or "FREE_SHOPPING"
        products = ranked_candidates(context)[:3]
        return {
            "customer_summary": f"{customer['preferred_style']} 스타일을 선호하는 {customer['membership']} 고객입니다.",
            "recommended_products": [
                {
                    "product_id": product["product_id"],
                    "reason": f"{purpose} 방문 목적과 선호 스타일에 잘 맞는 상품입니다.",
                }
                for product in products
            ],
            "greeting": f"{customer['masked_name']} 고객님, 취향에 맞는 상품을 준비했습니다.",
            "cross_sell": "선택한 가방과 함께 활용할 수 있는 액세서리도 제안해 보세요.",
            "caution": "고객이 동의한 정보와 현재 방문 목적 안에서만 상담하세요.",
        }


class AIService:
    def __init__(self, provider: AIProvider, timeout_seconds: float, max_retries: int) -> None:
        self.provider = provider
        self.fallback = RuleBasedAIProvider()
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)

    def generate(self, method_name: str, context: dict) -> tuple[object, bool]:
        method = getattr(self.provider, method_name)
        for _ in range(self.max_retries + 1):
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(method, context)
            try:
                result = future.result(timeout=self.timeout_seconds)
                executor.shutdown(wait=True)
                return result, False
            except TimeoutError:
                future.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                executor.shutdown(wait=False, cancel_futures=True)
        fallback_method = getattr(self.fallback, method_name)
        try:
            return fallback_method(context), True
        except Exception as exc:
            raise AIProviderUnavailable("AI Provider와 기본 추천 생성이 모두 실패했습니다.") from exc
