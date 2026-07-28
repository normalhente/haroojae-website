#!/usr/bin/env python3
"""히어로 수묵화에서 '운무 통과 마스크'를 만든다.

알파 = 그 행에서 상대적으로 밝은 정도.
  행마다 85퍼센타일(그 깊이의 종이빛)을 기준으로 정규화하므로
  아래로 갈수록 전체가 어두워지는 것에 영향받지 않는다.
  → 능선 몸통(행 안에서 어두움) = 0, 골짜기·종이(행 안에서 밝음) = 1
"""
import sys
from PIL import Image, ImageFilter
import numpy as np

# 행 기준 밝기 대비 이 구간에서 0→1.
# 처음엔 0.55/0.92 였다 — 웬만큼 어두우면 다 차단하니 운무가 '밝은 골짜기만' 채웠다.
# 골짜기는 이미 밝기 194~224 인데 운무가 241 이라 흰 위의 흰색이 되어 존재감이 5~7% 에
# 그쳤고, 그 5~7% 가 미세하게 출렁이니 움직임은 0 에 수렴했다(라이브 실측: 프레임 간
# 평균 ΔL 0.20, 화면의 2% 만 변화).
# 0.22/0.48 은 '가장 짙은 먹 17%' 만 차단한다. 운무가 중간 먹 능선을 덮으므로
# 대비가 생기고 — 존재감도 움직임도 같이 산다. 가장 짙은 근경은 여전히 가리므로 깊이는 유지.
# ── 마스크의 역할이 바뀌었다 ──
# 처음엔 '능선이 운무를 가린다'는 생각으로 0.55/0.92 를 썼다. 웬만큼 어두우면 다 차단하니
# 운무가 밝은 골짜기만 채웠고, 골짜기는 이미 밝아서(194~224) 크림 운무(241)가 흰 위의 흰색이
# 되었다. 존재감 5~7%, 움직임은 그 5~7% 의 미세한 출렁임이라 보이지 않았다.
#
# 원하는 그림은 그 반대다 — 운무가 지나가며 능선이 흐려졌다 드러나는 것. 그러려면 운무가
# 먹을 '덮어야' 한다. 지금 마스크는 가장 짙은 먹 약 10% 만 막아 맨 앞 능선을 운무 앞에
# 세우는 역할만 한다(깊이 유지). 나머지 능선은 운무가 덮고 지나간다.
#
# 같은 문턱을 두 그림에 쓰면 안 된다. 그림마다 대비 분포가 달라 데스크톱 값을 모바일에
# 쓰면 차단이 1%대로 떨어져 맨 앞 능선까지 지워진다. '차단 약 10%' 를 맞추도록 따로 잡는다.
# 문턱을 올릴수록 운무가 능선을 못 덮는다. 어두운 능선의 밝기 변화폭(= '흐려졌다 드러남'의
# 세기)을 실측하면 트레이드오프가 그대로 보인다:
#   0.14/0.34 (차단 7.5%) → 원경 63 / 중경 21 / 근경  7
#   0.08/0.22 (차단 3.0%) → 원경 70 / 중경 45 / 근경 25
#   0.05/0.16 (차단 0.5%) → 원경 71 / 중경 57 / 근경 45   ← 채택
#   0.02/0.10 (차단 0.0%) → 원경 72 / 중경 70 / 근경 69
# 아래쪽은 그림 전체가 짙어서 문턱을 조금만 올려도 근경 띠가 통째로 막힌다.
# 0.05/0.16 은 가장 짙은 먹심만 남겨 맨 앞을 살짝 앞세우면서 효과의 대부분을 가져간다.
THRESH = {
    'hero-ink.jpg':        (0.05, 0.16),   # 차단 0.5%
    'hero-ink-mobile.jpg': (0.12, 0.28),   # 차단 1.3%
}
LO, HI = THRESH['hero-ink.jpg']
BLUR = 6              # 가장자리 부드럽게 (원본 해상도 기준)


def make(src, dst, scale=0.5, lo=None, hi=None):
    import os
    lo, hi = (lo, hi) if lo is not None else THRESH.get(os.path.basename(src), (LO, HI))
    im = Image.open(src).convert('L')
    W, H = im.size
    a = np.asarray(im, dtype=np.float32)

    base = np.percentile(a, 85, axis=1, keepdims=True)   # 행별 종이빛
    base = np.maximum(base, 1.0)
    # 행 기준선 자체를 세로로 부드럽게 (행마다 튀지 않도록)
    k = 41
    pad = np.pad(base[:, 0], (k // 2, k // 2), mode='edge')
    base = np.convolve(pad, np.ones(k) / k, mode='valid')[:, None]

    r = a / base
    alpha = (r - lo) / (hi - lo)
    alpha = np.clip(alpha, 0.0, 1.0)
    alpha = alpha * alpha * (3 - 2 * alpha)              # smoothstep

    m = Image.fromarray((alpha * 255).astype(np.uint8), 'L')
    m = m.filter(ImageFilter.GaussianBlur(BLUR))
    if scale != 1.0:
        m = m.resize((int(W * scale), int(H * scale)), Image.LANCZOS)

    out = Image.new('RGBA', m.size, (255, 255, 255, 255))
    out.putalpha(m)
    out.save(dst, optimize=True)
    return m, (W, H)


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    m, (W, H) = make(src, dst)
    arr = np.asarray(m, dtype=np.float32) / 255.0
    print('src %dx%d -> mask %dx%d' % (W, H, m.size[0], m.size[1]))
    print('alpha 평균 %.3f  0.1미만 %.1f%%  0.9초과 %.1f%%'
          % (arr.mean(), (arr < 0.1).mean() * 100, (arr > 0.9).mean() * 100))
    # 행별 평균 알파 (원본 imgY 기준)
    rows = arr.mean(axis=1)
    print('imgY  meanAlpha')
    step = max(1, len(rows) // 28)
    for i in range(0, len(rows), step):
        print('%5d  %.3f' % (int(i / m.size[1] * H), rows[i]))
