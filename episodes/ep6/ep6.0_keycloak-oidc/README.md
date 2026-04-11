# Keycloak OIDC ローカル SSO デモ

## 概要

Keycloak 24 と OIDC を使い、ローカル環境だけで SSO（シングルサインオン）を動かすミニマムなデモです。
外部サービスは不要で、`docker compose up` と `python app.py` だけで完結します。

構成:
- **Keycloak 24**: IdP（認証サーバー）。Docker で起動
- **Flask**: OIDC クライアント（Web アプリ）。Authlib を使用

## 起動手順

```bash
# Keycloak 起動（初回はレルム自動インポート）
docker compose up -d

# Keycloak が起動するまで待つ（30秒ほど）
# http://localhost:8080 でアクセス確認

# Flask アプリ起動
cd app
pip install -r requirements.txt
python app.py

# ブラウザで http://localhost:5000 を開く
```

## テストユーザー

| 項目 | 値 |
|------|----|
| ユーザー名 | `testuser` |
| パスワード | `password` |

## Keycloak 管理画面

URL: `http://localhost:8080`

| 項目 | 値 |
|------|----|
| ユーザー名 | `admin` |
| パスワード | `admin` |

管理画面から `demo` レルムを選択すると、クライアント・ユーザーの設定を確認できます。

## ファイル構成

```
ep6.0_keycloak-oidc/
├── docker-compose.yml        # Keycloak コンテナ定義
├── keycloak/
│   └── realm-export.json     # レルム設定（起動時に自動インポート）
├── app/
│   ├── app.py                # Flask アプリ本体
│   ├── requirements.txt
│   └── templates/
│       ├── index.html        # トップページ
│       └── profile.html      # ログイン後プロフィールページ
└── README.md
```
