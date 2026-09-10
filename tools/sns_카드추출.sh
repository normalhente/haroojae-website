#!/bin/bash
# SNS 카드 초안(_sns_*.html)의 카드를 1080×1350 PNG 로 뽑는다. 설치할 것 없다.
#
#   tools/sns_카드추출.sh _sns_철학초안.html
#   tools/sns_카드추출.sh _sns_철학초안.html ~/Desktop/하루재_첫게시물
#
# 원리
#   초안에 ?only=N 모드를 넣어 두었다. 카드 한 장만 원본 크기로 남기고 페이지
#   껍데기를 지운다. 그 주소를 크롬 헤드리스가 1080×1350 창으로 찍으면 카드가
#   그대로 나온다. Playwright 같은 별도 설치가 필요 없다.
#
# 전제
#   - 로컬 서버(포트 8080)가 떠 있어야 한다. 표지·수묵화가 상대경로라 file:// 로는 안 뜬다
#   - 어도비 폰트 킷을 받아야 산돌명조로 나온다 → 네트워크 필요
set -euo pipefail

HTML="${1:-}"
OUT="${2:-$HOME/Desktop/하루재_SNS}"
W=1080; H=1350
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

[ -z "$HTML" ] && { echo "사용법: $0 <초안.html> [저장폴더]" >&2; exit 1; }
[ -x "$CHROME" ] || { echo "크롬을 찾지 못했다: $CHROME" >&2; exit 1; }
curl -sS -o /dev/null "http://localhost:8080/" || { echo "로컬 서버(8080)가 꺼져 있다. 미리보기를 먼저 띄울 것" >&2; exit 1; }

ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$HTML")
# .slot 을 센다. 'class="card "' 로 세면 class="card" 인 카드(2·3번)를 놓친다
N=$(curl -sS "http://localhost:8080/$ENC" | grep -c 'class="slot"' || true)
[ "$N" -eq 0 ] && { echo "카드를 찾지 못했다" >&2; exit 1; }

mkdir -p "$OUT"
STEM=$(basename "$HTML" .html | sed 's/^_//')
echo "카드 ${N}장 · ${W}×${H} · → $OUT"

for i in $(seq 1 "$N"); do
  F="$OUT/${STEM}_$(printf '%02d' "$i").png"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 \
    --window-size="${W},${H}" \
    --virtual-time-budget=8000 \
    --screenshot="$F" \
    "http://localhost:8080/$ENC?only=$i" >/dev/null 2>&1
  if [ -f "$F" ]; then
    SIZE=$(python3 -c "
from struct import unpack
d=open('$F','rb').read(33)
print('%dx%d' % unpack('>II', d[16:24]))
" 2>/dev/null || echo '?')
    KB=$(( $(stat -f%z "$F") / 1024 ))
    echo "  $i/$N  $(basename "$F")  ${SIZE}  ${KB}KB"
  else
    echo "  $i/$N  실패" >&2
  fi
done
echo "끝. 인스타에는 1→${N} 순서로 올릴 것"
