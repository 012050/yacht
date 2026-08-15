# Yacht Dice Game

웹 기반 멀티플레이어 요트(Yacht) 다이스 게임입니다. 5개의 주사위를 최대 3회 굴려 12개 카테고리에 점수를 기록하는 턴제 게임입니다.

## 기술 스택

| 계층 | 기술 |
|------|------|
| Backend | Python 3.10+, FastAPI |
| Auth | JWT (HttpOnly 쿠키, Access + Refresh Token) |
| Frontend | React 18+, TypeScript, Vite |
| Real-time | WebSocket |
| Database | SQLite (SQLAlchemy ORM, WAL 모드) |
| Migration | Alembic |
| State Management | Zustand |
| Styling | Tailwind CSS |

## 프로젝트 구조

```
backend/          # FastAPI 백엔드
  app/
    main.py       # 진입점
    core/         # 설정, 의존성 주입
    database/     # SQLAlchemy 모델, 세션 관리
    models/       # 도메인 모델
    schemas/      # Pydantic 스키마
    services/     # 비즈니스 로직 (scoring, dice, game, auth, stats, websocket)
    api/routes/   # HTTP + WebSocket 라우트
  migrations/     # Alembic 마이그레이션
frontend/         # React + TypeScript 프론트엔드
  src/
    components/   # UI 컴포넌트
    hooks/        # 커스텀 훅 (auth, game, websocket)
    store/        # Zustand 스토어
    types/        # TypeScript 타입
    utils/        # 유틸리티 (점수 계산)
docs/             # 설계 문서
```

## 게임 규칙

- 5개 주사위를 최대 3회 굴립니다
- 원하는 주사위를 보관(keep)하고 나머지만 재굴릴 수 있습니다
- 12개 카테고리(상단 6개 + 하단 6개) 중 하나를 선택해 점수를 기록합니다
- 상단 합계가 63점 이상이면 +35점 보너스
- 각 플레이어의 턴에 60초 타임아웃 적용
- 게임 생성 시 6자리 참여 코드로 친구 초대

## 실행 방법

### Docker Compose (권장)

```bash
docker compose up -d --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### 로컬 개발

**Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health` | 헬스 체크 |
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| POST | `/api/auth/refresh` | 토큰 갱신 |
| POST | `/api/auth/logout` | 로그아웃 |
| GET | `/api/users/me` | 내 프로필 |
| GET | `/api/users/session` | 세션 확인 |
| GET | `/api/users/leaderboard` | 리더보드 |
| POST | `/api/games/` | 게임 생성 |
| POST | `/api/games/join` | 게임 참여 |
| GET | `/api/games/{id}` | 게임 정보 |
| POST | `/api/games/{id}/start` | 게임 시작 (host) |
| GET | `/api/games/{id}/current-turn` | 현재 턴 정보 |
| WS | `/ws/{game-id}` | WebSocket 연결 |

## 설정

`.env` 파일에서 설정할 수 있습니다:

```
DATABASE_URL=sqlite:////app/data/yacht.db
SECRET_KEY=your-secret-key
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7
TURN_TIME_LIMIT=60
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
