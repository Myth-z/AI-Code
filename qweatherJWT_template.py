import json
import base64
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ======================= 配置你的信息 =======================
# 直接粘贴你的 PEM 私钥（包括 BEGIN 和 END 行）
# 请从和风天气控制台获取你的私钥，并替换下面的内容
PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_CONTENT_HERE
-----END PRIVATE KEY-----"""

PROJECT_ID = "YOUR_PROJECT_ID"    # sub: 项目ID（在和风天气控制台查看）
KID = "YOUR_CREDENTIAL_ID"        # kid: 凭据ID（在和风天气控制台查看）
EXPIRES_IN_SECONDS = 3600         # Token有效期：1小时（建议不要超过24小时）
# ==========================================================

def base64url_encode(data):
    """Base64URL 编码（无填充）"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

# 1. 加载 PEM 私钥
try:
    private_key: Ed25519PrivateKey = serialization.load_pem_private_key(
        PRIVATE_KEY_PEM.encode('utf-8'),
        password=None  # 如果私钥加密了，请填写密码
    )
except Exception as e:
    raise ValueError(f"私钥加载失败，请检查格式: {e}")

# 2. 构造 JWT Header 和 Payload
header = {"alg": "EdDSA", "kid": KID}
now = int(time.time())
payload = {
    "sub": PROJECT_ID,
    "iat": now,
    "exp": now + EXPIRES_IN_SECONDS
}

# 3. Base64URL 编码 Header 和 Payload
encoded_header = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
encoded_payload = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

# 4. 签名内容：header.payload
signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
signature = private_key.sign(signing_input)
encoded_signature = base64url_encode(signature)

# 5. 生成最终 JWT Token
jwt_token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"

# 输出结果
print("\n✅ 成功生成 JWT Token！")
print(f"\n🔑 Authorization Header:")
print(f"Bearer {jwt_token}")

print("\n📎 调用 API 示例（curl）:")
print(f'''curl.exe -H "Authorization: Bearer {jwt_token}" --compressed https://devapi.qweather.com/v7/weather/now?location=101010100 -o -''')

print("\n🔍 提示：")
print("• 可在 https://dev.qweather.com/jwt-validator 验证 Token")
print("• 确保系统时间准确")
print("• API Host 白名单已添加 devapi.qweather.com")

print("\n⚠️  配置说明：")
print("• 请在和风天气控制台 (https://console.qweather.com) 获取你的凭据")
print("• 将 YOUR_PRIVATE_KEY_CONTENT_HERE 替换为你的私钥内容")
print("• 将 YOUR_PROJECT_ID 替换为你的项目ID")
print("• 将 YOUR_CREDENTIAL_ID 替换为你的凭据ID")
print("• 配置完成后，删除此配置说明部分")
