import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from load_data import load_products, get_customer_by_id

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _validate_alternative_products(alternative_products, customer, products):
    """AI가 규칙(재고 없는 관심상품만 대체, name/replaces는 서로 다른 실제 제품명)을
    어긴 항목을 걸러낸다. 모델이 확률적으로 규칙을 놓칠 수 있어 코드로 재검증한다."""
    product_by_name = {p["name"]: p for p in products}
    candidates = set(customer.get("recently_viewed", [])) | set(customer.get("liked_products", []))
    valid_targets = {
        name for name in candidates
        if name in product_by_name and product_by_name[name]["stock"] is False
    }

    cleaned = []
    seen_replaces = set()
    for item in alternative_products if isinstance(alternative_products, list) else []:
        name = item.get("name")
        replaces = item.get("replaces")
        if replaces not in valid_targets:
            continue
        if name == replaces or name not in product_by_name or product_by_name[name]["stock"] is False:
            continue
        if replaces in seen_replaces:
            continue
        seen_replaces.add(replaces)
        cleaned.append({"name": name, "replaces": replaces})
    return cleaned


def generate_guide(customer_id):
    customer = get_customer_by_id(customer_id)
    if customer is None:
        return {"statusCode": 404, "message": "고객을 찾을 수 없습니다", "error": "CUSTOMER_NOT_FOUND"}
    products = load_products()

    system_prompt = """당신은 럭셔리 브랜드 MCM 매장의 AI 접객 어시스턴트입니다.
매장 직원이 고객을 맞이하기 직전, 직원에게 전달할 '접객 가이드'를 생성합니다.
당신의 역할은 직원을 대체하는 것이 아니라, 직원이 고객을 빠르게 이해하고
개인화된 응대를 준비하도록 돕는 것입니다.

MCM은 여행과 이동을 중시하는 젊고 대담한 독일 럭셔리 브랜드입니다.
톤은 우아하고 품격 있게 유지하세요.

반드시 아래 JSON 형식으로만 답변하세요. 다른 설명은 붙이지 마세요:
{
  "customer_summary": "고객 요약 (한 문장)",
  "style_analysis": {"미니멀": 50, "럭셔리": 20, "클래식": 15, "트렌디": 10, "캐주얼": 5},
  "style_tags": ["#미니멀", "#비즈니스", "#블랙"],
  "recommended_products": [
    {"name": "제품명 (시즌 포함, 예: 스타크 사이드 스터드 비세토스 백팩 26SS)", "reason": "이 고객의 어떤 데이터(최근 조회/과거 구매/일정 등)를 근거로 추천하는지 구체적으로 명시"}
  ],
  "alternative_products": [
    {"name": "대체 상품명", "replaces": "어떤 재고없는 상품을 대체하는지 (원본 상품명 명시)"}
  ],
  "greeting": "직원이 건넬 첫 인사 멘트",
  "cross_sell": "크로스셀 제안 (한 문장)",
  "caution": "이 고객만의 구체적인 응대 팁"
}

작성 규칙:
- style_analysis: 고객의 구매·조회 이력을 바탕으로 5가지 스타일(미니멀/럭셔리/클래식/트렌디/캐주얼)의 비율을 추정하되, 합이 반드시 100이 되게 하세요.
- style_tags: 태그 앞에 반드시 #을 붙이세요.
- recommended_products: 반드시 아래 '제품 목록'의 실제 제품 중 재고(stock)가 true인 제품만 사용하고, 제품명에 시즌(season)을 함께 표기하세요. reason에는 "최근 OO를 조회하셨고", "과거 OO를 구매하셨기에", "다음 주 OO 일정이 있어" 처럼 구체적 근거를 반드시 포함하세요.
- alternative_products: 이 고객의 recently_viewed(최근 조회) 또는 liked_products(좋아요) 목록에 있는 상품 중에서 재고(stock)가 false인 것이 있을 때만 사용합니다. purchase_history(과거 구매 이력)는 이 조건에 포함하지 않습니다 — 구매 이력에만 있고 recently_viewed/liked_products에는 없는 상품은 대상이 아닙니다. 조건을 만족하는 경우, name에는 재고 있는 다른 대체 상품을, replaces에는 재고 없는 원본 상품명을 넣으세요. name과 replaces는 반드시 '제품 목록'의 name 필드와 완전히 동일한 문자열이어야 하며, 시즌(season)이나 다른 텍스트를 덧붙이지 마세요. name과 replaces는 반드시 서로 다른 상품이어야 합니다. 위 조건을 만족하는 상품이 없으면 반드시 빈 배열 []로 두세요.
- 고객의 선호 색상, 스타일, 최근 조회 상품, 일정을 종합적으로 반영하세요.
- 반드시 아래 제품 목록에 실제로 존재하는 제품만 사용하고, 목록에 없는 제품명을 지어내지 마세요.
"""

    user_prompt = f"""[고객 정보]
{json.dumps(customer, ensure_ascii=False, indent=2)}

[제품 목록]
{json.dumps(products, ensure_ascii=False, indent=2)}

위 고객을 위한 접객 가이드를 생성하세요."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result["alternative_products"] = _validate_alternative_products(
            result.get("alternative_products"), customer, products
        )
        return result
    except Exception as e:
        return {"statusCode": 500, "message": "AI 응대 가이드 생성에 실패했습니다", "error": str(e)}


if __name__ == "__main__":
    customer_id = "C002"  # C001~C005 바꿔가며 테스트
    result = generate_guide(customer_id)
    print(f"=== {customer_id} 접객 가이드 ===\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))