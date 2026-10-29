"""스텔라이브 다시보기 채널에 새 영상이 올라오면 카카오톡 '나에게 보내기'로 알린다.

환경 변수
  KAKAO_REST_KEY       카카오 앱의 REST API 키
  KAKAO_REFRESH_TOKEN  get_token.py로 받은 리프레시 토큰
  KAKAO_CLIENT_SECRET  (선택) 앱에서 Client Secret을 켠 경우만

실행
  python check.py          새 영상 확인 후 알림
  python check.py --test   카톡 시험 메시지 1개 보내기
  python check.py --dry    카톡 없이 확인만 (seen.json 안 바꿈)
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SEEN_FILE = HERE / "seen.json"
NEW_TOKEN_FILE = HERE / "new_refresh_token.txt"  # 워크플로가 읽고 바로 지움
KEEP = 50  # 채널마다 기억할 영상 수

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Cookie": "SOCS=CAI",  # 유럽 서버에서 동의 화면 건너뛰기
}


def fetch_videos(channel_id):
    # YouTube RSS 피드가 404를 내서(2026-10 확인) 채널의 '동영상' 탭을 직접 읽는다
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    req = urllib.request.Request(url, headers=HEADERS)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html)
    if not m:
        raise RuntimeError("페이지 구조를 읽지 못함")

    videos = []

    def walk(o):
        if isinstance(o, dict):
            if "lockupViewModel" in o:
                v = o["lockupViewModel"]
                title = v.get("metadata", {}).get("lockupMetadataViewModel", {}).get("title", {}).get("content")
                if v.get("contentId") and title:
                    videos.append((v["contentId"], title))
            elif "videoRenderer" in o:
                v = o["videoRenderer"]
                videos.append((v["videoId"], "".join(r["text"] for r in v["title"]["runs"])))
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(json.loads(m.group(1)))
    if not videos:
        raise RuntimeError("영상 목록이 비어 있음")
    seen_ids, out = set(), []
    for vid, title in videos:
        if vid not in seen_ids:
            seen_ids.add(vid)
            out.append({"id": vid, "title": title, "url": f"https://www.youtube.com/watch?v={vid}"})
    return out  # 최신순


def post(url, data, headers=None):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers or {})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def get_access_token():
    data = {
        "grant_type": "refresh_token",
        "client_id": os.environ["KAKAO_REST_KEY"],
        "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
    }
    if os.environ.get("KAKAO_CLIENT_SECRET"):
        data["client_secret"] = os.environ["KAKAO_CLIENT_SECRET"]
    res = post("https://kauth.kakao.com/oauth/token", data)
    # 리프레시 토큰 만료가 1달 안 남으면 새 토큰이 온다 → 워크플로가 Secret을 갱신
    if res.get("refresh_token"):
        NEW_TOKEN_FILE.write_text(res["refresh_token"], encoding="utf-8")
    return res["access_token"]


def send_kakao(token, text, url):
    template = {
        "object_type": "text",
        "text": text[:200],
        "link": {"web_url": url, "mobile_web_url": url},
        "button_title": "영상 보기",
    }
    post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        {"template_object": json.dumps(template, ensure_ascii=False)},
        {"Authorization": f"Bearer {token}"},
    )


def main():
    args = sys.argv[1:]
    if "--test" in args:
        send_kakao(get_access_token(), "[스텔라이브 다시보기 알림] 시험 메시지입니다.",
                   "https://www.youtube.com/@stellive_official")
        print("시험 메시지를 보냈습니다.")
        return

    dry = "--dry" in args
    channels = json.loads((HERE / "channels.json").read_text(encoding="utf-8"))
    seen = json.loads(SEEN_FILE.read_text(encoding="utf-8")) if SEEN_FILE.exists() else {}

    new_items = []  # (이름, 영상)
    for name, cid in channels.items():
        try:
            videos = fetch_videos(cid)
        except Exception as e:
            print(f"{name}: 피드 읽기 실패 ({e})")
            continue
        known = seen.get(cid)
        if known is None:
            # 처음 보는 채널은 지금 있는 영상을 기록만 한다 (알림 폭탄 방지)
            seen[cid] = [v["id"] for v in videos][:KEEP]
            print(f"{name}: 처음 등록, 영상 {len(videos)}개 기록")
            continue
        fresh = [v for v in videos if v["id"] not in known]
        print(f"{name}: 새 영상 {len(fresh)}개")
        for v in reversed(fresh):  # 오래된 것부터
            new_items.append((name, cid, v))

    if new_items and not dry:
        token = get_access_token()
        for name, cid, v in new_items:
            try:
                send_kakao(token, f"[{name} 다시보기]\n{v['title']}", v["url"])
            except Exception as e:
                # 실패한 영상은 기록하지 않아 다음 실행 때 다시 시도
                print(f"{name}: 카톡 전송 실패 ({e})")
                continue
            seen[cid] = ([v["id"]] + seen[cid])[:KEEP]
            print(f"알림 보냄: {name} - {v['title']}")

    if not dry:
        SEEN_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
