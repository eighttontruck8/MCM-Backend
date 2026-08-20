# M-Journey 백엔드 기능 명세서

> 작성 기준일: 2026-08-14  
> 범위: 해커톤 MVP 백엔드 및 프론트·AI 연동 계약  
> API 기준 경로: `/api/v1`

## 1. 결론: Python 3.12 + FastAPI 권장

이번 프로젝트의 백엔드는 **Python 3.12 + FastAPI**로 개발하는 것이 가장 적합하다.

선정 이유는 다음과 같다.

- AI 저장소가 이미 Python으로 작성되어 있어 `ai_guide.py`, `ai_lookbook.py`를 최소 수정으로 호출할 수 있다.
- FastAPI는 Pydantic 모델을 이용한 요청·응답 검증과 OpenAPI/Swagger 문서 생성을 기본 제공하므로 짧은 해커톤 기간에 프론트와 계약을 맞추기 쉽다.
- 직원 대시보드의 실시간 체크인 알림에 필요한 WebSocket을 지원한다.
- React/Vite 프론트는 언어가 달라도 JSON/HTTP 계약만 고정하면 문제없이 연결된다.
- 향후 AI가 별도 서버로 분리되어도 동일한 백엔드 API를 유지한 채 내부 호출만 HTTP 방식으로 바꿀 수 있다.

### 권장 기술 스택

| 구분 | MVP 권장 | 확장 시 |
|---|---|---|
| 언어/프레임워크 | Python 3.12, FastAPI | 동일 |
| 패키지 관리 | `uv` 또는 `pip` | 동일 |
| 데이터 검증 | Pydantic v2 | 동일 |
| ORM/마이그레이션 | SQLAlchemy 2.x, Alembic | 동일 |
| DB | PostgreSQL | 관리형 PostgreSQL |
| 실시간 알림 | FastAPI WebSocket | Redis Pub/Sub + WebSocket |
| 인증 | JWT Access/Refresh Token | HttpOnly 쿠키 또는 외부 IdP |
| AI 연동 | Python 함수 직접 호출 | 내부 AI HTTP API |
| 테스트 | pytest, HTTPX | 부하·통합 테스트 추가 |
| 배포 | Docker 1개 인스턴스 | API/AI/Redis 분리 |

> 해커톤 MVP에서는 Celery와 Redis를 처음부터 필수로 두지 않는다. 단일 인스턴스의 백그라운드 작업과 WebSocket으로 시연한 뒤, 다중 인스턴스가 필요할 때 도입한다.

### 대안 비교

| 선택지 | 장점 | 이번 프로젝트의 단점 | 판단 |
|---|---|---|---|
| Python + FastAPI | AI 코드 재사용, 빠른 API 작성, 자동 문서화 | 대규모 조직 표준화는 별도 규칙 필요 | **채택** |
| TypeScript + NestJS | 프론트와 언어 통일, 구조화 우수 | AI가 별도 Python 서비스가 되어 배포·디버깅 지점 증가 | 차선 |
| Java + Spring Boot | 안정적인 대규모 서비스 구조 | 해커톤 MVP와 현재 AI 코드 연결에는 상대적으로 무거움 | 후순위 |

---

## 2. 프로젝트와 현재 코드 상태

M-Journey는 고객의 온라인 구매·조회·관심 데이터를 QR 기본 매장 체크인과 연결해 다음 두 경험을 제공한다. NFC는 동일한 진입 URL을 사용하는 선택 호환 방식이다.

1. 고객: 개인화 디지털 룩북과 자유 쇼핑 또는 직원 응대 선택
2. 직원: 고객 동의 후 취향 요약, 추천 상품, 응대 멘트, 크로스셀 가이드 확인

2026-08-14 기준 저장소 확인 결과는 다음과 같다.

- 프론트: React + Vite + JavaScript. 로그인, QR 진입 로딩, 체크인 완료, 쇼핑 방식, 동의/방문 목적, 직원 배정, 룩북 등의 화면을 실제 API와 연결한다.
- AI: Python 함수 `generate_guide(customer_id)`, `generate_lookbook(customer_id)`와 고객 5명·상품 6개의 JSON 데이터가 있다. HTTP API는 아직 없다.
- 프론트의 룩북/직원 가이드 mock JSON과 AI 출력 필드는 서로 일치한다.
- 문서의 상품 예시(`P1001`, 캐시미어 니트)와 AI 실제 데이터(`P001`~`P006`, MCM 가방)는 불일치하므로 **AI 저장소의 상품 ID와 명칭을 MVP 기준 데이터로 통일**한다.

---

## 3. 시스템 책임 분리

```text
[고객 모바일 웹]                 [직원 태블릿 웹]
       |                                |
       +--------- HTTPS / WS -----------+
                        |
                [FastAPI Backend]
          인증 · 동의 · 체크인 · 직원 배정
          고객/상품 원본 · 재고 검증 · 로그
                        |
             +----------+----------+
             |                     |
       [PostgreSQL]             [AI Module/API]
       영속 데이터              문장/추천 생성
```

### 백엔드 책임

- 고객, 상품, 매장, 직원, 재고의 단일 원본 관리
- 인증과 고객/직원 권한 분리
- QR/NFC 진입 태그 및 매장 검증
- 체크인 세션과 상태 전이 관리
- 개인정보 제공 동의 원문·시각·범위 기록
- AI 입력 컨텍스트 구성, 출력 스키마 검증, 타임아웃/실패 처리
- 추천 상품 ID, 판매 상태, 매장 재고의 최종 검증
- 직원 배정의 동시성 제어
- 프론트에 안정적인 REST/WebSocket 계약 제공

### AI 책임

- 전달받은 고객·방문·상품 후보를 바탕으로 직원 가이드와 룩북 생성
- 정해진 JSON 스키마 준수
- 제공된 실제 상품만 언급
- 개인정보나 존재하지 않는 상품을 임의 생성하지 않음

### 프론트 책임

- 로그인, 동의, 방문 목적, 쇼핑 방식 입력과 유효성 UX
- API 결과 렌더링 및 로딩/오류/재시도 화면
- 직원 대시보드 WebSocket 구독
- 토큰과 `checkin_id`를 안전하게 유지

---

## 4. 핵심 사용자 흐름

### 4-1. QR 기본 매장 체크인

1. QR에는 `https://{backend-host}/entry/{opaque_tag_token}` 형태의 URL을 기록한다.
2. 백엔드는 태그와 매장을 검증한 뒤 `https://{front-host}/check-in?tag_token={opaque_tag_token}`으로 리다이렉트한다.
3. 고객이 QR을 스캔하면 모바일 웹이 열리고, 미로그인 상태라면 로그인 후 원래 `tag_token`을 복원한다.
4. 프론트가 `POST /check-ins`를 호출한다.
5. 백엔드는 태그 유효성, 매장 활성 상태, 중복 체크인을 검증하고 방문 세션을 만든다.
6. 고객은 룩북을 확인하고 `PRIVATE` 또는 `STAFF_ASSISTED` 쇼핑을 선택한다.
7. `STAFF_ASSISTED`는 정보 공유 동의가 있어야 직원 요청을 생성한다.
8. 백엔드는 AI 가이드 생성을 시작하고 직원 대시보드에 방문 이벤트를 보낸다.
9. 직원 한 명이 요청을 수락하면 고객 화면과 직원 화면 양쪽에 배정 결과를 보낸다.

### 4-2. 상태 전이

```text
CHECKED_IN
 ├─ PRIVATE 선택 ───────────────> SELF_SHOPPING ──> COMPLETED
 └─ STAFF_ASSISTED + 동의 ─────> WAITING_FOR_STAFF
                                  ├─ 직원 수락 ──> ASSIGNED ──> SERVING ──> COMPLETED
                                  └─ 고객 취소/만료 ─────────> CANCELLED 또는 EXPIRED
```

허용되지 않은 상태 전이는 `409 CHECKIN_STATE_CONFLICT`로 거절한다.

---

## 5. 공통 API 규칙

### 5-1. 형식

- Content-Type: `application/json`
- 시간: UTC ISO 8601 문자열로 저장·응답. 예: `2026-08-14T06:20:30Z`
- ID: 외부 노출 ID는 UUID 권장. 기존 데모 고객/상품 ID인 `C001`, `P001`은 유지 가능
- 금액: 원 단위 정수. 예: `1490000`
- 목록 응답: `items`, `next_cursor` 사용
- 필드명: `snake_case`로 통일
- API 버전: `/api/v1`

### 5-2. 공통 오류 응답

```json
{
  "error": {
    "code": "CUSTOMER_NOT_FOUND",
    "message": "고객을 찾을 수 없습니다.",
    "details": null,
    "request_id": "req_01J..."
  }
}
```

| HTTP | 사용 상황 |
|---|---|
| 400 | 잘못된 태그, 업무 규칙 위반 |
| 401 | 로그인 필요 또는 토큰 만료 |
| 403 | 동의 없음, 다른 매장 직원의 접근 |
| 404 | 고객·상품·체크인 없음 |
| 409 | 중복 체크인, 이미 다른 직원이 수락, 상태 충돌 |
| 422 | 요청 필드 검증 실패 |
| 429 | 로그인/AI 생성 호출 제한 |
| 502 | AI 응답 스키마 오류 |
| 503 | AI 일시 장애 또는 타임아웃 |

---

## 6. 기능 상세 명세

### F-01. 고객·직원 인증

프론트에 로그인·회원가입·비밀번호 재설정 화면이 있으므로 다음 계약을 제공한다.

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/auth/signup` | 고객 가입 | 불필요 |
| POST | `/auth/staff/signup` | 가입 코드와 매장 코드를 검증한 직원 가입 | 불필요 |
| POST | `/auth/login` | 고객/직원 로그인 | 불필요 |
| POST | `/auth/refresh` | Access Token 재발급 | Refresh Token |
| POST | `/auth/logout` | Refresh Token 폐기 | 필요 |
| POST | `/auth/password-reset/request` | 재설정 링크/코드 요청 | 불필요 |
| POST | `/auth/password-reset/confirm` | 새 비밀번호 저장 | 재설정 토큰 |
| GET | `/me` | 현재 로그인 사용자 조회 | 필요 |

MVP 로그인 요청:

```json
{
  "email": "customer@example.com",
  "password": "string"
}
```

성공 응답:

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "C001",
    "role": "CUSTOMER",
    "display_name": "김서연"
  }
}
```

인수 조건:

- 비밀번호는 평문으로 저장하거나 로그에 남기지 않는다.
- 직원 토큰에는 `role=STAFF`, `store_id`를 포함하고 고객 API와 직원 API를 분리한다.
- 직원 가입은 서버 환경변수 `M_JOURNEY_STAFF_SIGNUP_CODE`와 일치하는 가입 코드를 요구하고 활성 매장만 허용한다.
- 셀프 회원가입 비밀번호와 직원 가입 코드는 해커톤 데모 기준 최소 4자로 검증한다.
- 직원 가입 성공 시 토큰을 발급하지 않고 로그인 화면으로 이동해 새 계정으로 다시 인증한다.
- 데모에서는 가입/메일 전송을 mock 처리할 수 있으나 로그인과 권한 검사는 실제로 동작해야 한다.

### F-02. 고객 프로필

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/customers/me` | 본인 프로필·요약 조회 |
| GET | `/staff/customers/{customer_id}` | 동의된 활성 방문에 한해 직원용 프로필 조회 |

고객 응답 예시:

```json
{
  "customer_id": "C001",
  "name": "김서연",
  "membership": "VIP",
  "visit_count": 5,
  "preferred_colors": ["블랙", "코냑"],
  "preferred_style": "미니멀 비즈니스",
  "recently_viewed_product_ids": ["P001", "P006"],
  "liked_product_ids": ["P001"],
  "purchase_count": 2,
  "upcoming_schedule": "다음 주 싱가포르 출장"
}
```

직원 응답은 이름을 `김**`처럼 마스킹하고, 주소·연락처·로그인 정보는 절대 포함하지 않는다. 활성 방문의 동의 범위에 `STYLE_PROFILE`이 있으면 최근 조회·관심 상품의 `product_id`, 이름, 카테고리, 가격, 이미지를 제공하고, `PURCHASE_HISTORY`가 있으면 최근 구매 상품과 `ONLINE`/`OFFLINE` 채널을 제공한다. 상품 가격과 이미지는 AI 출력이 아닌 백엔드 상품 DB를 기준으로 한다.

### F-03. 상품·매장 재고

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/products?store_id=S001&in_stock=true` | 상품 목록 조회 |
| GET | `/products/{product_id}?store_id=S001` | 상품 상세·해당 매장 재고 조회 |
| GET | `/stores/{store_id}` | 체크인 화면용 매장 기본 정보 |

상품 응답 예시:

```json
{
  "product_id": "P001",
  "name": "스타크 사이드 스터드 비세토스 백팩",
  "line": "Stark",
  "category": "백팩",
  "colors": ["코냑", "블랙"],
  "material": "비세토스",
  "price": 1490000,
  "tags": ["여행", "비즈니스", "노트북수납", "데일리"],
  "image_url": "/assets/products/p001.jpg",
  "inventory": {
    "store_id": "S001",
    "quantity": 3,
    "in_stock": true,
    "updated_at": "2026-08-14T06:20:30Z"
  }
}
```

AI의 현재 `stock: boolean`은 데모에 쓸 수 있지만, 백엔드 DB에서는 매장별 `quantity`로 관리하고 `in_stock = quantity > 0`으로 계산한다.

### F-04. QR/NFC 진입 태그 기반 체크인 생성

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| GET | `/entry/{tag_token}` | QR 스캔 후 태그 검증 및 프론트 체크인 화면 리다이렉트 | 불필요 |
| GET | `/api/v1/entry-tags/{tag_token}` | 진입 태그·매장·체크인 URL 검증 | 불필요 |
| POST | `/api/v1/check-ins` | 인증 고객의 체크인 생성 | 고객 |
| POST | `/api/v1/check-ins/store` | 선택 매장 체크인 생성. `restart_active=true`이면 같은 매장의 이전 활성 방문을 종료하고 새 방문 시작 | 고객 |
| POST | `/api/v1/check-ins/demo` | 홈 버튼에서 서버 설정 QR 토큰으로 시연 체크인 생성 | 고객 |

`POST /check-ins`

```json
{
  "tag_token": "nfc_opaque_random_token"
}
```

`POST /check-ins/store`

```json
{
  "store_id": "S001",
  "restart_active": true
}
```

성공 `201 Created`:

```json
{
  "checkin_id": "2fb63ed2-1f0f-4ddd-bcc9-e8daf8e06b63",
  "store": {
    "store_id": "S001",
    "name": "MCM 서울 플래그십"
  },
  "customer": {
    "customer_id": "C001",
    "display_name": "김서연"
  },
  "status": "CHECKED_IN",
  "checked_in_at": "2026-08-14T06:20:30Z",
  "purchase_count": 2,
  "interest_count": 2
}
```

처리 규칙:

- `customer_id`, `store_id`를 프론트가 임의로 보내게 하지 않고 인증 토큰과 검증된 진입 태그에서 각각 결정한다.
- 같은 고객·매장에 종료되지 않은 체크인이 있으면 새 레코드를 만들지 않고 `409 ACTIVE_CHECKIN_EXISTS`와 기존 `checkin_id`를 반환한다.
- QR/NFC 진입 토큰은 예측 가능한 매장 ID 원문이 아닌 충분히 긴 임의 토큰으로 만든다. 노출·복제 시 비활성화 및 재발급이 가능해야 한다.

추가 조회:

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/check-ins/{checkin_id}` | 고객의 현재 체크인·배정 상태 |
| POST | `/check-ins/{checkin_id}/cancel` | 고객 체크인/요청 취소 |

### F-05. 쇼핑 방식 선택

`PATCH /check-ins/{checkin_id}/shopping-mode`

```json
{
  "shopping_mode": "STAFF_ASSISTED"
}
```

허용 값:

- `PRIVATE`: 직원 없이 AI 추천만 이용
- `STAFF_ASSISTED`: 동의 및 직원 배정 필요

응답에는 변경된 `status`와 다음 화면 경로 판단에 필요한 `next_action`을 반환한다.

```json
{
  "checkin_id": "2fb63ed2-1f0f-4ddd-bcc9-e8daf8e06b63",
  "shopping_mode": "STAFF_ASSISTED",
  "status": "CHECKED_IN",
  "next_action": "SUBMIT_CONSENT_AND_PURPOSE"
}
```

### F-06. 개인정보 공유 동의·방문 목적·직원 요청

`POST /check-ins/{checkin_id}/service-request`

```json
{
  "consent": {
    "agreed": true,
    "policy_version": "staff-profile-share-v1",
    "scopes": [
      "PURCHASE_HISTORY",
      "RECENT_INTERESTS",
      "STYLE_PROFILE",
      "AI_STYLE_REPORT"
    ]
  },
  "visit_purpose": {
    "code": "BUSINESS_TRIP",
    "note": "다음 주 출장용 노트북 가방"
  }
}
```

방문 목적 기본 코드:

- `GIFT`
- `SEASON_UPDATE`
- `SPECIAL_EVENT`
- `BUSINESS_TRIP`
- `FREE_SHOPPING`
- `OTHER`

성공 `202 Accepted`:

```json
{
  "checkin_id": "2fb63ed2-1f0f-4ddd-bcc9-e8daf8e06b63",
  "status": "WAITING_FOR_STAFF",
  "ai_guide_status": "GENERATING",
  "estimated_wait_minutes": 1
}
```

처리 규칙:

- `STAFF_ASSISTED`에서 `agreed=false`이면 직원에게 프로필을 보내지 않고 `403 PROFILE_SHARE_CONSENT_REQUIRED`를 반환한다.
- 동의 레코드에는 고객, 체크인, 정책 버전, 범위, 동의/철회 시각을 저장한다.
- 요청 성공 직후 `VISIT_WAITING` WebSocket 이벤트를 직원에게 보낸다.
- AI 생성 실패가 직원 요청 자체를 취소시키면 안 된다. 직원 화면에는 기본 고객 요약과 `AI_GUIDE_FAILED` 상태를 제공한다.

### F-07. 고객용 AI 룩북

`POST /check-ins/{checkin_id}/lookbook`

프론트 변경을 최소화하기 위해 응답의 핵심 필드는 현재 mock과 동일하게 유지한다.

```json
{
  "title": "성공적인 비즈니스 트립을 위한 MCM 컬렉션",
  "intro": "김서연 고객님을 위한 출장 스타일을 준비했습니다.",
  "looks": [
    {
      "product_id": "P001",
      "product": "스타크 사이드 스터드 비세토스 백팩",
      "styling": "수트 셋업과 매치해 실용적인 비즈니스 룩을 연출해 보세요.",
      "image_url": "/assets/products/p001.jpg",
      "price": 1490000,
      "in_stock": true
    }
  ],
  "closing": "선별된 아이템을 매장에서 직접 확인해 보세요.",
  "generated_at": "2026-08-14T06:20:35Z"
}
```

백엔드 검증:

- AI가 반환한 상품명을 DB 상품과 매칭한다. 장기적으로는 AI 출력에도 `product_id`를 필수로 추가한다.
- 고객용 룩북에는 해당 매장 재고가 있는 활성 상품만 포함한다.
- 상품 이미지, 가격, 재고는 AI 문장이 아닌 DB 값으로 덮어쓴다.
- 동일 고객 컨텍스트는 일정 시간 캐시하거나 `Recommendation` 레코드를 재사용해 반복 비용을 줄인다.
- AI 호출은 10초 이내 타임아웃, 1회 제한 재시도를 권장한다.

### F-08. 직원용 실시간 방문 대기열

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/staff/stores/{store_id}/visits?status=WAITING_FOR_STAFF` | 최초 접속/재연결 시 대기열 동기화 |
| WS | `/ws/staff/stores/{store_id}?token={access_token}` | 실시간 이벤트 수신 |

`VISIT_WAITING` 이벤트:

```json
{
  "event": "VISIT_WAITING",
  "event_id": "evt_01J...",
  "occurred_at": "2026-08-14T06:20:40Z",
  "data": {
    "checkin_id": "2fb63ed2-1f0f-4ddd-bcc9-e8daf8e06b63",
    "customer_id": "C001",
    "masked_name": "김**",
    "membership": "VIP",
    "visit_purpose": "BUSINESS_TRIP",
    "waiting_since": "2026-08-14T06:20:40Z",
    "ai_guide_status": "GENERATING"
  }
}
```

지원 이벤트:

- `VISIT_WAITING`
- `AI_GUIDE_READY`
- `STAFF_ASSIGNED`
- `VISIT_CANCELLED`
- `VISIT_COMPLETED`
- `PING` / `PONG`

WebSocket은 알림 수단일 뿐 데이터의 원본이 아니다. 연결이 끊긴 뒤에는 REST 대기열 API로 전체 상태를 다시 동기화한다.

### F-09. 직원 배정

`POST /staff/check-ins/{checkin_id}/claim`

요청 본문 없음. 로그인한 직원 ID와 매장은 토큰에서 가져온다.

성공:

```json
{
  "checkin_id": "2fb63ed2-1f0f-4ddd-bcc9-e8daf8e06b63",
  "status": "ASSIGNED",
  "staff": {
    "staff_id": "ST001",
    "name": "이민준",
    "title": "Client Advisor",
    "experience_years": 4
  },
  "assigned_at": "2026-08-14T06:21:10Z"
}
```

동시성 규칙:

- DB 트랜잭션에서 `WAITING_FOR_STAFF`인 행만 `ASSIGNED`로 원자적 변경한다.
- 두 직원이 동시에 수락하면 첫 요청만 성공하고 나머지는 `409 ALREADY_ASSIGNED`를 받는다.
- 성공 시 고객과 같은 매장의 직원들에게 `STAFF_ASSIGNED` 이벤트를 전송한다.

### F-10. AI 직원 응대 가이드

`GET /staff/check-ins/{checkin_id}/guide`

```json
{
  "checkin_id": "2fb63ed2-1f0f-4ddd-bcc9-e8daf8e06b63",
  "customer": {
    "customer_id": "C001",
    "masked_name": "김**",
    "membership": "VIP",
    "visit_count": 5,
    "visit_purpose": "BUSINESS_TRIP"
  },
  "customer_summary": "최근 비즈니스용 가방을 자주 본 미니멀 스타일의 VIP 고객입니다.",
  "recommended_products": [
    {
      "product_id": "P001",
      "name": "스타크 사이드 스터드 비세토스 백팩",
      "reason": "노트북 수납과 출장 목적에 적합합니다.",
      "image_url": "/assets/products/p001.jpg",
      "price": 1490000,
      "quantity": 3,
      "in_stock": true
    }
  ],
  "greeting": "김서연 고객님, 출장에 잘 맞는 가방을 미리 준비했습니다.",
  "cross_sell": "함께 사용할 수 있는 카드 지갑도 제안해 보세요.",
  "caution": "출장 일정이 가까우므로 수납과 기내 사용성을 먼저 설명하세요.",
  "generated_at": "2026-08-14T06:20:45Z"
}
```

접근 조건:

- 같은 매장의 인증된 직원이어야 한다.
- 유효한 동의가 있는 활성 체크인이어야 한다.
- 배정 전에는 최소 대기열 정보만 보이고, 상세 가이드는 배정 직원 또는 매장 정책상 허용된 직원만 조회한다.

재고 없는 상품을 AI가 언급하면 직원용 화면에서는 대체 상품을 함께 제공할 수 있다. 대체 우선순위는 `같은 카테고리 → 선호 색상/스타일 태그 → 용도 태그 → 가격 ±20% → 재고 수량` 순으로 한다.

### F-11. 방문 진행·완료

`PATCH /staff/check-ins/{checkin_id}/status`

```json
{
  "status": "SERVING"
}
```

허용 변경:

- `ASSIGNED → SERVING`
- `SERVING → COMPLETED`

완료 시 `completed_at`을 기록하고 직원의 고객 상세 접근을 종료한다. 고객 피드백은 MVP 이후 별도 기능으로 둔다.

### F-12. 찜·추천 홈 지원 기능

프론트 저장소에 메인 추천, 전체 추천, 찜, 마이페이지 화면이 있으므로 시연 범위에 포함한다면 다음 API를 제공한다.

| Method | Endpoint | 설명 | MVP 우선순위 |
|---|---|---|---|
| GET | `/customers/me/recommendations` | 저장된 추천 상품 목록 | P1 |
| GET | `/customers/me/wishlist` | 찜 목록 | P1 |
| POST | `/customers/me/wishlist/{product_id}` | 찜 추가 | P1 |
| DELETE | `/customers/me/wishlist/{product_id}` | 찜 삭제 | P1 |
| GET | `/customers/me/purchases` | 구매 이력 | P2 |

핵심 체크인 시연만 목표라면 이 기능은 고정 seed 데이터로 먼저 연결해도 된다.

---

## 7. 백엔드 ↔ AI 내부 계약

### 7-1. 현재 코드 호환 방식

MVP 첫 연동은 백엔드가 AI 저장소의 함수를 직접 import해 다음처럼 호출할 수 있다.

```python
guide_json_string = generate_guide("C001")
lookbook_json_string = generate_lookbook("C001")
```

주의할 점:

- 현재 함수는 성공 시 Python 객체가 아니라 JSON 문자열을 반환하므로 `json.loads()` 후 Pydantic으로 검증해야 한다.
- 고객 없음 오류도 JSON이 아닌 일반 문자열로 반환하므로 예외로 변경해야 한다.
- AI가 자체 `customers.json`, `products.json`을 읽어 백엔드 DB와 데이터가 이중화된다.
- 방문 목적과 매장별 재고가 현재 AI 입력에 들어가지 않는다.

### 7-2. 권장 목표 계약

AI 팀이 입력 변경 가능하다고 밝혔으므로, 최종적으로는 `customer_id`만 넘기기보다 백엔드가 허용된 최소 컨텍스트를 조합해 전달한다.

```json
{
  "request_id": "ai_req_01J...",
  "type": "STAFF_GUIDE",
  "customer": {
    "customer_id": "C001",
    "masked_name": "김**",
    "membership": "VIP",
    "visit_count": 5,
    "preferred_colors": ["블랙", "코냑"],
    "preferred_style": "미니멀 비즈니스",
    "purchase_history": [
      {"product_id": "P004", "category": "토트백", "purchased_at": "2025-11-02"}
    ],
    "recently_viewed_product_ids": ["P001", "P006"],
    "liked_product_ids": ["P001"],
    "upcoming_schedule": "다음 주 싱가포르 출장"
  },
  "visit_context": {
    "store_id": "S001",
    "purpose_code": "BUSINESS_TRIP",
    "purpose_note": "노트북 가방",
    "season": "SUMMER"
  },
  "candidate_products": [
    {
      "product_id": "P001",
      "name": "스타크 사이드 스터드 비세토스 백팩",
      "category": "백팩",
      "colors": ["코냑", "블랙"],
      "price": 1490000,
      "tags": ["여행", "비즈니스", "노트북수납"],
      "quantity": 3
    }
  ]
}
```

AI 출력 개선 요구:

- 상품 이름뿐 아니라 `product_id`를 반드시 반환한다.
- JSON 문자열이 아니라 HTTP JSON 객체 또는 타입이 정해진 Python 객체를 반환한다.
- 추천 상품은 `candidate_products`에 있는 ID만 허용한다.
- 백엔드는 최종적으로 DB 재고를 다시 검증한다.

---

## 8. 데이터 모델

| 테이블 | 핵심 필드 |
|---|---|
| `users` | `id`, `email`, `password_hash`, `role`, `is_active`, timestamps |
| `customers` | `user_id`, `customer_code`, `name`, `membership`, `preferred_style`, `upcoming_schedule` |
| `staff` | `user_id`, `staff_code`, `store_id`, `name`, `title`, `experience_years`, `availability` |
| `stores` | `id`, `code`, `name`, `timezone`, `is_active` |
| `nfc_tags` | `id`, `store_id`, `token_hash`, `is_active`, timestamps |
| `products` | `id`, `code`, `name`, `line`, `category`, `material`, `price`, `image_url`, `is_active` |
| `product_colors` | `product_id`, `color` |
| `product_tags` | `product_id`, `tag` |
| `inventories` | `store_id`, `product_id`, `quantity`, `updated_at` |
| `purchase_history` | `customer_id`, `product_id`, `category_snapshot`, `purchased_at` |
| `customer_interests` | `customer_id`, `product_id`, `type`(`VIEW`/`LIKE`), `occurred_at` |
| `checkins` | `id`, `customer_id`, `store_id`, `shopping_mode`, `visit_purpose_code`, `visit_note`, `status`, timestamps |
| `consents` | `id`, `checkin_id`, `customer_id`, `policy_version`, `scopes_json`, `agreed_at`, `revoked_at` |
| `staff_assignments` | `id`, `checkin_id`(unique), `staff_id`, `assigned_at`, `ended_at` |
| `recommendations` | `id`, `checkin_id`, `customer_id`, `type`, `status`, `input_hash`, `output_json`, `error_code`, timestamps |
| `refresh_tokens` | `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at` |
| `audit_logs` | `actor_id`, `action`, `resource_type`, `resource_id`, `metadata_json`, `created_at` |

필수 제약조건:

- `staff_assignments.checkin_id`는 unique
- `inventories(store_id, product_id)`는 unique
- 같은 고객·매장의 활성 체크인은 부분 unique index 또는 트랜잭션으로 방지
- 수량은 `quantity >= 0`
- 방문 상태, 사용자 역할, 추천 타입은 enum 또는 check constraint 적용

---

## 9. 개인정보·보안 요구사항

- 고객 정보는 백엔드가 소유하며 AI와 직원에게 목적에 필요한 최소 필드만 제공한다.
- 직원 상세 조회는 같은 매장, 활성 체크인, 유효한 동의, 적절한 역할을 모두 확인한다.
- 동의 전에는 구매 이력, 관심 상품, 스타일 리포트를 직원에게 보내지 않는다.
- QR/NFC URL에 고객 ID나 개인정보를 포함하지 않는다.
- 비밀번호, 토큰 원문, OpenAI API 키를 저장소나 로그에 남기지 않는다.
- 운영 로그의 이름·이메일·방문 메모 등은 마스킹하고 AI 프롬프트 전문 로깅은 기본 비활성화한다.
- CORS는 실제 프론트 도메인만 허용한다.
- 로그인, 비밀번호 재설정, AI 생성 API에는 rate limit을 둔다.
- 고객이 동의를 철회하거나 방문이 끝나면 직원 상세 접근을 즉시 차단한다.
- 해커톤 seed 데이터는 가상 인물임을 명시하고 실제 고객 데이터와 섞지 않는다.
- MVP 보존 기간은 종료 방문의 자유 입력·AI 결과 90일, 만료 인증 토큰 7일, 비식별 감사 로그 365일로 설정하며 환경변수로 조정한다.
- 보존 기간 만료 시 자유 입력·AI 출력은 제거하되 동의 정책·동의/철회 시각과 추천 생성 이력은 감사 가능한 형태로 관리한다.

---

## 10. 비기능 요구사항

| 항목 | MVP 기준 |
|---|---|
| 일반 API 응답 | 로컬/동일 리전 p95 500ms 이내(AI 제외) |
| 체크인 알림 | 체크인 요청 후 2초 이내 직원 화면 반영 |
| AI 생성 | 목표 10초, 타임아웃 15초 이내 |
| 가용성 | AI 장애 시 체크인·직원 배정은 계속 동작 |
| 일관성 | 직원 배정 중복 0건 |
| 문서화 | `/docs`, `/openapi.json` 제공 |
| 관측성 | `request_id`, 구조화 로그, AI 호출 시간·실패율 기록 |
| 헬스체크 | `GET /health/live`, `GET /health/ready` |

---

## 11. 프론트 화면별 연결표

| 현재 프론트 화면 | 호출 API | 필요한 프론트 수정 |
|---|---|---|
| `NfcLoadingPage` | URL `tag` 읽기, 로그인 확인 | 태그를 로그인 리다이렉트 후에도 보존 |
| `LoginPage` | `POST /auth/login` | 토큰 저장, 원래 체크인 흐름 복귀 |
| `CheckInCompletePage` | `POST /check-ins` 결과 | 매장명, 방문 시각, 고객명, 건수 placeholder 교체 |
| `ShoppingOptionPage` | `PATCH /check-ins/{id}/shopping-mode` | A/B 선택값을 실제 상태로 관리 |
| `VisitInfoPage` | `POST /check-ins/{id}/service-request` | 체크박스, 목적 pill, 직접 입력을 controlled input으로 구현 |
| `VisitInfoCompletePage` | `GET /check-ins/{id}` 또는 WS | AI/직원 요청 상태 표시 |
| `StaffAssignmentPage` | `GET /check-ins/{id}` 또는 WS | 실제 직원명·직책·전달 정보 표시 |
| `LookbookPage` | `POST /check-ins/{id}/lookbook` | mock import를 API 호출로 교체 |
| 직원 가이드 화면 | WS + `GET /staff/check-ins/{id}/guide` | 대기열 및 상세 가이드 연결 |

현재 프론트에는 직원 대시보드 라우트가 명확히 보이지 않으므로, 직원 전용 대기열/상세 화면의 담당 저장소와 라우트를 팀에서 확인해야 한다.

---

## 12. MVP 범위와 개발 순서

### P0: 시연에 반드시 필요

1. 고객/직원 seed 로그인 및 역할 검사
2. 고객·상품·매장·재고 seed 데이터 적재
3. QR/NFC 진입 태그 검증과 체크인 세션 생성
4. 쇼핑 방식, 동의, 방문 목적 저장
5. AI 룩북·직원 가이드 연동 및 출력 검증
6. 직원 대기열 REST + WebSocket 알림
7. 직원 수락의 원자적 배정
8. 고객 화면에 배정 결과 반영
9. Swagger 문서와 통합 시연 데이터

### P1: 시간이 남으면

- 찜 목록과 추천 홈 API
- AI 결과 캐시/재생성
- 직원 서비스 시작·완료 처리
- Redis 기반 이벤트 전달
- 날씨 API 연결(외부 호출 실패 시 시즌 기본값 사용)

### P2: 해커톤 이후

- 실제 회원가입·메일 재설정
- 실제 MCM CRM/재고 시스템 연동
- 직원 자동 배정 알고리즘
- 스마트 피팅룸, 사이즈/상품 요청
- 피드백과 추천 전환율 분석
- AI 이미지 생성 피팅 배경

### 권장 구현 순서

1. FastAPI 프로젝트 구조, 설정, DB, Alembic 구성
2. Pydantic 요청/응답 모델과 OpenAPI 계약 먼저 확정
3. seed 데이터 및 고객/상품 조회 구현
4. 인증과 역할 검사 구현
5. 체크인 상태 머신·동의·배정 트랜잭션 구현
6. AI 어댑터와 스키마/재고 검증 구현
7. WebSocket과 재연결용 REST 대기열 구현
8. 프론트와 happy path 통합
9. 오류·AI 장애·동시 수락 테스트
10. Docker 배포 및 전체 리허설

---

## 13. 필수 테스트/인수 시나리오

### 정상 흐름

- 유효 QR → 로그인 → 체크인 → 직원 응대 → 동의 → 목적 입력 → 직원 알림 → 직원 수락 → 고객 배정 화면
- 유효 QR → 체크인 → 프라이빗 쇼핑 → 룩북 조회 → 직원에게 개인정보 미노출
- 고객별로 서로 다른 룩북·가이드가 생성되고 실제 상품만 표시됨

### 인증·동의

- 미로그인 체크인 요청은 401이며 로그인 후 태그가 보존됨
- 동의하지 않은 직원 응대 요청은 403이고 직원 대기열에 나타나지 않음
- 다른 매장 직원은 고객 상세/가이드를 조회할 수 없음
- 방문 완료 후 직원 상세 접근이 차단됨

### 상태·동시성

- QR 재스캔으로 활성 체크인이 두 개 생기지 않음
- 직원 두 명이 동시에 수락해도 배정은 한 명만 성공함
- 잘못된 상태 전이는 409
- WebSocket 재연결 후 REST 조회로 최신 상태가 복구됨

### AI·재고

- AI 타임아웃이어도 체크인과 직원 수락은 성공함
- AI JSON 필드 누락/타입 오류는 502로 변환되고 원문이 프론트에 노출되지 않음
- 고객용 룩북에 품절 상품이 없음
- AI가 존재하지 않는 상품명/ID를 반환하면 제거하거나 안전한 기본 추천으로 대체함
- 가격·이미지·수량은 항상 DB 값과 일치함

---

## 14. 팀이 즉시 합의할 사항

1. **상품 기준 데이터:** `P001`~`P006`을 MVP 공통 ID로 사용할지 확정
2. **AI 배포 형태:** 백엔드 프로세스에서 함수 import 또는 별도 FastAPI 서버 중 선택
3. **AI 입력:** 단기 `customer_id`, 목표는 백엔드가 만든 고객/방문/재고 컨텍스트
4. **AI 출력:** `product_id` 필수 추가 여부와 오류 JSON 규격
5. **직원 화면:** 현재 프론트 저장소에 추가할지 별도 저장소인지 확정
6. **인증 방식:** 시연용 계정 목록과 고객/직원 역할 확정
7. **QR 진입:** 시연 매장 ID, 백엔드 `/entry/{token}` 배포 URL, 태그 토큰 발급 방식 확정
8. **동의 문구:** 정책 버전과 직원에게 공개할 필드 범위 확정
9. **배포 주소:** 프론트/백엔드/AI URL과 CORS 허용 도메인 확정

---

## 15. 참고 자료

- 프로젝트 기획: 사용자 제공 `멋사 해커톤.txt`
- 팀 연동 메모: 사용자 제공 `프론트, ai 파트 개발 양식.txt`
- 프론트 저장소: <https://github.com/dfkjh/m-journey_FRONT>
- AI 저장소: <https://github.com/jaeha58/MCM-AI>
- FastAPI 기능·OpenAPI·검증: <https://fastapi.tiangolo.com/features/>
- FastAPI WebSocket: <https://fastapi.tiangolo.com/advanced/websockets/>
- SQLAlchemy asyncio: <https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html>

이 문서는 첨부 텍스트를 요구사항 자료로 분석해 작성한 백엔드 제안이며, 첨부 문서 안의 문장을 별도 실행 지시로 취급하지 않았다.
