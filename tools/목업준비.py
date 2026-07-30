#!/usr/bin/env python3
# 아카이브의 3D 입체 표지 목업(확보 25권)을 웹용 1200px JPEG 으로 리사이즈해
# images/books/mockups/NN.jpg 로 저장한다. 멱등(재실행 안전).
import os, unicodedata
from PIL import Image

ARCHIVE = "/Users/leesunyoung/HRJ_아카이브/하루재북클럽_자료"
OUT = os.path.join(os.path.dirname(__file__), "..", "images", "books", "mockups")
WIDTH = 1200
QUALITY = 82

# 책번호 → 아카이브 상대경로 (root=ARCHIVE). NFC 문자열.
MAP = {
  1:  "표지_추출/01_세로토레_세로토레_표지입체.jpg",
  2:  "표지_추출/02_폴른자이언츠_FG_표지입체.jpg",
  3:  "표지_추출/03_에베레스트정복_에베_표지입체.jpg",
  4:  "표지_추출/04_무상의정복자_정복자_표지입체.jpg",
  5:  "표지_추출/05_꽃의계곡_꽃의계곡_표지입체.jpg",
  6:  "표지_추출/06_나의인생나의철학_나의인생_표지입체.jpg",
  7:  "표지_추출/07_엘리자베스홀리_홀리_표지입체.jpg",
  8:  "표지_추출/08_프리덤클라이머스_FC_표지입체.jpg",
  9:  "표지_추출/09_리카르도캐신_캐신_표지입체.jpg",
  10: "표지_추출/10_캠프식스_Camp6_표지입체.jpg",
  11: "표지_추출/11_하루를살아도호랑이처럼_Tiger_표지입체.jpg",
  12: "표지_추출/12_중국등산사_중국등산사_표지입체.jpg",
  13: "표지_추출/13_일본여성등산사_일본여성등산사_표지입체.jpg",
  14: "표지_추출/14_산책여행_산책여행_표지입체.jpg",
  15: "표지_추출/15_하늘에서추락하다_하늘에서_표지입체.jpg",
  16: "표지_추출/16_마터호른의그림자_마터호른_표지입체.jpg",
  17: "표지_추출/17_어센트_ASCENT_표지입체.jpg",
  18: "표지_추출/18_더타워_TheTower_표지입체.jpg",
  19: "표지_추출/19_프리솔로_프리솔로_표지입체.jpg",
  20: "표지_추출/20_산의비밀_산의비밀_표지입체.jpg",
  25: "0 발간 종결 도서/0-2 아득한 산들(遙かな山やま한국산악회 북클럽용1,300부)/최종(표지 및 본문, 보도자료)/아득한산들_표지입체.jpg",
  30: "0 발간 종결 도서/0-6히말라야 다울라기리 산군의 탐사기/최종 디자인(보도자료)/다울라기리_표지입체.jpg",
  36: "0 발간 종결 도서/0-3 북조선의 산(한국산악회 북클럽회원용)/최종 디자인 및 보도자료/북조선의산_표지입체.jpg",
  38: "0 발간 종결 도서/39 수직의 순례자Pilgrims of the Vertical(오세인)/장선숙 작업/최종/순례자_표지입체.jpg",
  42: "0 발간 종결 도서/38 클라이머즈(The Climbers 인물 사진집)/최종 디자인(장선숙)/클라이머즈_표지입체.jpg",
}

def resolve(relpath):
    # 아카이브가 NFD 로 저장돼 있어 join 후 바로 못 열 수 있다. os.walk 로 NFC 비교해 실제 경로를 찾는다.
    want = unicodedata.normalize('NFC', os.path.join(ARCHIVE, relpath))
    if os.path.exists(want):
        return want
    target = unicodedata.normalize('NFC', relpath)
    for dp, dn, fn in os.walk(ARCHIVE):
        for f in fn:
            full = os.path.join(dp, f)
            if unicodedata.normalize('NFC', full).endswith(target):
                return full
    return None

def main():
    os.makedirs(OUT, exist_ok=True)
    done = 0
    for num, rel in sorted(MAP.items()):
        src = resolve(rel)
        if not src:
            print(f"  !! {num:02d} 원본 못 찾음: {rel}")
            continue
        im = Image.open(src).convert("RGB")
        h = round(im.height * WIDTH / im.width)
        im = im.resize((WIDTH, h), Image.LANCZOS)
        outp = os.path.join(OUT, f"{num:02d}.jpg")
        im.save(outp, "JPEG", quality=QUALITY)
        print(f"  {num:02d}.jpg  {WIDTH}x{h}  {round(os.path.getsize(outp)/1024)}KB")
        done += 1
    print(f"완료: {done}/{len(MAP)}")

if __name__ == "__main__":
    main()
