# Database migrations

애플리케이션 모델 변경은 Alembic migration으로 관리한다.

```powershell
$env:M_JOURNEY_DATABASE_URL='postgresql+psycopg://user:password@localhost:5432/mjourney'
uv run alembic upgrade head
```

새 migration은 모델 변경 후 다음 명령으로 생성하고 내용을 검토한다.

```powershell
uv run alembic revision --autogenerate -m "describe change"
```
