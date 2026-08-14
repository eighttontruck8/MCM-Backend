# M-Journey Backend

해커톤 MVP의 기본 백엔드다. 고객·직원 JWT 인증, 고객·상품·재고 조회와 NFC 체크인, 쇼핑 방식, 동의/방문 목적 저장을 제공한다.

## 실행

```powershell
cd backend
$env:M_JOURNEY_JWT_SECRET='<충분히 긴 임의 문자열>'
$env:M_JOURNEY_DEMO_PASSWORD='<데모 계정 비밀번호>'
uv sync --dev
uv run uvicorn app.main:app --reload
```

- API 문서: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health/live>

기본 SQLite DB는 첫 실행 시 자동 생성되고 가상 데이터가 입력된다.

## 테스트

```powershell
cd backend
uv run python -m pytest
```

`M_JOURNEY_JWT_SECRET`을 설정하지 않으면 프로세스 시작 시 임시 키가 생성되어 서버 재시작 후 기존 토큰을 사용할 수 없다. 데모 로그인 계정은 `M_JOURNEY_DEMO_PASSWORD`를 설정한 경우에만 seed 된다.

## 인증과 체크인 시연

Seed 계정:

- 고객: `customer@example.com`, `customer2@example.com`
- 직원: `staff@example.com`, `staff2@example.com` (`S001` 소속)
- 비밀번호: `M_JOURNEY_DEMO_PASSWORD` 환경변수에 설정한 값

로그인:

```text
POST /api/v1/auth/login
{
  "email": "customer@example.com",
  "password": "<M_JOURNEY_DEMO_PASSWORD 값>"
}
```

응답의 `access_token`을 고객 API의 Bearer 토큰으로 사용한다.

```text
POST /api/v1/check-ins
Authorization: Bearer <access_token>

{
  "tag_token": "nfc-demo-seoul-001"
}
```

토큰 갱신과 로그아웃은 각각 `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`에 `refresh_token`을 전달한다. 갱신 시 기존 Refresh Token은 즉시 폐기된다.

## 직원 방문 처리

직원 Access Token으로 다음 API를 사용할 수 있다.

- `GET /api/v1/staff/stores/S001/visits?status=WAITING_FOR_STAFF`: 대기열 동기화
- `POST /api/v1/staff/check-ins/{checkin_id}/claim`: 방문 수락
- `PATCH /api/v1/staff/check-ins/{checkin_id}/status`: `SERVING`, `COMPLETED` 상태 변경
- `GET /api/v1/staff/customers/{customer_id}`: 활성 방문과 동의 범위 내 마스킹 프로필 조회

직원은 JWT에서 확인된 소속 매장의 방문만 조회·수락할 수 있다. 두 직원이 같은 방문을 수락하면 한 요청만 성공한다.

## AI 추천

- `POST /api/v1/check-ins/{checkin_id}/lookbook`: 고객용 룩북 생성
- `GET /api/v1/staff/check-ins/{checkin_id}/guide`: 배정 직원용 응대 가이드 조회

현재는 백엔드 DB의 고객·방문 목적·매장 재고를 입력으로 사용하는 `AIProvider` 인터페이스와 규칙 기반 기본 Provider를 제공한다. 실제 AI 함수나 HTTP 클라이언트가 준비되면 Provider 구현만 교체하면 된다.

AI 출력의 `product_id`는 활성 상품과 매장 재고를 다시 확인하며 가격·이미지·수량은 항상 DB 값으로 덮어쓴다. 타임아웃이나 Provider 장애 시 품절 상품을 제외한 기본 추천을 반환하고, 형식이 잘못된 응답은 원문을 노출하지 않은 채 `502 AI_RESPONSE_INVALID`로 처리한다. 같은 입력의 검증된 결과는 `recommendations` 테이블에서 재사용한다.

## 실시간 이벤트

Access Token을 `token` 쿼리 파라미터로 전달해 연결한다.

- 직원: `ws://127.0.0.1:8000/api/v1/ws/staff/stores/{store_id}?token={access_token}`
- 고객: `ws://127.0.0.1:8000/api/v1/ws/customers/me?token={access_token}`

지원 이벤트:

- `VISIT_WAITING`: 직원 응대 요청 생성
- `AI_GUIDE_READY`: 직원 가이드 생성 또는 fallback 완료
- `STAFF_ASSIGNED`: 직원 배정 완료
- `VISIT_CANCELLED`: 방문 취소
- `VISIT_COMPLETED`: 방문 완료
- `PING`, `PONG`: 연결 확인

모든 이벤트는 `event`, `event_id`, `occurred_at`, `data` 필드를 가진다. WebSocket은 알림 수단이며 데이터 원본은 REST API와 DB다. 재연결한 직원 화면은 방문 대기열 REST API로 전체 상태를 다시 동기화해야 한다.

현재 `InMemoryEventBroker`는 단일 서버 시연용이다. 프론트·외부 AI 연동 방식은 이벤트 계약을 유지하고, 다중 서버 배포 시 브로커 구현만 Redis Pub/Sub 등으로 교체한다.
