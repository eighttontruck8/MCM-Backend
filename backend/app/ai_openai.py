from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field


class StructuredAIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LookbookCandidate(StructuredAIModel):
    product_id: str = Field(min_length=1)
    styling: str = Field(min_length=1)


class LookbookOutput(StructuredAIModel):
    title: str = Field(min_length=1)
    intro: str = Field(min_length=1)
    looks: list[LookbookCandidate]
    closing: str = Field(min_length=1)


class GuideCandidate(StructuredAIModel):
    product_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class StaffGuideOutput(StructuredAIModel):
    customer_summary: str = Field(min_length=1)
    recommended_products: list[GuideCandidate]
    greeting: str = Field(min_length=1)
    cross_sell: str = Field(min_length=1)
    caution: str = Field(min_length=1)


LOOKBOOK_SYSTEM_PROMPT = """당신은 럭셔리 브랜드 MCM의 퍼스널 스타일리스트입니다.
고객에게 직접 건네는 우아하고 간결한 한국어 룩북을 작성하세요.
추천 후보는 입력된 candidate_products 안에서만 고르고 product_id를 그대로 반환하세요.
재고, 가격, 이미지 같은 원본 데이터는 만들거나 수정하지 마세요.
선호 스타일, 색상, 방문 목적과 일정을 자연스럽게 반영하고 2~3개 상품을 추천하세요."""


STAFF_GUIDE_SYSTEM_PROMPT = """당신은 MCM 매장 직원의 AI 접객 어시스턴트입니다.
직원이 고객을 빠르게 이해하도록 품격 있고 실행 가능한 한국어 가이드를 작성하세요.
추천 후보는 입력된 candidate_products 안에서만 고르고 product_id를 그대로 반환하세요.
고객 동의 범위 밖의 정보를 추론하지 말고, 가격·재고·개인정보를 만들지 마세요.
추천 이유에는 공개된 취향과 방문 목적 중 실제 입력 근거만 사용하세요."""


class OpenAIResponsesProvider:
    """백엔드 검증 컨텍스트를 OpenAI Responses Structured Outputs에 연결한다."""

    # [Backend-04-'OpenAI Responses AI Provider'] AI는 후보 ID와 문장만 생성하고 원본 상품 정보는 백엔드가 검증한다.

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 10,
        client: Any | None = None,
    ) -> None:
        if client is None and not api_key:
            raise ValueError("OpenAI Provider를 사용하려면 M_JOURNEY_OPENAI_API_KEY가 필요합니다.")
        self.client = client or OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
        self.model = model

    def _generate(self, context: dict, system_prompt: str, output_model: type[StructuredAIModel]) -> dict:
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, separators=(",", ":")),
                },
            ],
            text_format=output_model,
            store=False,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("OpenAI가 구조화된 결과를 반환하지 않았습니다.")
        return parsed.model_dump(mode="json")

    def generate_lookbook(self, context: dict) -> object:
        return self._generate(context, LOOKBOOK_SYSTEM_PROMPT, LookbookOutput)

    def generate_staff_guide(self, context: dict) -> object:
        return self._generate(context, STAFF_GUIDE_SYSTEM_PROMPT, StaffGuideOutput)
