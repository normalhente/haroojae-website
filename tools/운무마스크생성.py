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

LO, HI = 0.55, 0.92   # 행 기준 밝기 대비 이 구간에서 0→1
BLUR = 6              # 가장자리 부드럽게 (원본 해상도 기준)


def make(src, dst, scale=0.5):
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
    alpha = (r - LO) / (HI - LO)
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
