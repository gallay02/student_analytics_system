import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="sk-31ed2ebd4cb84d2a9ee19321cdf38a6d"
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",   # 或 "deepseek-v4-pro"
    messages=[{"role": "user", "content": "你好"}]
)

print(response.choices[0].message.content)





