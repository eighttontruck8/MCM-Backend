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
- 직원: `staff@example.com` (`S001` 소속)
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
