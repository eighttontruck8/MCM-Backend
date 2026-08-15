// src/mock/mockProducts.js

// 상품 카탈로그 가짜 데이터입니다.
// AI가 추천한 상품의 ID를 기반으로 화면에 상품 이미지와 가격을 매칭하여 띄울 때 사용해 주십시오.
export const mockProducts = [
  {
    "product_id": "P1001",
    "brand": "M·JOURNEY",
    "product_name": "프리미엄 캐시미어 니트",
    "price": 850000,
    "image_url": "https://via.placeholder.com/400x500?text=Cashmere+Knit",
    "stock_status": "in_stock",
    "category": "니트/스웨터",
    "tags": ["오버사이즈", "캐시미어", "베스트셀러"]
  },
  {
    "product_id": "P1002",
    "brand": "M·JOURNEY",
    "product_name": "시그니처 트렌치 코트",
    "price": 1250000,
    "image_url": "https://via.placeholder.com/400x500?text=Trench+Coat",
    "stock_status": "in_stock",
    "category": "아우터",
    "tags": ["클래식", "가을 필수템"]
  },
  {
    "product_id": "P1003",
    "brand": "M·JOURNEY",
    "product_name": "클래식 레더 숄더백",
    "price": 2100000,
    "image_url": "https://via.placeholder.com/400x500?text=Leather+Bag",
    "stock_status": "out_of_stock",
    "category": "악세서리",
    "tags": ["베스트셀러", "재고없음"]
  },
  {
    "product_id": "P1004",
    "brand": "M·JOURNEY",
    "product_name": "미니멀 울 슬랙스",
    "price": 450000,
    "image_url": "https://via.placeholder.com/400x500?text=Wool+Slacks",
    "stock_status": "in_stock",
    "category": "팬츠",
    "tags": ["모노톤", "미니멀"]
  },
  {
    "product_id": "P1005",
    "brand": "M·JOURNEY",
    "product_name": "실크 스카프 베이지",
    "price": 320000,
    "image_url": "https://via.placeholder.com/400x500?text=Silk+Scarf",
    "stock_status": "in_stock",
    "category": "악세서리",
    "tags": ["크로스셀", "포인트 아이템"]
  }
];