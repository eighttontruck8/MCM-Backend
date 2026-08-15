// src/api/mockApi.js
import { mockCustomers } from '../mock/mockCustomers';
import { mockProducts } from '../mock/mockProducts';

// AI 추천 결과를 모방하는 임시 데이터입니다.
const mockAiRecommendation = {
  "customer_summary": "최근 모노톤의 미니멀 럭셔리 스타일을 선호하시는 고객입니다.",
  "recommended_products": [
    { "product_id": "P1001", "name": "프리미엄 캐시미어 니트", "reason": "고객님의 최근 관심사인 가을 아우터와 잘 어울립니다." },
    { "product_id": "P1004", "name": "미니멀 울 슬랙스", "reason": "선호하시는 오버사이즈 실루엣에 매칭하기 좋습니다." }
  ],
  "greeting": "고객님, 다시 방문해 주셔서 감사합니다. 날씨가 많이 쌀쌀해졌죠?",
  "cross_sell": "니트와 함께 매치하기 좋은 울 슬랙스도 새로 들어왔는데 한번 보시겠습니까?",
  "caution": "가격보다는 소재의 퀄리티를 중시하시니, 캐시미어 소재의 장점을 강조해 주십시오."
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
  return new Promise((resolve) => {
    // AI가 분석하는 시간을 모방하기 위해 1.2초 지연시킵니다.
    setTimeout(() => {
      resolve(mockAiRecommendation);
    }, 1200); 
  });
};


const mockLookbookData = {
  "title": "가을의 정취를 담은 미니멀 룩북",
  "intro": "김** 고객님, 이번 가을 고객님의 우아함을 더해줄 스타일링을 제안합니다.",
  "looks": [
    { "product_id": "P1002", "product": "시그니처 트렌치 코트", "styling": "벨트를 묶어 허리선을 강조하고 미니멀 슬랙스와 매치해보세요." },
    { "product_id": "P1005", "product": "실크 스카프 베이지", "styling": "트렌치 코트 깃 안에 가볍게 둘러 포인트를 주면 완벽합니다." }
  ],
  "closing": "가까운 M·JOURNEY 매장에서 고객님만을 위한 프라이빗 피팅을 경험해보세요."
};

// 가상의 룩북 API 호출 함수입니다.
export const fetchLookbook = async (customerId) => {
  return new Promise((resolve) => setTimeout(() => resolve(mockLookbookData), 1000));
};