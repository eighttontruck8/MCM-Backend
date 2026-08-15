import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from load_data import load_products, get_customer_by_id

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_lookbook(customer_id):
    # 1. 고객 데이터와 제품 목록 불러오기
    customer = get_customer_by_id(customer_id)
    if customer is None:
        return "해당 고객을 찾을 수 없습니다."
    products = load_products()

    # 2. AI에게 줄 지시문(프롬프트)
    system_prompt = """당신은 럭셔리 브랜드 MCM의 퍼스널 스타일리스트입니다.
고객이 매장에 방문하기 전, 고객의 폰으로 전달할 '나만의 디지털 룩북'을 작성합니다.

MCM은 1976년 뮌헨에서 시작된, 여행과 이동을 중시하는 젊고 대담한 독일 럭셔리 브랜드입니다.
당신의 글은 고객이 설레며 매장에 방문하고 싶게 만드는, 우아하고 감성적인 톤이어야 합니다.
직원에게 지시하는 딱딱한 말투가 아니라, 고객에게 직접 건네는 다정하고 세련된 말투로 작성하세요.

반드시 아래 JSON 형식으로만 답변하세요. 다른 설명은 붙이지 마세요:
{
  "title": "룩북 제목 (고객의 상황·일정을 반영한 감성적인 한 줄)",
  "intro": "고객에게 건네는 인사와 이번 룩북 소개 (2~3문장, 다정하고 우아하게)",
  "looks": [
    {
      "product": "제품명",
      "styling": "이 제품을 어떤 상황에 어떻게 매치하면 좋은지 감성적으로 제안 (1~2문장)"
    }
  ],
  "closing": "매장 방문을 기대하게 만드는 마무리 한마디"
}

주의사항:
- 추천 제품은 반드시 아래 '제품 목록'에 있는 실제 제품만 사용하세요.
- 재고(stock)가 false인 제품은 룩북에 넣지 마세요. (고객을 실망시키지 않기 위해)
- 고객의 선호 색상, 스타일, 최근 조회 상품, 다가오는 일정을 감성적으로 녹여내세요.
- looks는 2~3개가 적당합니다.
"""

    user_prompt = f"""[고객 정보]
{json.dumps(customer, ensure_ascii=False, indent=2)}

[제품 목록]
{json.dumps(products, ensure_ascii=False, indent=2)}

위 고객을 위한 감성적인 디지털 룩북을 작성하세요."""

    # 3. AI 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


# 직접 실행하면 테스트
if __name__ == "__main__":
    customer_id = "C005"  # C001~C005 바꿔가며 테스트
    result = generate_lookbook(customer_id)

    print(f"=== {customer_id} 디지털 룩북 ===\n")
    lookbook = json.loads(result)
    print(json.dumps(lookbook, ensure_ascii=False, indent=2))