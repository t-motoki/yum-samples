# ep6.0.2 — Keycloak SSO デモ

## 概要

シングルサインオン（SSO）とは、1回のログインで複数のアプリにアクセスできる仕組みです。
Keycloak がセッションを一元管理するため、各アプリは個別にパスワードを確認しません。

このデモでは2つの Flask アプリ（App A / App B）を起動します。
App A でログインすると、App B でも認証画面が出ずにそのまま入れることを確認できます。

---

## 起動手順

### 1. Keycloak を起動する

```bash
docker compose up -d
```

Keycloak が起動するまで数十秒かかります。
http://localhost:8080 にアクセスして管理画面が表示されたら準備完了です。

### 2. App A を起動する（ターミナル 1）

```bash
cd app-a
pip install -r requirements.txt
python app.py
```

http://localhost:5000 で起動します。

### 3. App B を起動する（ターミナル 2）

```bash
cd app-b
pip install -r requirements.txt
python app.py
```

http://localhost:5001 で起動します。

---

## SSO を確認する

1. http://localhost:5000 を開く（App A）
2. 「ログイン」をクリック → Keycloak のログイン画面が表示される
3. テストユーザー（`testuser` / `password`）でログインする
4. App A のトップに「ログイン中」と表示される
5. ページ下部の「App B を開く」リンクをクリックする
6. App B のトップが開く（この時点では「ログインしていません」）
7. App B の「ログイン」をクリックする → Keycloak にリダイレクトされる
8. **Keycloak のログイン画面が出ずに、そのまま App B のプロフィールページに遷移する** ← SSO

> Keycloak が既存セッションを認識するため、2回目以降のログインはパスワード入力をスキップします。
> App B のトップページは Flask の独立したセッション Cookie を使っているため「ログインしていません」と表示されますが、「ログイン」ボタンを押した瞬間に SSO が働きます。

## シングルログアウトを確認する

1. App A または App B のいずれかで「ログアウト」をクリックする
2. もう一方のアプリに戻り、ページをリロードする
3. 「ログインしていません」の表示に変わる ← Keycloak セッションが切れたため

---

## テストユーザー

| 項目 | 値 |
|------|-----|
| ユーザー名 | testuser |
| パスワード | password |

---

## Keycloak 管理画面

| 項目 | 値 |
|------|-----|
| URL | http://localhost:8080 |
| ユーザー名 | admin |
| パスワード | admin |

レルム `demo` の Clients に `flask-app`（App A 用）と `flask-app-b`（App B 用）が登録されています。

---

## ファイル構成

```
ep6.0.2_keycloak-sso/
├── README.md
├── docker-compose.yml          # Keycloak 24 (:8080)
├── keycloak/
│   └── realm-export.json       # レルム定義（2クライアント登録済み）
├── app-a/                      # App A (:5000)
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       ├── index.html
│       └── profile.html
└── app-b/                      # App B (:5001)
    ├── app.py
    ├── requirements.txt
    └── templates/
        ├── index.html
        └── profile.html
```
