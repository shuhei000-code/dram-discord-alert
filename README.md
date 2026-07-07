# DRAM Discord Alert

DRAMを毎週積立している前提で、下落時の買い増し判断をDiscordに通知するPythonアプリです。

## 目的

- 毎日22:40 JSTにDRAMの状況を定期通知
- それ以外の時間は30分ごとにチェック
- 下落率が買い増し基準に到達したときだけ追加通知
- 価格取得元はYahoo Finance

## 買い増しルール

| 直近高値からの下落率 | 通知内容 |
|---:|---:|
| -5% | 1株追加 |
| -10% | 2株追加 |
| -20% | 4株追加 |
| -30%以上 | 5株追加 |

## 通知仕様

### 22:40 JSTの定期通知

毎日22:40に以下を通知します。

- 現在価格
- 前日比
- 直近高値
- 直近高値からの下落率
- 買い増し判定
- 買い増しルール
- 取得元
- 取得時刻

### それ以外の時間帯

30分ごとに価格をチェックします。  
ただし、通知するのは新しい買い増し基準に到達したときだけです。

例：

- -5%に初到達 → 通知
- その後も-5%台 → 通知しない
- -10%に到達 → 通知
- -20%に到達 → 通知
- -5%未満まで回復 → 通知状態をリセット

## GitHub Secrets

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Name | Value |
|---|---|
| `DISCORD_WEBHOOK` | Discord Webhook URL |

## GitHub Actions

`.github/workflows/notify.yml` により実行します。

- `40 13 * * *` → 22:40 JSTの定期通知
- `*/30 * * * *` → 30分ごとの下落チェック

GitHub ActionsのcronはUTC基準です。

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main
```

`.env` には `DISCORD_WEBHOOK` を設定してください。

## 注意

このアプリは投資判断を自動化するものではなく、買い増し候補を通知するだけです。実際の売買判断は、相場状況や資金管理を確認してから行ってください。
