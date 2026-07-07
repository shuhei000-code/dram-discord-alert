# DRAM Discord Notifier

Investing.com から DRAM ETF の価格を取得し、Discord Webhook に通知する Python アプリです。  
GitHub Actions により **30分ごと** に自動実行できます。

## フォルダ構成

```text
dram-discord-notifier/
├── .github/
│   └── workflows/
│       └── notify.yml
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── investing.py
│   ├── notifier.py
│   └── main.py
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## 機能

- Investing.com の DRAM ページから価格を取得
- Discord Webhook に通知
- GitHub Actions で30分ごとに実行
- 手動実行にも対応
- エラー発生時も Discord に通知可能
- User-Agent 設定済み

## 事前準備

### 1. Discord Webhook URL を用意

Discord の通知したいチャンネルで以下を行います。

1. チャンネルの歯車アイコンを開く
2. `連携サービス` を開く
3. `ウェブフック` を作成
4. Webhook URL をコピー

### 2. GitHub Secrets に登録

GitHub リポジトリで以下を開きます。

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

以下を追加してください。

| Name | Value |
|---|---|
| `DISCORD_WEBHOOK` | Discord Webhook URL |

## GitHub Actions での自動実行

`.github/workflows/notify.yml` により、30分ごとに実行されます。

```yaml
schedule:
  - cron: "*/30 * * * *"
```

GitHub Actions の cron は UTC 基準です。  
30分ごとの実行なので、日本時間でも毎時 `00分 / 30分` 付近に動きます。

また、GitHub の `Actions` タブから `Run workflow` で手動実行もできます。

## ローカルで実行する方法

### 1. Python 環境を用意

Python 3.12 推奨です。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. `.env` を作成

```bash
cp .env.example .env
```

`.env` の中に Discord Webhook URL を入れます。

```env
DISCORD_WEBHOOK=https://discord.com/api/webhooks/xxxxx/yyyyy
```

### 3. 実行

```bash
python -m src.main
```

## 環境変数

| 変数名 | 必須 | 説明 | デフォルト |
|---|---:|---|---|
| `DISCORD_WEBHOOK` | ✅ | Discord Webhook URL | なし |
| `INVESTING_URL` | 任意 | DRAM価格取得ページ | `https://jp.investing.com/etfs/dram` |
| `DRAM_SYMBOL` | 任意 | 通知に表示するシンボル | `DRAM` |
| `TIMEZONE` | 任意 | 通知時刻のタイムゾーン | `Asia/Tokyo` |
| `NOTIFY_ON_ERROR` | 任意 | エラー時もDiscord通知するか | `true` |
| `DISCORD_MENTION` | 任意 | メンションしたい場合に指定 | 空 |

## Discord通知例

```text
📈 DRAM ETF Price Alert

DRAM: 60.43 USD
取得時刻: 2026-07-08 00:30 JST
Source: Investing.com
```

## 注意点

Investing.com のHTML構造が変更された場合、価格取得に失敗する可能性があります。  
その場合は `src/investing.py` のセレクタや正規表現を調整してください。

GitHub Actions の無料枠や仕様変更により、実行タイミングが数分ずれることがあります。  
また、GitHub Actions は一定期間リポジトリの活動がない場合、スケジュール実行が停止されることがあります。

## ライセンス

MIT License
