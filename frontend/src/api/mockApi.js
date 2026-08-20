// src/api/mockApi.js
import { mockCustomers } from '../mock/mockCustomers';
import { mockProducts } from '../mock/mockProducts';

// AI 추천 결과를 모방하는 임시 데이터입니다.
const mockAiRecommendation = {
  "customer_summary": "클래식하면서도 세련된 모던 럭셔리 스타일을 선호하시는 고객입니다.",
  "recommended_products": [
    { "product_id": "P002", "name": "New Liz 비세토스 쇼퍼", "reason": "데일리부터 오피스까지 활용도 높은 클래식 쇼퍼입니다." },
    { "product_id": "P011", "name": "트렌치 코트", "reason": "시즌 전환기 필수 아우터로 고객님의 클래식 취향에 딱 맞습니다." },
    { "product_id": "P004", "name": "Aren 비세토스 E/W 숄더백", "reason": "단정한 비즈니스 룩에 완벽하게 어울리는 숄더백입니다." },
    { "product_id": "P001", "name": "Stark 베베 부 골드 크리스탈 비세토스 백팩", "reason": "골드 크리스탈이 포인트인 MCM 시그니처 백팩입니다." }
  ],
  "greeting": "고객님, 다시 방문해 주셔서 감사합니다.",
  "cross_sell": "쇼퍼백과 함께 Aren 체인 월렛을 매치해보시는 건 어떨까요?",
  "caution": "소재의 퀄리티와 클래식한 디자인을 중시하시니, 비세토스 라인을 중심으로 추천해 주십시오."
};

// 1. 전체 고객 목록을 불러오는 함수
export const fetchCustomers = async () => {
  return new Promise((resolve) => {
    // 서버 통신 시간을 모방하기 위해 0.8초 지연시킵니다.
    setTimeout(() => {
      resolve(mockCustomers);
    }, 800); 
  });
};

// 2. 특정 고객의 상세 정보를 불러오는 함수
export const fetchCustomerById = async (customerId) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const customer = mockCustomers.find(c => c.customer_id === customerId);
      if (customer) {
        resolve(customer);
      } else {
        reject(new Error("해당 고객의 정보를 찾을 수 없습니다."));
      }
    }, 500);
  });
};

// 3. 특정 상품의 상세 정보를 불러오는 함수
export const fetchProductById = async (productId) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const product = mockProducts.find(p => p.product_id === productId);
      if (product) {
        resolve(product);
      } else {
        reject(new Error("요청하신 상품을 찾을 수 없습니다."));
      }
    }, 500);
  });
};

// 4. AI 추천 데이터를 불러오는 함수
export const fetchAiRecommendation = async (customerId) => {
  void customerId;
  return new Promise((resolve) => {
    // AI가 분석하는 시간을 모방하기 위해 1.2초 지연시킵니다.
    setTimeout(() => {
      resolve(mockAiRecommendation);
    }, 1200); 
  });
};


const mockLookbookData = {
  "title": "당신을 위한 MCM 큐레이션",
  "intro": "고객님의 스타일에 맞춰 엄선한 MCM 컬렉션입니다.",
  "looks": [
    { "product_id": "P001", "product": "Stark 베베 부 골드 크리스탈 비세토스 백팩", "styling": "골드 크리스탈 디테일로 어떤 룩에도 포인트를 더하는 시그니처 백팩입니다.", "image_url": "/1.avif", "price": 2350000, "in_stock": true },
    { "product_id": "P002", "product": "New Liz 비세토스 쇼퍼", "styling": "넉넉한 수납과 클래식한 비세토스 패턴으로 데일리부터 오피스까지.", "image_url": "/2.avif", "price": 1150000, "in_stock": true },
    { "product_id": "P004", "product": "Aren 비세토스 E/W 숄더백", "styling": "단정한 셋업에 매치하면 세련된 비즈니스 룩을 완성할 수 있습니다.", "image_url": "/4.avif", "price": 980000, "in_stock": true },
    { "product_id": "P011", "product": "트렌치 코트", "styling": "시즌 전환기에 빠질 수 없는 클래식 아우터. 어깨 라인이 돋보입니다.", "image_url": "/11.avif", "price": 1980000, "in_stock": true },
    { "product_id": "P008", "product": "루렉스 데님 플레어 팬츠", "styling": "은은한 루렉스 광택이 글래머러스한 이브닝 룩에 어울립니다.", "image_url": "/8.avif", "price": 780000, "in_stock": true },
    { "product_id": "P013", "product": "시어링 ECONYL® 애비에이터 재킷", "styling": "지속 가능한 소재와 프리미엄 시어링의 조합. 겨울 스타일의 정점.", "image_url": "/13.avif", "price": 3200000, "in_stock": true }
  ],
  "closing": "매장에서 직접 착용감을 확인해 보세요. 고객님만을 위한 프라이빗 쇼핑이 준비되어 있습니다."
};

// 가상의 룩북 API 호출 함수입니다.
export const fetchLookbook = async (customerId) => {
  void customerId;
  return new Promise((resolve) => setTimeout(() => resolve(mockLookbookData), 1000));
};
