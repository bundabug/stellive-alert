"""카카오 리프레시 토큰을 처음 한 번 받는 도구. 내 PC에서 직접 실행한다.

  python get_token.py
"""
import json
import urllib.parse
import urllib.request

REDIRECT_URI = "https://localhost"

rest_key = input("REST API 키: ").strip()
secret = input("Client Secret (안 켰으면 그냥 Enter): ").strip()

auth_url = "https://kauth.kakao.com/oauth/authorize?" + urllib.parse.urlencode({
    "client_id": rest_key,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": "talk_message",
})
print("\n1) 아래 주소를 브라우저에서 열고 카카오 로그인 후 '동의'를 누르세요.")
print(auth_url)
print("\n2) 그러면 'https://localhost/?code=...' 주소로 바뀌며 '연결할 수 없음' 화면이 뜹니다. 정상입니다.")
redirected = input("   그 주소창의 주소 전체를 복사해 붙여 넣으세요: ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(redirected).query)["code"][0]

data = {
    "grant_type": "authorization_code",
    "client_id": rest_key,
    "redirect_uri": REDIRECT_URI,
    "code": code,
}
if secret:
    data["client_secret"] = secret
req = urllib.request.Request("https://kauth.kakao.com/oauth/token",
                             data=urllib.parse.urlencode(data).encode())
res = json.loads(urllib.request.urlopen(req, timeout=30).read())

print("\n완료! 아래 값을 GitHub Secret 'KAKAO_REFRESH_TOKEN'에 넣으세요. (다른 사람에게 보여주지 마세요)")
print(res["refresh_token"])
