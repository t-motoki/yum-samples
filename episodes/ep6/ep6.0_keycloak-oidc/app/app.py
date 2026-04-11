import os
from flask import Flask, redirect, session, url_for, render_template
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

KEYCLOAK_BASE = "http://localhost:8080"
REALM = "demo"
CLIENT_ID = "flask-app"
# デモ用の固定シークレット。本番では os.environ.get("CLIENT_SECRET") のように環境変数から取得すること
CLIENT_SECRET = "flask-app-secret"

oauth = OAuth(app)
oauth.register(
    name="keycloak",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    # OIDC Discovery エンドポイントからメタデータを自動取得する
    server_metadata_url=f"{KEYCLOAK_BASE}/realms/{REALM}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@app.route("/")
def index():
    user = session.get("user")
    return render_template("index.html", user=user)


@app.route("/login")
def login():
    redirect_uri = url_for("callback", _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri)


@app.route("/callback")
def callback():
    token = oauth.keycloak.authorize_access_token()
    # userinfo が取得できれば優先する（なければトークン自体を保存）
    session["user"] = token.get("userinfo") or token
    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    user = session.get("user")
    if not user:
        return redirect(url_for("index"))
    return render_template("profile.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    # Keycloak 側のセッションも終了させる
    logout_url = (
        f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/logout"
        f"?post_logout_redirect_uri={url_for('index', _external=True)}"
        f"&client_id={CLIENT_ID}"
    )
    return redirect(logout_url)


if __name__ == "__main__":
    # debug=True はローカル開発専用。本番環境では必ず False にする
    app.run(debug=True, port=5000)
