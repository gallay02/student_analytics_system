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

# 预设科目列表
PRESET_SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "信息技术"]

# 数据库基础路径（用户隔离后动态生成）
DB_BASE_PATH = "data"