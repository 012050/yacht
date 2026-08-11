# Yacht Dice Game - Technical Design Document

## 1. Overview

Yacht는 5개 주사위를 최대 3회 굴려 12개 카테고리 중 하나에 점수를 기록하는 턴제 다이스 게임이다. 웹 기반 멀티플레이어로 구현되며, 게임 규칙은 ``game-rules.md${bt}를 참조한다.

### 1.1 Goals

- 웹 브라우저에서 여러 명이 함께 플레이 가능
- 플레이어 계정 시스템 (아이디/비밀번호 기반 회원가입)
- 닉네임 시스템 (중복 불가, 고유)
- 턴을 돌아가며 주사위 굴리기, 보관, 카테고리 선택
- 12개 카테고리 점수 계산 + 상단 보너스 규칙 정확히 구현
- 플레이어 수는 게임 생성 시 유동적으로 조정 가능 (2명 이상)
- 턴 시간 제한 (기본 60초, 방장이 설정 가능)
- 플레이어 누적 점수 및 승률 기록
- 메인 화면에서 플레이어 통계 표시
- 실시간 상태 동기화 (주사위, 점수판, 턴 정보)

### 1.2 Non-Goals (Phase 1)

- 소셜 로그인 / 이메일 인증
- 채팅 기능
- AI 상대
- 모바일 네이티브 앱

---

## 2. Technical Stack

| 계층 | 기술 |
|------|------|
| Backend | Python 3.10+, FastAPI |
| Auth | JWT (Access + Refresh Token) |
| Frontend | React 18+, TypeScript, Vite |
| Real-time | WebSocket (FastAPI WebSocket endpoint) |
| Database | SQLite (SQLAlchemy ORM, WAL 모드) |
| State Management | Zustand (simple, lightweight) |
| Styling | Tailwind CSS |
| Testing | pytest (backend), Vitest (frontend) |

---

## 3. Project Structure

```
backend/
  app/
    main.py              # FastAPI 진입점, 라우트 등록
    core/
      config.py          # 설정 값
      dependencies.py    # 의존성 주입
    models/
      user.py            # 플레이어 모델
      game.py            # 게임 상태 모델
      dice.py            # 주사위 모델
    schemas/
      user.py            # Pydantic schema (회원가입/로그인)
      game.py            # Pydantic schema (요청/응답)
      websocket.py       # WebSocket 메시지 스키마
    services/
      scoring.py         # 12개 카테고리 점수 계산 (순수 함수)
      dice_service.py    # 주사위 굴리기/보관 로직
      game_service.py    # 게임 흐름 관리 (턴, 라운드, 종료)
      auth_service.py    # 인증 (JWT 발급/검증)
      stats_service.py   # 플레이어 통계 (누적 점수, 승률, 게임 결과 저장)
      security_service.py  # Rate limiting, 입력 검증, CSRF 보호
      websocket_service.py # WebSocket 메시지 처리
    api/
      routes/
        auth.py          # HTTP 엔드포인트 (회원가입/로그인/토큰 갱신/세션 복구)
        users.py         # HTTP 엔드포인트 (프로필 조회/통계, 세션 복구)
        games.py         # HTTP 엔드포인트 (게임 생성/참가/정보 조회, 참여 코드 검증)
        websocket.py     # WebSocket 엔드포인트
    database/
      db.py              # SQLite 설정, 세션 관리
      models.py          # SQLAlchemy 테이블 모델
frontend/
  src/
    main.tsx
    App.tsx
    components/
      DiceRoller.tsx          # 주사위 표시, 굴리기/보관 UI
      Scoreboard.tsx          # 점수판 표시
      CategorySelector.tsx    # 카테고리 선택 UI
      PlayerList.tsx          # 참가자 목록
      PlayerStats.tsx         # 플레이어 통계 (누적 점수, 승률)
      GameStatus.tsx          # 현재 턴/라운드 정보, 남은 시간
      ResultScreen.tsx        # 게임 결과 화면 (상세 점수판, 랭킹, 재플레이)
      WaitingRoom.tsx         # 게임 시작 전 대기방 (시간 설정 UI)
      LoginPage.tsx           # 로그인/회원가입 폼
      HomeScreen.tsx          # 메인 화면 (플레이어 랭킹 표시)
    hooks/
      useWebSocket.ts         # WebSocket 연결/메시지 처리
      useAuth.ts              # 인증 훅 (토큰 관리)
      useGame.ts              # 게임 상태 관리
    types/
      game.ts                 # TypeScript 타입 정의
      user.ts                 # 사용자 타입 정의
    store/
      gameStore.ts            # Zustand store (게임 상태)
      authStore.ts            # Zustand store (인증 상태)
    utils/
      scoring.ts              # 프론트엔드 점수 계산 (예상 점수 표시용)
  index.html
  package.json
  tsconfig.json
  vite.config.ts
game-rules.md                 # 게임 규칙 문서
design.md                     # 이 파일
```

---

## 4. Backend Architecture

### 4.1 Game State Model

서버가 단일 소스 오브 트루스(single source of truth)로 게임 상태를 관리한다.

```python
class GameSession:
    id: str                          # 게임 고유 ID (URL 공유용)
    host_user_id: str                # 방장 ID (시간 설정 권한)
    players: list[GamePlayer]        # 참가 플레이어 목록
    current_player_index: int        # 현재 턴의 플레이어 인덱스
    current_round: int               # 현재 라운드 (1~12)
    dice: DiceState                  # 현재 주사위 상태
    rolls_remaining: int             # 남은 굴리기 횟수 (최대 3)
    turn_time_limit: int             # 턴 시간 제한 (초, 기본 60)
    turn_timer_expires_at: datetime  # 현재 턴의 시간 초과 시각
    scoreboards: dict[str, Scoreboard]  # 플레이어별 점수판
    status: GameStatus              # WAITING, PLAYING, FINISHED
    created_at: datetime
    finished_at: datetime | None
```

```python
class GamePlayer:
    user_id: str                     # 유저 테이블의 고유 ID
    join_order: int                  # 입장 순서
```

```python
class User:
    id: str                          # 고유 사용자 ID (UUID)
    username: str                    # 로그인용 ID (중복 불가)
    password_hash: str               # 해시화된 비밀번호
    nickname: str                    # 게임 표시용 닉네임 (중복 불가)
    total_games: int                 # 총 게임 수
    total_wins: int                  # 총 승리 수
    cumulative_score: int            # 누적 점수
    created_at: datetime
```

```python
class DiceState:
    values: list[int]               # 현재 주사위 5개
    kept_indices: set[int]          # 보관된 주사위 인덱스 (0-based)
```

```python
class Scoreboard:
    scores: dict[Category, int | None]  # None = 미선택
    upper_total: int               # 상단 합계 (보너스 계산용)
    bonus: int                     # 35 또는 0 (즉시 적용)
```


### 4.1.1 SQLite 동시성 관리

WAL(Write-Ahead Log) 모드를 사용하여 동시 읽기 성능을 높이고 쓰기 경쟁을 피한다.

- **WAL 모드**: 읽기 트랜잭션이 쓰기 트랜잭션을 블로킹하지 않음 (real-time 게임에서 대부분의 클라이언트가 상태 읽기)
- **세션 관리**: 각 WebSocket 연결당 별도 SQLAlchemy Session을 사용
- **쓰기 직렬화**: 같은 게임 세션에 대한 상태 변경은 서버 측에서 asyncio.Lock으로 직렬화
- **체크포인트**: WAL 파일이 커지지 않도록 주기적으로 `PRAGMA wal_checkpoint(TRUNCATE)` 실행

---
### 4.2 HTTP API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | 회원가입 (username, password, nickname) -- username/비밀번호 최대 20글자 |
| POST | ``/api/auth/login${bt}` | 로그인 (username, password) → JWT 반환 |
| POST | ``/api/auth/refresh${bt}` | 리프레시 토큰으로 액세스 토큰 갱신 |
| GET | ``/api/users/me${bt}` | 현재 사용자 프로필/통계 조회 |
| GET | ``/api/users/leaderboard${bt}` | 전체 플레이어 랭킹 (누적 점수/승률 기준) |
| POST | ``/api/games${bt}` | 새 게임 생성, 게임 ID + 방장 설정 반환 |
| POST | ``/api/games/{id}/join${bt}` | 게임 참가 (인증 필요) |
| GET | ``/api/games/{id}${bt}` | 게임 정보 조회 (상태, 플레이어 목록) |
| DELETE | ``/api/games/{id}/leave${bt}` | 게임 퇴장 |
| POST | ``/api/games/{id}/start${bt}` | 게임 시작 (방장만, 최소 2명 필요) |
| PUT | ``/api/games/{id}/settings${bt}` | 게임 설정 변경 (방장만, 시간 제한 조정) |

### 4.3 WebSocket Protocol

모든 게임 행동은 WebSocket을 통해 전달된다. 서버는 상태 변경을 모든 참가자에게 브로드캐스트한다.

```typescript
// Client -> Server
interface ClientMessage {
  type: 'ROLL' | 'KEEP' | 'FINISH_ROLLS' | 'SELECT_CATEGORY' | 'LEAVE' | 'SESSION_RECOVER'
  payload?: any
}

// Server -> Client
interface ServerMessage {
  type: 'STATE_UPDATE' | 'PLAYER_JOINED' | 'PLAYER_LEFT' | 'GAME_STARTED'
       | 'GAME_FINISHED' | 'TIME_WARNING' | 'TIME_EXPIRED' | 'SESSION_RECOVERED' | 'ERROR'
  payload: any
}
```

#### 메시지 흐름 예시

1. **주사위 굴리기**: client `ROLL` -> server 주사위 굴림 + 타이머 시작 -> `STATE_UPDATE` 브로드캐스트
2. **보관**: client `KEEP {indices}` -> server 보관 적용 -> `STATE_UPDATE`
3. **굴리기 종료**: client `FINISH_ROLLS` -> server 카테고리 선택 단계로 이동 -> `STATE_UPDATE`
4. **카테고리 선택**: client `SELECT_CATEGORY {category}` -> server 점수 기록, 보너스 체크, 턴 이전 -> `STATE_UPDATE`
5. **시간 경고**: 남은 10초 -> `TIME_WARNING` 브로드캐스트
6. **시간 초과**: timer expire -> 자동 카테고리 선택 -> `TIME_EXPIRED` + `STATE_UPDATE`

### 4.4 Authentication Flow

1. 사용자가 `/api/auth/register`으로 회원가입 (username, password, nickname)
2. username 또는 nickname 중복 시 에러 반환
3. 로그인 시 `/api/auth/login`으로 액세스 토큰(15분) + 리프레시 토큰(7일) 발급
4. 게임 참여 및 WebSocket 연결 시 JWT 인증 필요
5. 토큰 만료 시 리프레시 토큰으로 갱신

### 4.5 Player Stats

게임 종료 시 서버가 각 플레이어의 통계를 업데이트한다.

```python
def update_stats_on_finish(game: GameSession):
    for player in game.players:
        user = get_user(player.user_id)
        score = game.scoreboards[player.user_id].total()
        user.total_games += 1
        user.cumulative_score += score
        
        # 승자 판정 (동점 시 무승 처리 - 여러 승자도 total_wins 증가 않 함)
        winner_score = max(sb.total() for sb in game.scoreboards.values())
        winners = [sb for sb in game.scoreboards.values() if sb.total() == winner_score]
        if len(winners) == 1 and score == winner_score:
            user.total_wins += 1
        # 동점 시 무승으로 처리, cumulative_score는 기록됨
        # 동점 시 무승으로 처리, cumulative_score는 기록됨

---

## 5. Frontend Architecture

### 5.1 Page Flow

1. **로그인/회원가입 화면**: 처음 접속 시 로그인 필요
2. **홈 화면**: 플레이어 통계(누적 점수, 승률, 게임 수) 표시, 랭킹 보기, 게임 생성/참여
3. **대기방**: 참가자 목록, 게임 시작 버튼, 턴 시간 설정 (방장만), 게임 ID 공유
4. **게임 화면**: 주사위 UI, 점수판, 카테고리 선택, 플레이어 목록, 남은 시간
5. **결과 화면**: 최종 점수 순위, 보너스 여부 표시, 홈 화면으로 복귀

### 5.2 Component Structure

```
App
  Router
    /login -> LoginPage
    /register -> RegisterPage
    / -> HomeScreen (로그인 필요)
      Leaderboard       - 전체 랭킹 (누적 점수/승률)
      MyStats           - 내 통계
      GameActions       - 게임 생성/참여 버튼
    /game/:id -> GameContainer
      WaitingRoom (status == WAITING)
        PlayerList      - 참가자 목록
        HostSettings    - 방장용 설정 (시간 제한)
        StartButton     - 게임 시작 (방장만)
      GameScreen (status == PLAYING)
        GameStatus      - 현재 턴 정보, 남은 시간
        DiceRoller      - 주사위 표시, 굴리기 버튼, 보관 체크박스
        CategorySelector - 카테고리 목록, 예상 점수 표시
        Scoreboard      - 점수판 (본인 + 모든 플레이어)
        PlayerList      - 참가자 목록
      ResultScreen (status == FINISHED)
        FinalRanking    - 최종 점수 순위
        BackToHome      - 홈 화면으로 이동
```

### 5.3 State Management (Zustand)

```typescript
interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refresh: () => Promise<void>
}

interface GameState {
  gameId: string | null
  status: 'WAITING' | 'PLAYING' | 'FINISHED'
  currentRound: number
  currentPlayerId: string
  isMyTurn: boolean
  turnTimeRemaining: number  // 남은 시간 (초)

  diceValues: number[]
  keptIndices: number[]
  rollsRemaining: number

  scoreboards: Record<string, Scoreboard>
  myPlayerId: string | null
  players: PlayerInfo[]

  setGameState: (state: Partial<GameState>) => void
  handleRoll: () => void
  handleKeep: (indices: number[]) => void
  handleFinishRolls: () => void
  handleSelectCategory: (category: Category) => void
}
```

---

## 6. Scoring Logic Specification

점수 계산은 백엔드 `scoring.py`와 프론트엔드 `scoring.ts`에 동일하게 구현된다. 백엔드가 authority이며, 프론트엔드는 예상 점수 표시용으로만 사용한다.

### 6.1 숫자별 (ONES ~ SIXES)

```
count = dice 중 target_eye 의 개수
score = count * target_eye
```

### 6.2 Yacht

```
if 모든 주사위가 동일:
    score = 50
else:
    score = 0
```

### 6.3 Four of a Kind

```
counter = collections.Counter(dice)
max_count = counter 의 최댓값
if max_count >= 4:
    value = 해당 눈의 숫자
    score = (value * max_count) + 1
else:
    score = 0
```

### 6.4 Full House

```
counts = sorted(collections.Counter(dice).values())
if counts == [2, 3]:
    score = 25
else:
    score = 0
```

### 6.5 Small Straight

```
unique = sorted(set(dice))
for i in range(len(unique) - 3):
    if unique[i+3] - unique[i] == 3:
        return 30
return 0
```

### 6.6 Large Straight

```
unique = sorted(set(dice))
if unique == [1,2,3,4,5] or unique == [2,3,4,5,6]:
    return 40
return 0
```

### 6.7 Chance

```
return sum(dice)
```

### 6.8 Bonus

```
upper_total = sum of scores in categories 1~6 (only recorded ones)
if upper_total >= 63:
    bonus = 35  # 즉시 적용
else:
    bonus = 0
```

---

## 7. Turn Flow

```
[Turn Start]
  1. Dice.roll() - 첫 굴리기 (5개 전체, rolls_remaining = 3)
  2. turn_timer_expires_at = now + turn_time_limit
  3. WebSocket을 통해 모든 플레이어에게 주사위 상태 + 타이머 브로드캐스트
  4. 현재 턴 플레이어가 동작 가능

[During Turn - 굴리기/보관]
  5. 플레이어가 보관할 주사위 선택
  6. 플레이어가 '다시 굴리기' 또는 '굴리기 종료' 선택
  7. 만약 재굴리: Dice.reroll(exclude=kept), rolls_remaining -= 1
  8. turn_timer_expires_at = now + turn_time_limit (타이머 갱신, 재굴리마다 60초 리셋)
  9. 주사위 상태 + 남은 시간 브로드캐스트
  10. rolls_remaining > 0 이면 5로 반복

[Category Selection]
  11. '굴리기 종료' 시 카테고리 선택 단계로 전환
  12. 가능한 카테고리 목록 + 예상 점수 표시
  13. 플레이어가 카테고리 선택
  14. Scoreboard.record(category, score)
  15. 보너스 확인: 상단 합계 >= 63 이면 보너스 즉시 적용
  17. 모든 플레이어의 모든 카테고리 기록되면 게임 종료 (정상 종료)
  17. 모든 플레이어의 모든 카테고리 기록되면 게임 종료 (정상 종료)

[Time Expired]
  18. 타이머 만료 시 순간 판단
    - 주사위 굴리기/보관 단계 중: 보관된 주사위는 그대로 두고, 다른 주사위를 자동 굴린 후
      가장 높은 점수의 미선택 카테고리에 자동 기록
    - 카테고리 선택 단계: 가장 높은 점수의 미선택 카테고리에 자동 기록
  19. TIME_EXPIRED + STATE_UPDATE 브로드캐스트 + 턴 이전
[Turn End]
  21. 상태 브로드캐스트
  22. 다음 플레이어 턴 시작 (1로 복귀)
```

### 7.1 Turn Constraints

- 주사위 굴리기: 최대 3회 (첫 굴리 + 재굴리 2회)
- 3회 굴린 후 또는 보관할 주사위가 없을 때 카테고리 선택 강제
- 카테고리 선택은 반드시 하나 (0점이라도 기록)
- 이미 선택한 카테고리는 재선택 불가
- 턴 시간 제한: 기본 60초, 방장이 대기방에서 설정 가능 (30~120초)
- 플레이어 퇴장 시: 다른 플레이어가 1명 이하라면 게임 종료 (비정상 종료로 기록, 점수판에 포함하지 않음), 아니만 턴 순서에서 제외
- 플레이어 텔장 시: 다른 플레이어가 1명 이하라면 게임 종료 (비정상 종료로 기록, 점수판에 포함하지 않음), 아니만 턴 순서에서 제외

### 7.2 Auto-Select on Timeout

시간 초과 시 자동 선택 로직:

```
available = scoreboard.available_categories()
best_category = None
best_score = -1

for cat in available:
    score = Scorer.calculate(cat, dice.values)
    if score > best_score:
        best_score = score
        best_category = cat

scoreboard.record(best_category, best_score)
```

---

## 8. Database Schema (SQLite)

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- UUID
    username TEXT NOT NULL UNIQUE,    -- 로그인용 ID (중복 불가)
    password_hash TEXT NOT NULL,
    nickname TEXT NOT NULL UNIQUE,    -- 게임 표시용 닉네임 (중복 불가)
    total_games INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    cumulative_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE games (
    id TEXT PRIMARY KEY,              -- UUID
    host_user_id TEXT NOT NULL,       -- 방장 ID
    status TEXT NOT NULL DEFAULT 'WAITING',
    current_player_index INTEGER DEFAULT 0,
    current_round INTEGER DEFAULT 1,
    turn_time_limit INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    FOREIGN KEY (host_user_id) REFERENCES users(id)
);

CREATE TABLE game_players (
    game_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    join_order INTEGER NOT NULL,
    PRIMARY KEY (game_id, user_id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE scoreboards (
    game_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    score INTEGER NOT NULL,
    PRIMARY KEY (game_id, user_id, category),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE game_results (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rank INTEGER NOT NULL,
    total_score INTEGER NOT NULL,
    top_section_sum INTEGER NOT NULL,
    bottom_section_sum INTEGER NOT NULL,
    bonus INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 9. Error Handling

| Case | Behavior |
|------|----------|
| 잘못된 보관 인덱스 | WebSocket ERROR 메시지, 클라이언트 재시도 |
| 이미 선택한 카테고리 | ERROR 메시지, 다른 카테고리 선택 요청 |
| 턴이 아닌 플레이어가 동작 시도 | ERROR 메시지, 무시 |
| WebSocket 연결 끊김 | 자동 재연결 시도 (최대 3회), 실패 시 게임에서 제외 |
| 플레이어 퇴장 | 상태 브로드캐스트, 턴 순서 업데이트 |
| 아이디/비밀번호 20글자 초과 | 회원가입/로그인 시 400 에러 반환 |
| 중복 닉네임/아이디 | 회원가입 시 에러, 다른 이름 입력 요청 |
| 아이디/벨림발호 20글자 초과 | 회원가입/로그인 시 400 에러 반환 |
| 만료된 JWT | 401 에러, 리프레시 토큰으로 갱신 시도 |

---

## 10. Test Plan

### 10.1 Backend Tests (pytest)

- **test_scoring.py**: 12개 카테고리 + 보너스 규칙
  - 조건 만족 케이스 (game-rules.md 예시)
  - 조건 불만족 케이스 (0점 반환)
  - 경계 케이스: [1,1,1,1,1], [6,6,6,6,6], [1,2,3,4,6]
  - 보너스 즉시 적용 테스트 (상단 합계 62 -> 63이 되는 시점)
- **test_dice_service.py**: 굴리기, 보관, 재굴리 상태 변화
- **test_game_service.py**: 턴 흐름, 라운드 진행, 게임 종료, 보너스 적용 시점
- **test_scoreboard.py**: 중복 기록 차단, 합산, is_full()
- **test_auth_service.py**: 회원가입 중복 체크, 로그인, 토큰 발급/검증
- **test_stats_service.py**: 게임 종료 시 통계 업데이트, 승률 계산
- **test_timeout.py**: 시간 초과 자동 선택 로직

### 10.2 Frontend Tests (Vitest)

- **scoring.test.ts**: 백엔드와 동일한 테스트 케이스
- **DiceRoller.test.tsx**: 보관 선택, 재굴리 상태
- **Scoreboard.test.tsx**: 점수 표시, 보너스 표시
- **GameStatus.test.tsx**: 남은 시간 표시, 타이머 감소

### 10.3 Cross-Validation Test

- **test_scoring_sync.py**: 백엔드(`scoring.py`)와 프론트엔드(`scoring.ts`)의 점수 계산 출력이 일치하는지 확인
  - 12개 카테고리 × 다양한 주사위 조합(최소 100개 케이스)에 대해 양쪽 출력을 비교
  - CI에서 backend pytest가 후에 frontend vitest를 순차 실행하고 결과를 매칭
  - 불일치 시 실패 + differing 입력 케이스 출력

### 10.4 Coverage Target

- 점수 계산 로직: 100%
- 전체: 80% 이상

---

## 11. Development Phases

### Phase 1: Backend Core + Auth

- [ ] FastAPI 프로젝트 세팅
- [ ] 데이터베이스 모델 정의 (User, Game, GamePlayer, Scoreboard)
- [ ] 인증 시스템 (JWT 회원가입/로그인/토큰 갱신)
- [ ] ``scoring.py${bt}` - 12개 카테고리 점수 계산 + 보너스
- [ ] ``dice_service.py${bt}` - 주사위 로직
- [ ] ``game_service.py${bt}` - 게임 흐름 관리
- [ ] HTTP 엔드포인트 (게임 생성/참가/조회, 사용자 API)
- [ ] 유닛 테스트

### Phase 2: WebSocket + Real-time

- [ ] WebSocket 엔드포인트 구현
- [ ] 메시지 처리 및 상태 브로드캐스트
- [ ] 턴 흐름 WebSocket 통합
- [ ] 타이머 + 자동 선택 로직
- [ ] 통합 테스트

### Phase 3: Frontend

- [ ] React + TypeScript 프로젝트 세팅 (Vite)
- [ ] 인증 UI (로그인/회원가입)
- [ ] 홈 화면 + 랭킹 표시
- [ ] WebSocket 연결 및 상태 관리
- [ ] 컴포넌트 구현 (대기방, 게임 화면, 결과 화면)
- [ ] 프론트엔드 테스트

### Phase 4: Polish

- [ ] UI/UX 개선
- [ ] 플레이어 퇴장 처리
- [ ] 전체 게임 흐름 테스트
- [ ] 배포 설정

---


## 12. Security

### 12.1 Rate Limiting

- FastAPI middleware ?? ?? (slowapi ?? ??? middleware)
- ?? ????? (????/???): ?? 10? ?? (IP ??)
- ?? ????? (??? ???/???? ??): ?? 30? ?? (user ??)
- WebSocket ???: ?? 10? ?? (?? ??)
- ?? ? 429 Too Many Requests ??

### 12.2 ?? ??

- ?? API ?? body: Pydantic schema ?? ?? (?? ??, ??, ?? ?)
- ???/????/???: ?? 20??, ???/??/???? ??
- ??? ?? ???: 0~4 ?? ??, ?? ?? ? ?
- ???? ??: ??? 12? ?????? ??
- JWT ??: ?? ?? ??, issuer ??
- ?? ??: 6?? ???+??? ?? (??? ^[A-Z0-9]{6}$)

### 12.3 CSRF ??

- HTTP API: CSRF ?? ?? ?? (SameSite Cookie + CSRF token ??)
- WebSocket: JWT ?? ? ?? ?? (CSRF?? ??, bidirectional channel)
- Cookie ??: `SameSite=Lax`, `HttpOnly`, `Secure`(????)
- CORS: ????? ???? ?? ( whitelist ??)

## 13. Results Screen & Session Recovery

### 13.1 ?? ?? (ResultScreen)

?? ??(FINISHED ??) ? ???? ??. ?? ??? ?????:

- **???? ??**: ?? ? ???? ?? (1? ? N?), ?? ? ?? ?? ??
- **?? ???**: ? ????? 12? ????? ??, ?? ??, ?? ??, ???, ??
- **???? ??**: "?? ???" ?? ? ?? ???? ???? ? ?? ?? (? game_id, ? join_code)
- **?? ????**: ?? ?? ?? ? ?? ??? ???? ??/?? ?? ??

```typescript
interface GameResult {
  game_id: string
  players: ResultPlayer[]
  finished_at: string
}

interface ResultPlayer {
  user_id: string
  display_name: string
  rank: number
  total_score: number
  scores: Record<string, number>  // category -> score
  top_section_sum: number
  bottom_section_sum: number
  bonus: number
}
```

### 13.2 ??? ???? ?? ??

???? ?? ? ???? ??????? ????? ???? ?? ? ?, ?? ?? ??? ?????.

**?? ??**:

1. **?? ??**: localStorage? Access/Refresh ??? ????? ??
2. **?? ??**: Access ?? ?? ? Refresh ???? ?? (`/api/auth/refresh`)
3. **?? ?? ??**: `GET /api/users/session` ?? ? ?? ??? ?? ?? ?? ??
4. **?? ??**: ?? ??? 1?? ?? ??, ?? ?? ?? UI ??
5. **WebSocket ???**: ??? ??? WebSocket ?????? ?? ???? ??
6. **SESSION_RECOVER ??**: `{type: 'SESSION_RECOVER', payload: {game_id}}` ??
7. **STATE_UPDATE ??**: ??? ?? ?? ?? ?? ?? (???, ?, ???, ??? ?)
8. **UI ??**: ??? ??? ????? ?? ???

**?? ? ??**:

- `SESSION_RECOVER` ??? ?? ? ?? ??? ??? ?????? ?? (JWT user_id ??)
- ?? ??? PLAYING ?? WAITING ? ?? ?? ?? ??
- ?? ??? FINISHED ? ?? ?? ?? ??? ??
- ??? ???? ??? ????? ???? ?? ?? ERROR ??

### 13.3 ?? ?? ??

?? ?? ? 6?? ?? ??(??+???)? ???? ?????.

- **?? ??**: `string.ascii_uppercase + string.digits`?? 6? ?? ??
- **?? ??**: UNIQUE ???? ?? ?? ?? ? ???
- **?? ??**:
  1. ????? `/join` ????? 6?? ?? ??
  2. `POST /api/games/join {join_code, user_id}` ??
  3. ???? ?? ?? ? ???? game_players ???? ??, STATE_UPDATE ??????
  4. ?? ??? ? 404 ?? ??
- **URL ??**: `https://yacht.example.com/join?code=ABC123`

## 14. Decisions & Open Questions

### 12.1 Resolved Decisions

| # | 의사결정 항목 | 선택 | 참고 |
|---|-------------|------|------|
| 1 | 플레이어 조기 퇴장 처리 | 자동 PASS 처리, 게임 계속 진행 | 퇴장한 플레이어의 남은 카테고리 0점 처리 |
| 2 | 최소 참여 인원 | 2명 | 게임 생성은 1명 가능, 시작은 2명 이상 필요 |
| 3 | ? ???? ?? | ?? ???? ?? (?? ??) | game-rules.md ??, ??? ??? ?? ? ?? ?? |
| 4 | 게임 시작 방식 | 호스트 명시적 시작 | Waiting Room에서 호스트가 "시작" 버튼 클릭 |
| 5 | 턴 순서 | 무작위 셔플 | 게임 시작 시 플레이어 순서 랜덤화 |
| 6 | ?? ??? ?? ?? | DB ?? (game_results ???) | ?? ??(?? ??, ??) ??? |
| 7 | ?? ?? ?? | 6?? ?? (??+???) | ?? URL ?? ??, game.join_code UNIQUE ?? |
| 8 | ??? ???? ?? ?? | JWT + WebSocket ??? + SESSION_RECOVER | ?? ?? ? ?? ?? ??? ?? |
| 9 | ?? | Rate limiting, ?? ??, CSRF ?? | FastAPI middleware ?? ?? |

### 12.2 Open Questions

(?? ?? ?? ??)
