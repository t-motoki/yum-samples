# Keycloak OIDC デモ — React + TypeScript 版

## 概要

ep6.0（Flask + Python）の OIDC クライアントを React + TypeScript + Vite で作り直したおまけ回。
Flask 版はサーバーサイドで認証コードを処理しクライアントシークレットが必要だったが、
SPA ではシークレットをブラウザに置けないため **PKCE（Proof Key for Code Exchange）** を使う。
`oidc-client-ts` がトークン管理・リフレッシュを担い、TypeScript の型でクレームを安全に扱える。

## 起動手順

```bash
# 1. Keycloak を起動
docker compose up -d

# 2. React アプリの依存関係をインストール
cd app && npm install

# 3. 開発サーバーを起動
npm run dev
```

ブラウザで http://localhost:5173 を開く。

## テストユーザー

| 項目 | 値 |
|------|-----|
| ユーザー名 | testuser |
| パスワード | password |

## Keycloak 管理画面

- URL: http://localhost:8080
- 管理者: admin / admin

## Flask 版との主な違い

- **publicClient + PKCE**: クライアントシークレット不要。code_verifier / code_challenge の生成は `oidc-client-ts` が自動で行う
- **TypeScript の型**: `KeycloakProfile` インターフェースでクレームを型安全に扱える。Python では dict アクセスで実行時エラーのリスクがあった
- **oidc-client-ts がトークン管理・リフレッシュを担う**: Flask 版ではセッションに手動で保存していたトークンを、ライブラリが sessionStorage で一元管理する
- **SPA のルーティング**: React Router でページ遷移を管理。サーバーへのリクエストは発生しない

## ファイル構成

```
.
├── docker-compose.yml          Keycloak 24 on :8080
├── keycloak/
│   └── realm-export.json       demo realm（flask-app + react-app クライアント）
└── app/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx            エントリポイント・MUI テーマ設定
        ├── App.tsx             ルーティング定義
        ├── auth/
        │   ├── oidcConfig.ts   UserManager 設定（PKCE 有効）
        │   └── types.ts        KeycloakProfile 型定義
        ├── pages/
        │   ├── LoginPage.tsx   ログイン・ログアウト
        │   ├── CallbackPage.tsx 認証コードをトークンに交換
        │   └── ProfilePage.tsx クレーム一覧表示
        └── components/
            └── ProfileCard.tsx MUI カードコンポーネント
```
