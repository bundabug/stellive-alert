"""텔레그램 채팅 ID를 확인하는 도구. 내 PC에서 직접 실행한다.

먼저 텔레그램에서 내 봇에게 아무 메시지(예: 안녕)를 하나 보낸 뒤 실행한다.
  python get_telegram_id.py
"""
import json
import urllib.request

token = input("봇 토큰: ").strip()


def api(method):
    return json.loads(urllib.request.urlopen(
        f"https://api.telegram.org/bot{token}/{method}", timeout=30).read())


me = api("getMe")["result"]
print(f"\n이 토큰의 봇: {me['first_name']} (@{me['username']})  →  https://t.me/{me['username']}")
if api("getWebhookInfo")["result"].get("url"):
    print("이 봇에 웹훅이 걸려 있어 메시지를 읽을 수 없습니다. 웹훅을 지웁니다.")
    api("deleteWebhook")
res = api("getUpdates")

chats = {}
for u in res.get("result", []):
    msg = u.get("message") or u.get("channel_post") or {}
    chat = msg.get("chat")
    if chat:
        chats[chat["id"]] = chat.get("title") or chat.get("first_name") or chat.get("username") or ""

if not chats:
    print(f"\n받은 메시지가 없습니다. 위 링크(@{me['username']})로 들어가 '시작'을 누르고")
    print("아무 메시지나 보낸 뒤 다시 실행하세요. (BotFather 방이 아니라 내 봇 방이어야 합니다)")
else:
    print("\n아래 숫자를 GitHub Secret 'TELEGRAM_CHAT_ID'에 넣으세요.")
    for cid, name in chats.items():
        print(f"  {cid}   ({name})")
