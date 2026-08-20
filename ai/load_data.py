import json

# 제품 데이터 불러오기
def load_products():
    with open("products.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["products"]

# 고객 데이터 불러오기
def load_customers():
    with open("customers.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["customers"]

# 특정 고객 한 명 찾기 (id로)
def get_customer_by_id(customer_id):
    customers = load_customers()
    for c in customers:
        if c["id"] == customer_id:
            return c
    return None

# 이 파일을 직접 실행하면 데이터가 잘 불러와지는지 확인
if __name__ == "__main__":
    products = load_products()
    customers = load_customers()

    print(f"✅ 제품 {len(products)}개 불러옴")
    print(f"✅ 고객 {len(customers)}명 불러옴\n")

    print("=== 고객 목록 ===")
    for c in customers:
        print(f"- {c['id']} {c['name']} ({c['membership']}, {c['preferred_style']})")

    print("\n=== 김서연(C001) 상세 ===")
    seoyeon = get_customer_by_id("C001")
    print(json.dumps(seoyeon, ensure_ascii=False, indent=2))