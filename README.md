# iPAS AI 備考 LINE Bot

每天推播 1 題 **L21 模擬題**，協助備考 **iPAS AI 應用規劃師中級能力鑑定**。

## 推播內容

- 20 題精選 L21 模擬題，每天一題、輪播不重複
- 題目含情境描述、四選一、答案與簡要解析
- 考試日期過後自動停止推播

## 推播時間

每日台灣時間 **07:00**（由 GitHub Actions cron 驅動）

## 專案結構

```
├── cards.json       # 20 題 L21 模擬題
├── push.py          # 推播主程式
├── requirements.txt # requests, python-dotenv
└── .github/
    └── workflows/
        └── push.yml # GitHub Actions 排程
```

## 部署方式

1. Fork 或 clone 此 repo
2. 在 GitHub → Settings → Secrets and variables → Actions 新增：
   - `LINE_CHANNEL_ACCESS_TOKEN`（必填）
   - `LINE_USER_ID`（必填，個人推播）
   - `LINE_GROUP_ID`（選填，群組推播）
3. Push 後 GitHub Actions 會依排程自動執行

> LINE 免費方案每月 200 則配額，個人或群組任一目標達到上限時會自動跳過，不中斷流程。

## 本地測試

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt

# 建立 .env 填入 token 與 ID 後執行
python push.py
```
