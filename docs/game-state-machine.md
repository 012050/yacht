# Game State Machine

## 1. States

| State | Description | Valid Transitions |
|-------|-------------|-------------------|
| `WAITING` | 게임 생성, 플레이어 참여 완료, 호스트의 시작 대기 | → PLAYING |
| `PLAYING` | 게임 진행 중 (플레이어 턴 교대) | → FINISHED |
| `FINISHED` | 모든 플레이어의 12개 카테고리 완료 | (none, terminal state) |

## 2. State Transitions

| From | To | Trigger | Action |
|------|-----|---------|--------|
| WAITING | PLAYING | 호스트가 "시작" 버튼 클릭 | 플레이어 순서 무작위 셔플, 1라운드 시작, 첫 플레이어 턴 시작 |
| PLAYING | FINISHED | 모든 플레이어의 12개 카테고리 모두 채움 | 최종 점수 계산, 승자 결정 |
| PLAYING | PLAYING | 턴 전환 (현재 플레이어의 턴 종료) | 다음 플레이어의 턴 시작 |

## 3. Turn Flow (within PLAYING state)

각 플레이어의 턴은 다음 단계로 구성됩니다:

### 3.1 ROLLING Phase

1. **1회차 던짐**: 5개 주사위 모두 던짐
2. **유지(Keep) 선택**: 유지할 주사위 선택 (선택 사항, 1회차 후)
3. **2회차 던짐**: 유지하지 않은 주사위만 재던짐
4. **유지(Keep) 선택**: 유지할 주사위 선택 (선택 사항, 2회차 후)
5. **3회차 던짐**: 유지하지 않은 주사위만 재던짐 (최종 던짐)

- 매 던짐 후 WebSocket을 통해 주사위 결과를 모든 플레이어에게 브로드캐스트
- 3회 던진 후 또는 플레이어가 조기 종료 선택 후 → SELECTING Phase로 이동

### 3.2 SELECTING Phase

- **유효한 카테고리 선택**: 점수 계산 → 기록 → 턴 종료 → 다음 플레이어
- **PASS 선택**: 해당 카테고리 0점 기록 → 턴 종료 → 다음 플레이어
- **60초 타임아웃**: 현재 주사위 상태로 자동 카테고리 선택 (보관한 주사위 유지, 남은 주사위를 1회만 자동 굴린 후 가장 높은 점수 카테고리 자동 기록) → 턴 종료 → 다음 플레이어

## 4. Edge Cases

### 4.1 플레이어 조기 퇴장

- **조건**: 플레이어가 게임 도중 WebSocket 연결 끊김 또는 명시적 퇴장
- **처리**:
  - 퇴장한 플레이어의 남은 (채워지지 않은) 카테고리: 자동 PASS (0점 처리)
  - 현재 퇴장한 플레이어의 턴인 경우: 즉시 PASS 처리, 다음 플레이어 턴으로 이동
  - 남은 플레이어들이 게임 계속 진행
- **마지막 플레이어도 퇴장 시**: 게임 종료 (FINISHED 상태), 모든 점수 무효

### 4.2 턴 타임아웃

- **조건**: 현재 플레이어의 턴이 60초 경과
- **처리**: 현재 주사위 상태로 자동 카테고리 선택 진행 (보관한 주사위는 그대로 두고, 남은 주사위는 자동으로 굴리고, 가장 높은 점수의 카테고리에 자동 기록). 자동 기록 시 플레이어가 직접 선택한 것과 동일한 점수가 기록됩니다.
- **타이머 재시작**: 다음 플레이어 턴 시작 시 60초 타이머 리셋

### 4.3 호스트 퇴장

- **WAITING 상태**: 호스트가 퇴장 시, 남은 플레이어 중 첫 번째 플레이어가 새 호스트로 변경. "시작" 권한 이전
- **PLAYING 상태**: 게임 계속 진행, 호스트 역할은 데이터 저장 목적으로만 필요 (특권 없음)

### 4.4 동시 카테고리 선택 방지

- **조건**: 현재 플레이어가 아닌 플레이어가 카테고리 선택 시도
- **처리**: ERROR 메시지 반환, 요청 거부
- **검증**: 서버에서 `current_player_id` 확인 후 처리

### 4.5 이미 채운 카테고리 재선택 방지

- **조건**: 플레이어가 이미 점수를 기록한 카테고리 선택
- **처리**: ERROR 메시지 반환, 다른 카테고리 선택 요청


### 4.6 타임아웃 자동 선택 시 충돌 카테고리

- **조건**: 타임아웃 자동 선택 결과로 계산된 최고 점수 카테고리가 이미 다른 플레이어가 채운 경우
- **처리**: 차순위 가장 높은 점수 카테고리 중 미사용인 카테고리 자동 선택. 만약 모든 카테고리가 이미 채워진 경우 PASS (0점) 처리
## 5. Game Data Structure

```python
from enum import Enum
from typing import Optional

class GameState(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

class PlayerInfo:
    user_id: str
    display_name: str
    join_order: int          # 참여 순서 (1-based)
    is_host: bool

class GameSession:
    id: str                          # Game ID (UUID)
    state: GameState                 # WAITING, PLAYING, FINISHED
    host_user_id: str               # Current host
    players: list[PlayerInfo]       # Player list (shuffled when game starts)
    current_player_index: int       # Current turn player index (0-based)
    current_round: int              # Current round (1-12)
    current_dice: list[int] | None  # Current dice values (during rolling)
    rolls_left: int                 # Rolls remaining for current turn (1-3)
    scoreboards: dict[str, dict]    # Player ID -> {category: score}
    created_at: datetime            # Game creation time
    started_at: datetime | None     # Game start time
    finished_at: datetime | None    # Game end time
```

## 6. Round Progression

- **1라운드**: 모든 플레이어가 1번씩 턴 수행 (각자 12개 카테고리 중 1개 채움)
- **2라운드**: 모든 플레이어가 2번씩 턴 수행
- ...
- **12라운드**: 모든 플레이어가 12번씩 턴 수행 (모든 카테고리 완료)
- **총 턴 수**: 플레이어 수 × 12

라운드 전환 조건: 마지막 플레이어가 턴 종료 시 다음 라운드 시작

## 7. Winning Condition

- 모든 12개 카테고리 완료 후 최종 점수 비교
- **최종 점수** = 상단 점수 합 + 하단 점수 합 + 보너스 (상단 >= 63 시 +35)
- 점수가 높은 플레이어 승리
- 동점 시 무승부 처리

## 8. Timer Management

| Event | Timer Action |
|-------|--------------|
| 턴 시작 | 60초 타이머 시작 |
| 주사위 재던짐 | 60초 타이머 리셋 |
| 턴 종료 (카테고리 선택) | 타이머 중지 |
| ???? (60? ??) | ?? ???? ?? (?? ??), ??? ?? |
| 다음 플레이어 턴 시작 | 60초 타이머 재시작 |
