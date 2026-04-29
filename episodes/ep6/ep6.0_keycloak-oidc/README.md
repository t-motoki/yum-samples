# Keycloak + OIDC ローカル認証デモ

## 概要

Keycloak 24 と OIDC（Authorization Code Flow）を使い、ローカル環境だけで認証を動かすミニマムなデモです。
外部サービスは不要で、`docker compose up` と `python app.py` だけで完結します。

構成:
- **Keycloak 24**: IdP（認証サーバー）。Docker で起動
- **Flask**: OIDC クライアント（Web アプリ）。Authlib を使用

Flask アプリはパスワードを知らない。「Keycloak が認証した」という証明（ID トークン）を受け取るだけ、という構成の最小実装です。

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
│   ├── app.py                # Flask アプリ本体（OIDC 関係は2か所だけ）
│   ├── requirements.txt
│   └── templates/
│       ├── index.html        # トップページ
│       └── profile.html      # ログイン後プロフィールページ
└── README.md
```

## 関連エピソード

- ep6.0.1: Keycloak + OIDC — ローカルで動かす認証の話
- ep6.0.2: Keycloak SSO — 複数アプリ間でセッションを共有する（予定）
- ep6.0.3: Keycloak SAML — SAMLプロトコルで認証する（予定）
