# iPAS AI 備考 LINE Bot

每天自動推播 4 次 AI 知識卡，協助備考 **iPAS AI 應用規劃師中級能力鑑定（L21 + L23）**。

## 推播時間（台灣時間）

07:00 / 12:00 / 17:00 / 21:00，共 80 張卡輪播（L21×40、L23×40）。

## 專案結構

```
├── cards.json       # 80 張知識卡內容
├── push.py          # 推播主程式
├── requirements.txt # requests, python-dotenv
└── .github/
    └── workflows/
        └── push.yml # GitHub Actions 排程（UTC cron）
```

## 部署方式

1. Fork 或 clone 此 repo
2. 在 GitHub → Settings → Secrets and variables → Actions 新增：
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`
3. Push 後 GitHub Actions 會依排程自動執行

## 本地測試

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt

# 建立 .env 填入 token 和 user ID
cp .env.example .env   # 或直接編輯 .env

python push.py
```
