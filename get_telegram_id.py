"""텔레그램 채팅 ID를 확인하는 도구. 내 PC에서 직접 실행한다.

먼저 텔레그램에서 내 봇에게 아무 메시지(예: 안녕)를 하나 보낸 뒤 실행한다.
  python get_telegram_id.py
"""
import json
import urllib.request

token = input("봇 토큰: ").strip()
res = json.loads(urllib.request.urlopen(
    f"https://api.telegram.org/bot{token}/getUpdates", timeout=30).read())

chats = {}
for u in res.get("result", []):
    msg = u.get("message") or u.get("channel_post") or {}
    chat = msg.get("chat")
    if chat:
        chats[chat["id"]] = chat.get("title") or chat.get("first_name") or chat.get("username") or ""

if not chats:
    print("\n받은 메시지가 없습니다. 텔레그램에서 봇에게 아무 메시지나 보낸 뒤 다시 실행하세요.")
else:
    print("\n아래 숫자를 GitHub Secret 'TELEGRAM_CHAT_ID'에 넣으세요.")
    for cid, name in chats.items():
        print(f"  {cid}   ({name})")
