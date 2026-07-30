#!/usr/bin/env python3
"""표지 이미지에서 CSS 3D 책의 '책등' 색을 뽑는다.

책등은 표지 왼쪽 끝의 연장이다. 왼쪽 6% 열의 중앙값을 쓰되(로고·띠 같은
국소 요소에 끌려가지 않도록 평균이 아니라 중앙값), 실제 책등은 앞면보다
빛을 덜 받으므로 조금 어둡게 눌러 준다.
"""
import glob, json, sys
import numpy as np
from PIL import Image

DARKEN = 0.82          # 책등은 앞면보다 어둡다
COL_FRAC = 0.06        # 왼쪽 6% 열


def spine_color(path):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im, dtype=np.float32)
    w = max(2, int(a.shape[1] * COL_FRAC))
    col = a[:, :w, :].reshape(-1, 3)
    med = np.median(col, axis=0) * DARKEN
    return tuple(int(round(v)) for v in np.clip(med, 0, 255))


if __name__ == '__main__':
    out = {}
    for f in sorted(glob.glob('images/books/*.jpg')) + sorted(glob.glob('images/books/*.png')):
        try:
            out[f] = '#%02X%02X%02X' % spine_color(f)
        except Exception as e:
            print('건너뜀 %s (%s)' % (f, e), file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=1))
