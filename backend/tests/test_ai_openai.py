from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.ai_openai import (
    LookbookOutput,
    OpenAIResponsesProvider,
    StaffGuideOutput,
)


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def parse(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        output_model = kwargs["text_format"]
        if output_model is LookbookOutput:
            parsed = LookbookOutput(
                title="서울 플래그십 룩북",
                intro="고객 취향을 반영한 제안입니다.",
                looks=[{"product_id": "P001", "styling": "블랙 재킷과 함께 연출하세요."}],
                closing="매장에서 직접 확인해 보세요.",
            )
        else:
            parsed = StaffGuideOutput(
                customer_summary="미니멀 스타일을 선호하는 고객",
                recommended_products=[{"product_id": "P001", "reason": "선호 색상과 일치"}],
                greeting="편안하게 둘러보실 수 있도록 안내해 주세요.",
                cross_sell="동일 컬러 액세서리를 제안하세요.",
                caution="동의한 정보만 활용하세요.",
            )
        return SimpleNamespace(output_parsed=parsed)


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def _context() -> dict:
    return {
        "customer": {"style_preferences": ["MINIMAL"], "preferred_colors": ["BLACK"]},
        "visit": {"purpose": "GIFT"},
        "candidate_products": [{"product_id": "P001", "name": "테스트 백", "quantity": 2}],
    }


@pytest.mark.parametrize(
    ("method_name", "expected_key"),
    [("generate_lookbook", "looks"), ("generate_staff_guide", "recommended_products")],
)
def test_openai_provider_uses_structured_responses_without_storing_input(
    method_name: str,
    expected_key: str,
) -> None:
    client = FakeClient()
    provider = OpenAIResponsesProvider(api_key=None, model="gpt-4o-mini", client=client)

    result = getattr(provider, method_name)(_context())

    assert result[expected_key][0]["product_id"] == "P001"
    call = client.responses.calls[0]
    assert call["model"] == "gpt-4o-mini"
    assert call["store"] is False
    sent_context = json.loads(call["input"][1]["content"])
    assert sent_context["candidate_products"][0]["product_id"] == "P001"


def test_openai_provider_requires_api_key_without_injected_client() -> None:
    with pytest.raises(ValueError, match="M_JOURNEY_OPENAI_API_KEY"):
        OpenAIResponsesProvider(api_key=None, model="gpt-4o-mini")


def test_openai_provider_rejects_missing_structured_output() -> None:
    client = FakeClient()
    client.responses.parse = lambda **_: SimpleNamespace(output_parsed=None)  # type: ignore[method-assign]
    provider = OpenAIResponsesProvider(api_key=None, model="gpt-4o-mini", client=client)

    with pytest.raises(ValueError, match="구조화된 결과"):
        provider.generate_lookbook(_context())
