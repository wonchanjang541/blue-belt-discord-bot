# 푸른 복대 디스코드 강화 봇

푸른 복대 이미지에 실제 능력치를 다시 그려서 보여주는
`혼돈의 주문서 60%` 디스코드 시뮬레이터입니다.

## 현재 규칙

- 정옵: 주스텟 10 / 공격력 2 / 마력 2 / 마법방어력 50
- 업그레이드 가능 횟수: 3
- 혼돈의 주문서 성공률: 60%
- 성공 시 주스텟/공격력/마력/마법방어력이 각각 독립적으로 -5 ~ +5
- 실패 시 능력치 변화 없음
- 성공/실패 모두 업횟 1 차감
- 기본 설정상 능력치는 0 미만으로 내려가지 않음
- 사람마다 자기 장비 상태를 SQLite DB에 따로 저장

## 명령어

- `/강화` : 버튼이 달린 강화창 열기
- `/내장비` : 내 현재 장비 보기
- `/강화초기화` : 정옵 상태로 되돌리기
- `/강화랭킹` : 공격력 기준 TOP 10

강화창 버튼:
- `📜 혼줌 60% 사용`
- `🎒 내 장비 보기`
- `🔄 초기화`

## 설치

Python 3.11 이상 권장.

```bash
pip install -r requirements.txt
```

Discord Developer Portal에서 봇을 만든 뒤 서버에 초대하세요.
OAuth2 URL Generator에서 `bot`, `applications.commands`를 체크하면 됩니다.

봇 토큰은 코드에 직접 넣지 말고 환경변수로 실행하세요.

### Windows PowerShell

```powershell
$env:DISCORD_BOT_TOKEN="여기에_봇_토큰"
python bot.py
```

### Windows CMD

```cmd
set DISCORD_BOT_TOKEN=여기에_봇_토큰
python bot.py
```

## 이미지 위치 조절

`bot.py`의 `render_item_png()` 안에 있는 좌표가
현재 첨부한 315x385 푸른 복대 이미지에 맞춰져 있습니다.

글씨 위치나 크기를 바꾸고 싶으면:
- `ys = [...]`
- `FONT_16 = get_font(16)`
- `draw.rectangle(...)`

부분을 조정하면 됩니다.

## 중요

봇 토큰은 절대로 디스코드 채팅이나 다른 사람에게 공개하지 마세요.
토큰이 노출되면 Discord Developer Portal에서 즉시 재발급하세요.
