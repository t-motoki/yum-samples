# Playwright でブラウザスクリーンショットをギャラリー画像として使う

## 背景

ターミナル操作画面や Web アプリの動作をギャラリーに表示したいとき、Pillow で描画した模擬画像より本物のブラウザ画面の方が伝わりやすい。
WSL2 環境からでも Playwright でヘッドレスブラウザを操作してスクリーンショットを撮れる。

## 手順

### 1. インストール

```bash
pip install playwright
playwright install chromium

# WSL2 の場合、システムライブラリが不足していることがある
# venv 内の playwright を使って deps をインストールする（sudo が必要）
sudo /path/to/.venv/bin/playwright install-deps chromium
```

エラー例:
```
Error: libnspr4.so: cannot open shared object file
```
→ `playwright install-deps chromium` で解決。

### 2. スクリプト例

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})

    # Flask アプリのページをキャプチャ
    page.goto("http://localhost:5000")
    page.screenshot(path="01_top_loggedout.png")

    # ログインボタンをクリックして Keycloak 画面をキャプチャ
    page.click("a[href='/login']")
    page.wait_for_url("**/realms/**")
    page.screenshot(path="02_keycloak_login.png")

    # ログイン後のページをキャプチャ
    page.fill("#username", "testuser")
    page.fill("#password", "password")
    page.click("#kc-login")
    page.wait_for_url("**/profile")
    page.screenshot(path="03_profile.png")

    browser.close()
```

### 3. 注意点

- 外部サービスが起動している必要がある（例: Flask + Keycloak）
- ヘッドレスなので、WSL2 のディスプレイ設定は不要
- ページ遷移後は `wait_for_url()` や `wait_for_selector()` で待機してからキャプチャすること

## ギャラリーへの組み込み

単一ファイルも `<!-- gallery: path/to/file.png -->` でギャラリーとして表示できる。
画像はシーンごとに1枚ずつ個別の scene ブロックに分けた方がテンポが作りやすい。

```markdown
<!-- gallery: inputs/episodes/ep6.0.1/gallery_login/01_top_loggedout.png -->

<!-- pause: 1.0 -->

<!-- gallery: inputs/episodes/ep6.0.1/gallery_login/02_keycloak_login.png -->
```

## 関連エピソード

- ep6.0.1: Keycloak + OIDC でこのアプローチを初めて使用
