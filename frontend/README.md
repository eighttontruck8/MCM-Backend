# M-Journey Frontend

고객 모바일 웹과 직원 대시보드를 제공하는 React/Vite 애플리케이션이다. API 계약과 데이터 원본은 루트의 백엔드 명세와 `backend/` 구현을 따른다.

## 실행

Node.js 20.19 이상(Node 22 권장)이 필요하다.

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

기본 API 주소는 `http://127.0.0.1:8000`이며 `VITE_API_BASE_URL`로 변경한다.

## QR 체크인 흐름

백엔드 QR URL `/entry/{tag_token}`은 프론트의 다음 주소로 리다이렉트한다.

```text
/check-in?tag_token=<opaque-token>
```

프론트는 태그를 검증하고 로그인한 고객의 JWT로 체크인을 생성한다. Access/Refresh Token은 자동 로그인 선택 시 `localStorage`, 그렇지 않으면 `sessionStorage`에 저장한다.

현재 실제 연결 범위는 QR 검증, 고객·직원 로그인·비밀번호 재설정, 토큰 갱신, 고객 체크인 생성·재개, 쇼핑 방식 선택, 개인정보 공유 동의·방문 목적 제출, 직원 대기열 조회·배정과 WebSocket 재연결, 고객 추천·룩북·찜·구매 이력까지다.
