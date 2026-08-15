# M-Journey Backend

해커톤 MVP의 기본 백엔드다. 고객·직원 JWT 인증, 고객·상품·재고 조회와 QR 기반 매장 체크인, 쇼핑 방식, 동의/방문 목적 저장을 제공한다. NFC는 같은 진입 토큰 계약을 사용하는 선택 호환 방식이다.

## 실행

```powershell
cd backend
$env:M_JOURNEY_JWT_SECRET='<충분히 긴 임의 문자열>'
$env:M_JOURNEY_DEMO_PASSWORD='<데모 계정 비밀번호>'
$env:M_JOURNEY_FRONTEND_BASE_URL='http://localhost:5173'
$env:M_JOURNEY_DEMO_QR_TOKEN='<충분히 긴 임의 토큰>'
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

### QR 진입

QR에는 다음 백엔드 URL을 담는다.

```text
https://<backend-host>/entry/<M_JOURNEY_DEMO_QR_TOKEN>
```

스캔하면 백엔드가 활성 태그와 매장을 검증하고 다음 프론트 주소로 `307` 리다이렉트한다.

```text
<M_JOURNEY_FRONTEND_BASE_URL>/check-in?tag_token=<opaque-token>
```

프론트는 로그인 전후에 `tag_token`을 보존하고, 로그인 완료 후 아래 체크인 API를 호출한다. 모바일 실기기 데모에서는 `localhost` 대신 휴대폰에서 접근 가능한 배포 주소 또는 LAN 주소를 설정해야 한다.

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
  "tag_token": "<M_JOURNEY_DEMO_QR_TOKEN 값>"
}
```

토큰 갱신과 로그아웃은 각각 `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`에 `refresh_token`을 전달한다. 갱신 시 기존 Refresh Token은 즉시 폐기된다.

`GET /api/v1/entry-tags/{tag_token}`으로 로그인 전에 태그·매장·체크인 URL을 검증할 수 있다. 기존 `nfc-demo-seoul-001` 토큰도 NFC 호환 시연용으로 유지한다.

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

## 고객 부가 기능

고객 Access Token으로 다음 API를 사용할 수 있다.

- `GET /api/v1/customers/me/recommendations`: 저장된 AI 추천 중 현재 매장 재고가 있는 상품
- `GET /api/v1/customers/me/wishlist`: 찜 목록
- `POST /api/v1/customers/me/wishlist/{product_id}`: 찜 추가
- `DELETE /api/v1/customers/me/wishlist/{product_id}`: 찜 삭제
- `GET /api/v1/customers/me/purchases`: 구매 당시 가격·카테고리 기준 구매 이력

목록 응답은 공통 계약인 `{ "items": [...], "next_cursor": null }` 형식을 사용한다. 찜 추가는 같은 상품을 반복 요청해도 중복 레코드를 만들지 않는다.

## 개인정보 공유 동의 철회

고객은 `POST /api/v1/check-ins/{checkin_id}/consent/revoke`로 직원 정보 공유 동의를 철회할 수 있다.

- 직원 응대를 즉시 종료하고 `PRIVATE / SELF_SHOPPING`으로 전환한다.
- 배정 직원의 고객 프로필·AI 가이드 접근을 즉시 차단한다.
- 직원 가이드 출력과 자유 입력 방문 메모를 제거한다.
- 동의 정책 버전과 동의·철회 시각은 감사 가능성을 위해 보존한다.
- `CONSENT_REVOKED` 이벤트를 직원과 고객 WebSocket에 전달한다.
- 같은 철회를 반복 요청해도 최초 철회 시각을 반환한다.

법적·운영 보존 기간과 기간 만료 후 익명화·삭제 정책은 확정 전이므로 자동 purge는 아직 수행하지 않는다.

## 비밀번호 재설정

- `POST /api/v1/auth/password-reset/request`: 재설정 안내 요청
- `POST /api/v1/auth/password-reset/confirm`: 일회용 토큰과 새 비밀번호 제출

재설정 토큰은 기본 15분 동안 유효하며 DB에는 SHA-256 해시만 저장한다. 요청 API는 계정 존재 여부와 관계없이 같은 `202` 응답을 반환한다. 비밀번호가 변경되면 해당 사용자의 모든 Refresh Token을 폐기하고 인증 버전을 증가시켜 기존 Access Token과 WebSocket 연결용 토큰도 무효화한다.

실제 메일 Provider가 연결되기 전 로컬 시연에서만 `M_JOURNEY_EXPOSE_PASSWORD_RESET_TOKEN=true`를 설정해 응답의 `reset_token`을 확인할 수 있다. 운영 환경에서는 반드시 `false`로 유지하고 토큰을 메일 등 별도 채널로 전달해야 한다.

## 감사·요청 로그와 Rate Limit

로그인 성공·실패, 로그아웃, 비밀번호 재설정, 동의 철회, 직원 배정과 방문 상태 변경은 `audit_logs` 테이블에 기록한다. 감사 로그에는 비밀번호, 토큰, 이메일, 방문 메모를 저장하지 않는다.

HTTP 요청 로그는 JSON 문자열로 기록하며 다음 필드만 포함한다.

- `event`, `request_id`, `method`, `path`, `status_code`, `duration_ms`
- 요청 본문과 쿼리 문자열은 기록하지 않는다.

로그인, 비밀번호 재설정 요청, AI 룩북·가이드에는 sliding-window rate limit을 적용한다. 제한 초과 시 `429 RATE_LIMIT_EXCEEDED`와 `Retry-After` 헤더를 반환한다. 기본 제한은 환경변수로 조정할 수 있다.

- `M_JOURNEY_RATE_LIMIT_WINDOW_SECONDS=60`
- `M_JOURNEY_LOGIN_RATE_LIMIT=10`
- `M_JOURNEY_PASSWORD_RESET_RATE_LIMIT=5`
- `M_JOURNEY_AI_RATE_LIMIT=10`

현재 limiter는 단일 프로세스용이다. 다중 서버에서는 Redis 등 공유 저장소 기반 구현으로 교체해야 한다.
