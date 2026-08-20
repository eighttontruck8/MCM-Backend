# MCM-AI

M-Journey의 룩북·직원 접객 프롬프트 실험 코드다.

`ai_lookbook.py`와 `ai_guide.py`는 로컬 JSON을 사용하는 프롬프트 프로토타입으로 유지한다. 실제 서비스 호출은 백엔드의 `app/ai_openai.py`가 담당하며, 고객·상품·매장 재고 원본은 백엔드 DB에서 구성하고 AI 출력의 `product_id`도 백엔드에서 재검증한다.

실제 Provider 활성화 방법은 `backend/README.md`의 AI 추천 설정을 따른다. API 키는 파일에 저장하지 않고 `M_JOURNEY_OPENAI_API_KEY` 환경변수 또는 배포 환경의 Secret Manager로 주입한다.
