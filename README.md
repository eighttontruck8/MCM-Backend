# M-Journey

M-Journey 백엔드, 고객·직원 프론트엔드, AI 추천 코드를 함께 관리하는 단일 저장소다. 서비스 데이터와 API 계약은 백엔드를 기준으로 한다.

```text
MCM-Backend/
├─ backend/   FastAPI, PostgreSQL, Alembic
├─ frontend/  React, Vite 고객·직원 화면
├─ ai/        AI 룩북·직원 가이드 생성 로직
└─ compose.yaml
```

## 실행 위치

- 백엔드와 PostgreSQL: 저장소 루트에서 `docker compose up --build`
- 백엔드 단독 개발: `backend/README.md` 참고
- 프론트엔드: Node.js 20.19 이상(Node 22 권장), `frontend`에서 `npm ci`, `npm run dev`
- AI: 현재 독립 프로토타입이며, 백엔드 `AIProvider` 계약에 맞춘 통합 작업이 필요하다.

각 하위 폴더에 별도 `.git`을 만들지 않는다. 모든 변경은 이 저장소의 `main` 브랜치에서 함께 관리한다.

## 통합 기준

- 고객·상품·매장·재고 원본과 인증·권한은 백엔드가 관리한다.
- 프론트는 백엔드 `/api/v1` REST 및 WebSocket 계약을 사용한다.
- AI는 백엔드가 전달한 context로 문장과 `product_id` 후보만 생성한다.
- 가격, 이미지, 재고는 AI나 프론트 mock이 아니라 백엔드 응답을 사용한다.
