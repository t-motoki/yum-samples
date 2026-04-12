# ep6.0.3 Keycloak SAML Identity Brokering

## 概要

SAML Identity Brokering とは、Keycloak が SAML プロトコルで外部 IdP と連携し、その認証結果を別のプロトコル（OIDC など）に変換して渡す仕組みです。

このデモでは以下の構成を動かします。

```
Flask App（OIDC・コード変更なし）
        │ OIDC
        ▼
Keycloak A (:8080) ── SAML ──▶ Keycloak B (:8081)
  [ブローカー]                    [外部 IdP]
```

**このデモで確認できること:**
- Flask アプリは OIDC のまま、一切コードを変えずに動く
- ログイン画面は Keycloak B（外部 SAML IdP）にリダイレクトされる
- Keycloak A が SAML と OIDC の通訳として機能する

「クライアントを変えなくていい」——これが SAML Brokering の価値です。既存の OIDC アプリをそのままに、認証バックエンドを SAML IdP に切り替えられます。

---

## 起動手順

### 1. Keycloak A・B を起動する

```bash
docker compose up -d
```

初回は Keycloak の起動に 1 分程度かかります。以下のコマンドで起動完了を確認してください。

```bash
# Keycloak A が起動したか確認
curl -s http://localhost:8080/realms/demo | python3 -m json.tool

# Keycloak B が起動したか確認
curl -s http://localhost:8081/realms/idp | python3 -m json.tool
```

### 2. Flask アプリを起動する

`ep6.0.3_keycloak-saml-brokering/app` ディレクトリで以下を実行します。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### 3. ログインフローを確認する

ブラウザで http://localhost:5000 を開き、「ログイン」をクリックします。

Keycloak A のログイン画面に遷移したあと、「External SAML IdP (Keycloak B)」ボタンが表示されます。これをクリックすると Keycloak B のログイン画面にリダイレクトされます。

Keycloak B 側のユーザー（samluser / password）でログインすると、Flask アプリに戻りプロフィールが表示されます。

---

## テストユーザー

Keycloak B（外部 SAML IdP）側に登録されているユーザーです。

| 項目 | 値 |
|------|-----|
| ユーザー名 | samluser |
| パスワード | password |
| メール | samluser@example.com |

---

## 管理画面

| サーバー | URL | ユーザー名 | パスワード |
|----------|-----|-----------|-----------|
| Keycloak A（ブローカー） | http://localhost:8080 | admin | admin |
| Keycloak B（外部 IdP） | http://localhost:8081 | admin | admin |

Keycloak A の管理画面では「Identity Providers」メニューから SAML IdP の設定を確認できます。

---

## ファイル構成

```
ep6.0.3_keycloak-saml-brokering/
├── README.md
├── docker-compose.yml
├── keycloak-a/
│   └── realm-export.json   # demo レルム（OIDC ブローカー）
├── keycloak-b/
│   └── realm-export.json   # idp レルム（外部 SAML IdP）
└── app/
    ├── app.py              # ep6.0.1 と完全に同じ（変更なし）
    ├── requirements.txt
    └── templates/
        ├── index.html
        └── profile.html
```

---

## 仕組みの補足

Keycloak A は「通訳」として動いています。

1. Flask アプリが OIDC で Keycloak A に認証を要求する
2. Keycloak A は SAML リクエストを生成し、Keycloak B（外部 IdP）に転送する
3. ユーザーが Keycloak B でログインする
4. Keycloak B が SAML レスポンスを Keycloak A に返す
5. Keycloak A が SAML レスポンスを解釈し、OIDC トークンを Flask アプリに返す

Flask アプリから見ると「OIDC で Keycloak A とやり取りしている」だけです。SAML の存在を知る必要はありません。
