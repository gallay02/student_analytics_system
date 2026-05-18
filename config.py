import os


LLM_CONFIG = {
    "provider": "deepseek",
    "base_url": "https://api.deepseek.com",
    "api_key":  os.getenv("LLM_API_KEY","sk-my_api_key"),# 替换为真实密钥
    "model": "deepseek-v4-flash",
    "temperature": 0.7,
    "max_tokens": 4096
}
SCORE_LEVELS = {
    (90, 100): "优秀",
    (80, 89): "良好",
    (70, 79): "中等",
    (60, 69): "及格",
    (0, 59): "待提高"
}

DB_PATH = "data/student_analytics.db"