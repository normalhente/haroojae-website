#!/usr/bin/env python3
"""SNS 카드 초안(_sns_*.html)의 카드를 1080×1080 PNG 로 뽑는다.

    python3 tools/sns_카드추출.py _sns_철학초안.html
    python3 tools/sns_카드추출.py _sns_철학초안.html -o ~/Desktop/하루재_첫게시물

왜 필요한가
  초안은 실제 1080×1080 으로 짜고 화면에는 36% 로 축소해 보여준다.
  브라우저 캡처로 뜨면 축소된 크기로 잡혀 인스타에 올릴 수 없다.
  이 스크립트는 축소를 풀고 카드 하나씩 원본 크기로 저장한다.

전제
  - 로컬 서버가 떠 있어야 한다 (.claude/launch.json 의 haroojae-website, 포트 8080).
    표지·수묵화 이미지가 상대경로라 file:// 로 열면 안 뜬다.
  - Playwright 필요: pip3 install --user playwright && python3 -m playwright install chromium
  - 어도비 폰트 킷을 받아야 산돌명조로 나온다 → 네트워크 연결 필요.
    킷이 안 붙으면 폴백(본명조)으로 찍히므로 스크립트가 경고한다.
"""
import argparse, asyncio, os, sys, urllib.parse, urllib.request

PORT = 8080
CARD = 1080


def server_alive() -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/", timeout=3)
        return True
    except Exception:
        return False


async def run(html_name: str, outdir: str, scale: int) -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright 가 없다. 설치:\n"
              "  pip3 install --user playwright\n"
              "  python3 -m playwright install chromium", file=sys.stderr)
        return 1

    url = f"http://localhost:{PORT}/{urllib.parse.quote(html_name)}"
    os.makedirs(outdir, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            viewport={"width": CARD + 200, "height": CARD + 200},
            device_scale_factor=scale,
        )
        await page.goto(url, wait_until="networkidle")

        # 어도비 킷이 붙었는지 — 안 붙으면 폴백 서체로 찍힌다
        kit_ok = await page.evaluate(
            "document.documentElement.className.includes('wf-sandoll-myeongjoneo1-n4-active')")
        if not kit_ok:
            print("⚠️  어도비 폰트 킷이 활성화되지 않았다. 폴백 서체(본명조)로 찍힌다.", file=sys.stderr)
            print("    네트워크를 확인하고 다시 실행할 것.", file=sys.stderr)

        # 축소(transform: scale)를 풀어 원본 1080 으로 만든다
        await page.evaluate("""() => {
            document.querySelectorAll('.card').forEach(c => { c.style.transform = 'none'; });
            document.querySelectorAll('.shell').forEach(s => {
                s.style.width = '1080px'; s.style.height = '1080px';
            });
        }""")
        await page.wait_for_timeout(600)

        cards = await page.query_selector_all(".card")
        if not cards:
            print("카드를 찾지 못했다 (.card 선택자 확인)", file=sys.stderr)
            await browser.close()
            return 1

        stem = os.path.splitext(os.path.basename(html_name))[0].lstrip("_")
        for i, card in enumerate(cards, 1):
            path = os.path.join(outdir, f"{stem}_{i:02d}.png")
            await card.screenshot(path=path)
            size = os.path.getsize(path) / 1024
            box = await card.bounding_box()
            print(f"  {i}/{len(cards)}  {os.path.basename(path)}"
                  f"  {int(box['width'])}×{int(box['height'])}"
                  f"  ({int(box['width'])*scale}×{int(box['height'])*scale}px 저장)  {size:.0f}KB")

        await browser.close()
    print(f"\n{len(cards)}장 저장 → {outdir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="SNS 카드 초안을 1080×1080 PNG 로 뽑는다")
    ap.add_argument("html", help="초안 파일명 (예: _sns_철학초안.html)")
    ap.add_argument("-o", "--out", default="~/Desktop/하루재_SNS", help="저장 폴더")
    ap.add_argument("-s", "--scale", type=int, default=2,
                    help="배율 (기본 2 = 2160px. 인스타 권장 1080 이면 1)")
    a = ap.parse_args()

    if not server_alive():
        print(f"로컬 서버(localhost:{PORT})가 꺼져 있다.\n"
              f"미리보기를 먼저 띄울 것 — .claude/launch.json 의 haroojae-website", file=sys.stderr)
        return 1

    return asyncio.run(run(a.html, os.path.expanduser(a.out), a.scale))


if __name__ == "__main__":
    sys.exit(main())
