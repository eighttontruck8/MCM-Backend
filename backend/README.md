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

## 데이터베이스 마이그레이션

스키마 변경은 Alembic으로 관리한다. 로컬 SQLite에서도 다음 명령으로 초기 스키마를 적용할 수 있다.

```powershell
cd backend
uv run alembic upgrade head
```

PostgreSQL 배포 환경에서는 연결 URL을 지정하고, 앱 시작 시 `create_all`과 데모 seed가 실행되지 않도록 설정한 뒤 마이그레이션을 먼저 적용한다.

```powershell
$env:M_JOURNEY_DATABASE_URL='postgresql+psycopg://user:password@host:5432/mjourney'
$env:M_JOURNEY_AUTO_CREATE_SCHEMA='false'
$env:M_JOURNEY_SEED_DEMO_DATA='false'
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

기존 개발용 SQLite 파일은 Alembic 도입 전에 `create_all`로 생성되었을 수 있다. 데이터 보존이 필요하지 않은 개발 DB는 파일을 다시 만든 뒤 `upgrade head`를 적용하고, 보존이 필요하면 스키마를 확인한 후에만 `alembic stamp head`를 사용한다.

## Docker로 PostgreSQL 실행

저장소 루트의 `compose.yaml`은 PostgreSQL과 API를 함께 실행한다. API는 DB health check가 통과한 뒤 Alembic migration을 적용하고 시작한다.

```powershell
cd ..
$env:M_JOURNEY_JWT_SECRET='<충분히 긴 임의 문자열>'
$env:M_JOURNEY_DEMO_PASSWORD='<데모 계정 비밀번호>'
docker compose up --build
```

- API 문서: <http://127.0.0.1:8000/docs>
- 준비 상태: <http://127.0.0.1:8000/health/ready>
- 종료: `docker compose down`
- DB 데이터까지 초기화: `docker compose down --volumes` (로컬 데모 데이터가 삭제됨)

Compose 파일의 기본 비밀번호와 JWT secret은 로컬 데모 전용이다. 외부 배포 전에는 `POSTGRES_PASSWORD`, `M_JOURNEY_JWT_SECRET`, `M_JOURNEY_DEMO_PASSWORD`, `M_JOURNEY_FRONTEND_BASE_URL`, `M_JOURNEY_CORS_ORIGINS`를 반드시 별도 환경변수로 설정한다. 다중 API 인스턴스 배포에서는 컨테이너마다 migration을 실행하지 말고 배포 단계의 단일 migration job으로 분리한다.

## 운영 CORS 설정

운영 배포에서는 환경과 실제 프론트 origin을 명시한다. 고객 웹과 직원 대시보드가 서로 다른 origin이면 쉼표로 구분한다.

```powershell
$env:M_JOURNEY_ENVIRONMENT='production'
$env:M_JOURNEY_FRONTEND_BASE_URL='https://shop.example.com'
$env:M_JOURNEY_CORS_ORIGINS='https://shop.example.com,https://staff.example.com'
```

운영 모드는 와일드카드, HTTP, localhost, 경로가 포함된 주소를 거부한다. `M_JOURNEY_FRONTEND_BASE_URL`도 QR 진입 리다이렉트 안전성을 위해 CORS 허용 목록에 포함되어야 한다. 허용 요청 헤더는 `Authorization`, `Content-Type`, `X-Request-ID`이며 응답에서는 `X-Request-ID`, `Retry-After`를 프론트에 노출한다.

### Render Blueprint 배포

저장소 루트의 `render.yaml`은 무료 플랜 기준으로 다음 리소스를 함께 만든다.

- `mjourney-api-eighttontruck8`: Docker FastAPI 서비스
- `mjourney-web-eighttontruck8`: React/Vite 정적 사이트
- `mjourney-db-eighttontruck8`: PostgreSQL

Render Dashboard에서 **New > Blueprint**를 선택하고 GitHub의 `eighttontruck8/MCM-Backend` 저장소를 연결한다. 초기 생성 화면에서 다음 두 비밀값만 직접 입력한다.

- `M_JOURNEY_DEMO_PASSWORD`: 12자 이상의 데모 로그인 비밀번호
- `M_JOURNEY_DEMO_QR_TOKEN`: 영문·숫자·`-`·`_`만 사용한 24자 이상의 임의 문자열

JWT secret은 Render가 자동 생성하고, API URL·프론트 URL·CORS와 DB 연결은 Blueprint가 연결한다. 첫 API 시작 시 Alembic migration 후 데모 seed가 입력된다. 배포가 끝나면 다음 주소를 확인한다.

- 프론트: <https://mjourney-web-eighttontruck8.onrender.com>
- API 준비 상태: <https://mjourney-api-eighttontruck8.onrender.com/health/ready>
- API 문서: <https://mjourney-api-eighttontruck8.onrender.com/docs>

Render가 이름 충돌 때문에 서비스명과 URL에 접미사를 붙인 경우, API의 `M_JOURNEY_PUBLIC_API_BASE_URL`, `M_JOURNEY_FRONTEND_BASE_URL`, `M_JOURNEY_CORS_ORIGINS`와 프론트의 `VITE_API_BASE_URL`을 실제 주소로 수정한 뒤 두 서비스를 다시 배포한다. 무료 PostgreSQL은 기간 제한이 있으므로 해커톤 이후 운영 전에는 유료 DB나 다른 운영 DB로 전환한다.

### 운영 배포 preflight

저장소 루트의 `.env.production.example`을 복사한 뒤 `example.com`과 모든 `<...>` 값을 실제 도메인·비밀값으로 교체한다. 실제 `.env.production`은 Git에서 제외된다.

```powershell
Copy-Item .env.production.example .env.production
cd backend
uv run --env-file ../.env.production python -m app.deployment
```

preflight는 실제 HTTPS API/프론트 origin, CORS 일치, PostgreSQL URL, 스키마 자동 생성 비활성화, JWT·데모 비밀번호·QR 토큰 강도를 검사한다. 성공 결과의 QR 토큰은 기본적으로 숨겨진다. QR 제작 직전에만 아래 명령으로 실제 진입 URL을 확인한다.

```powershell
uv run --env-file ../.env.production python -m app.deployment --show-qr-url
```

명령 출력에 포함된 실제 QR URL은 공개 로그나 저장소에 남기지 않는다.

### 인쇄용 시연 QR 생성

preflight를 통과한 운영 환경으로 저장소 루트의 `demo-artifacts/`에 흰 배경 SVG QR을 생성한다. 이 디렉터리는 Git에서 제외되며, QR 생성 결과의 콘솔 출력에도 실제 토큰을 표시하지 않는다.

```powershell
cd backend
uv run --env-file ../.env.production python -m app.demo_qr --output ../demo-artifacts/mjourney-entry.svg
```

기존 파일은 자동으로 덮어쓰지 않는다. 의도적으로 다시 만들 때만 `--force`를 추가한다. 생성된 SVG는 브라우저에서 열어 원본 비율로 인쇄하고, 실제 휴대폰 카메라로 HTTPS 접속과 체크인 완료까지 확인한다.

### 고객·직원 QR 시연 리허설

배포 후 아래 명령으로 두 시나리오를 순서대로 검증한다.

- 고객: readiness → QR 태그·프론트 리다이렉트 → 로그인 → 체크인 → PRIVATE → 룩북 → 취소
- 직원 응대: 고객 동의·응대 요청 → 직원 대기열 → 배정 → AI 가이드 → SERVING → COMPLETED

비밀번호와 QR 토큰은 명령행 인자로 받지 않고 `.env.production`에서만 읽는다. 리허설이 만든 체크인은 중간 실패 시 취소하며, 기존 활성 체크인이 있으면 임의로 변경하지 않고 중단한다.

```powershell
cd backend
uv run --env-file ../.env.production python -m app.demo_rehearsal
```

필요하면 `--scenario private` 또는 `--scenario staff`로 한 흐름만 실행한다. 기본값은 `all`이다.

로컬 Docker 환경은 명시적인 로컬 HTTP 허용 옵션으로 검증한다.

```powershell
$env:M_JOURNEY_DEMO_PASSWORD='mjourney-demo-password'
$env:M_JOURNEY_DEMO_QR_TOKEN='qr-demo-seoul-001-7f4d0b9e8c2a'
$env:M_JOURNEY_FRONTEND_BASE_URL='http://localhost:5173'
uv run python -m app.demo_rehearsal --api-base-url http://127.0.0.1:8000 --allow-http-local
```

자동 리허설 성공 후에도 실제 휴대폰 카메라, 모바일 브라우저, 직원 태블릿을 사용한 수동 전체 리허설은 별도로 수행한다.

## 테스트

```powershell
cd backend
uv run python -m pytest
```

`M_JOURNEY_JWT_SECRET`을 설정하지 않으면 프로세스 시작 시 임시 키가 생성되어 서버 재시작 후 기존 토큰을 사용할 수 없다. 데모 로그인 계정은 `M_JOURNEY_DEMO_PASSWORD`를 설정한 경우에만 seed 된다.

## 인증과 체크인 시연

고객은 `POST /api/v1/auth/signup`으로 이름, 연락처, 이메일, 4자 이상의 비밀번호를 제출해 가입할 수 있다. 가입 시 고객 프로필과 인증 계정을 한 트랜잭션으로 생성하고 Access/Refresh Token을 반환한다. 이메일과 연락처는 중복 가입할 수 없다.

직원은 로그인 화면의 `직원용 로그인`에서 진입한다. `POST /api/v1/auth/staff/signup`은 이름, 이메일, 4자 이상의 비밀번호, 매장 코드와 4자 이상의 직원 가입 코드를 검증한 뒤 `STAFF` 계정을 생성한다. 직원 가입 기능을 사용하려면 API 환경변수 `M_JOURNEY_STAFF_SIGNUP_CODE`를 설정해야 하며, 이 값은 프론트 코드나 저장소에 기록하지 않는다. 가입 완료 후 직원 로그인 화면으로 이동하며, 로그인 성공 후 소속 매장의 대기열 화면으로 이동한다.

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

백엔드 DB의 고객·방문 목적·매장 재고를 입력으로 사용하는 `AIProvider` 인터페이스를 제공한다. 기본값은 API 키 없이 동작하는 규칙 기반 Provider이며, 운영 환경에서는 OpenAI Responses API의 Pydantic Structured Outputs Provider를 선택할 수 있다.

```env
M_JOURNEY_AI_PROVIDER=openai
M_JOURNEY_OPENAI_API_KEY=환경변수나 Secret Manager에서 주입
M_JOURNEY_OPENAI_MODEL=gpt-4o-mini
M_JOURNEY_OPENAI_BASE_URL=https://api.openai.com/v1
```

API 키를 저장소나 로그에 남기지 않는다. OpenAI 요청은 `store=false`로 전송하며 AI는 추천 후보의 `product_id`와 표현 문장만 생성한다.

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

MVP 개인정보 보존 정책은 다음과 같다.

- 종료(`COMPLETED`, `CANCELLED`) 방문의 자유 입력 메모·방문 목적과 AI 추천 결과: 90일
- 만료된 Refresh Token·비밀번호 재설정 토큰: 만료 후 7일
- 비밀번호·토큰·이메일·방문 메모가 없는 감사 로그: 365일

동의 정책 버전·범위·동의/철회 시각과 추천 생성 이력 행은 감사 목적으로 유지한다. 보존 기간이 지난 추천은 출력만 제거하고 `REVOKED / PERSONAL_DATA_PURGED`로 표시한다. 활성 방문과 고객 프로필·찜·구매 이력은 이 정리 작업의 대상이 아니다.

명령은 `backend` 디렉터리에서 실행한다. 기본 실행은 변경 없이 대상 건수만 출력하며, `--execute`를 지정해야 실제 트랜잭션이 커밋된다.

```powershell
uv run python -m app.maintenance
uv run python -m app.maintenance --execute
```

Docker/PostgreSQL 환경에서는 저장소 루트에서 다음처럼 실행하며, 운영 스케줄러에서 하루 한 번 호출할 수 있다.

```powershell
docker compose run --rm api python -m app.maintenance --execute
```

보존 기간은 `M_JOURNEY_VISIT_PERSONAL_DATA_RETENTION_DAYS`, `M_JOURNEY_EXPIRED_AUTH_TOKEN_RETENTION_DAYS`, `M_JOURNEY_AUDIT_LOG_RETENTION_DAYS`로 조정한다.

## 비밀번호 재설정

- `POST /api/v1/auth/password-reset/request`: 재설정 안내 요청
- `POST /api/v1/auth/password-reset/confirm`: 일회용 토큰과 새 비밀번호 제출

재설정 토큰은 기본 15분 동안 유효하며 DB에는 SHA-256 해시만 저장한다. 요청 API는 계정 존재 여부와 관계없이 같은 `202` 응답을 반환한다. 비밀번호가 변경되면 해당 사용자의 모든 Refresh Token을 폐기하고 인증 버전을 증가시켜 기존 Access Token과 WebSocket 연결용 토큰도 무효화한다.

SMTP Provider는 다음 환경변수로 활성화한다. STARTTLS(일반적으로 587)와 SSL(일반적으로 465)은 동시에 켜지 않는다.

```env
M_JOURNEY_SMTP_HOST=smtp.example.com
M_JOURNEY_SMTP_PORT=587
M_JOURNEY_SMTP_USERNAME=...
M_JOURNEY_SMTP_PASSWORD=...
M_JOURNEY_SMTP_FROM=no-reply@example.com
M_JOURNEY_SMTP_STARTTLS=true
M_JOURNEY_SMTP_USE_SSL=false
```

SMTP가 설정되지 않은 로컬 시연에서만 `M_JOURNEY_EXPOSE_PASSWORD_RESET_TOKEN=true`를 사용해 응답의 `reset_token`을 확인할 수 있다. 운영 환경에서는 반드시 `false`로 유지한다. 메일 발송 실패는 계정 존재 여부가 노출되지 않도록 동일한 `202` 응답을 유지하며 서버 오류 로그로만 기록한다.

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
