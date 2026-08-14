# M-Journey Backend

해커톤 MVP의 기본 백엔드다. 현재 고객·상품·재고 조회와 NFC 체크인, 쇼핑 방식, 동의/방문 목적 저장을 제공한다.

## 실행

```powershell
cd backend
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

## 현재 체크인 시연

모든 고객 API에는 임시 개발용 헤더가 필요하다.

```text
X-Customer-ID: C001
```

체크인 요청:

```json
POST /api/v1/check-ins
{
  "tag_token": "nfc-demo-seoul-001"
}
```

이 헤더 방식은 JWT 인증이 구현되면 제거한다.
