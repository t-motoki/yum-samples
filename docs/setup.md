# WSL + Python + Docker セットアップガイド

> 対象：Windows PC を使っている初〜中級エンジニア
> このチャンネルで使うツールはすべて無料・OSS です。

---

## 1. WSL のセットアップ

### WSL2 とは

WSL（Windows Subsystem for Linux）は、Windows 上で Linux を動かす仕組みです。
Python 開発環境の構築や Docker の動作に必要なため、最初にセットアップします。

### 1-1. WSL2 のインストール

PowerShell を **管理者権限** で開いて、以下を実行します。

> ポイント：スタートメニューで「PowerShell」を右クリック →「管理者として実行」を選んでください。

```powershell
wsl --install
```

実行後、PC を再起動してください。

> 既に WSL が入っている場合は、以下で WSL2 にアップグレードできます。
>
> ```powershell
> wsl --set-default-version 2
> ```

### 1-2. Ubuntu のインストール

再起動後、再び PowerShell（管理者権限）を開いて実行します。

```powershell
wsl --install -d Ubuntu
```

> Microsoft Store からも「Ubuntu」で検索してインストールできます。どちらでも構いません。

### 1-3. 初回起動・ユーザー設定

インストールが完了すると Ubuntu が自動起動します。
以下のプロンプトが表示されるので、ユーザー名とパスワードを設定してください。

```
Enter new UNIX username: （任意のユーザー名を入力）
New password: （パスワードを入力 ※入力中は画面に表示されません）
Retype new password: （パスワードを再入力）
```

> ハマりポイント：パスワードは入力しても何も表示されませんが、正常な動作です。そのまま入力して Enter を押してください。

起動後、まずパッケージリストを更新しておきます。

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 2. Python のセットアップ（pyenv）

### なぜ pyenv を使うのか

Ubuntu にもデフォルトで Python が入っていますが、バージョンが古いことが多く、
プロジェクトごとに Python のバージョンを切り替えるのも困難です。
`pyenv` を使うと、複数バージョンの Python を簡単に管理できます。

### 2-1. pyenv の依存パッケージをインストール

```bash
sudo apt install -y \
  make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl \
  llvm libncursesw5-dev xz-utils tk-dev libxml2-dev \
  libxmlsec1-dev libffi-dev liblzma-dev git
```

### 2-2. pyenv をインストール

```bash
curl https://pyenv.run | bash
```

### 2-3. シェルに pyenv を登録する

`~/.bashrc` に設定を追記します。

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
```

設定を反映させます。

```bash
source ~/.bashrc
```

### 2-4. Python 3.11 のインストール

```bash
pyenv install 3.11.9
pyenv global 3.11.9
```

> インストールには数分かかることがあります。

### 2-5. インストールの確認

```bash
python --version
```

以下のように表示されれば成功です。

```
Python 3.11.9
```

> ハマりポイント：`python: command not found` と出る場合は、`source ~/.bashrc` をもう一度実行してください。

---

## 3. Docker のセットアップ

### 3-1. Docker Desktop のインストール（Windows 側）

[Docker Desktop 公式サイト](https://www.docker.com/products/docker-desktop/) からダウンロードしてインストールします。

> Docker Desktop は無料で使えます（個人利用・OSS 開発・学習目的）。

インストーラーを実行し、指示に従ってセットアップしてください。完了後、PC を再起動します。

> ハマりポイント：インストール中に「Use WSL 2 instead of Hyper-V」という選択肢が出たら、チェックを入れてください。

### 3-2. WSL2 Integration の有効化

Docker Desktop を起動し、以下の手順で WSL2 との連携を有効にします。

1. 右上の歯車アイコン（Settings）をクリック
2. 左メニューの「Resources」→「WSL Integration」を選択
3. 「Enable integration with my default WSL distro」をオンにする
4. 使用している Ubuntu ディストリビューションのトグルもオンにする
5. 「Apply & Restart」をクリック

### 3-3. インストールの確認

WSL（Ubuntu）のターミナルで実行します。

```bash
docker --version
docker run hello-world
```

`Hello from Docker!` と表示されれば成功です。

> ハマりポイント：`permission denied` エラーが出る場合は、WSL を一度閉じて再起動してください。Docker Desktop が完全に起動していないと接続できないことがあります。

---

## セットアップ完了チェックリスト

| 項目 | 確認コマンド | 期待する結果 |
| --- | --- | --- |
| WSL2 | `wsl --list --verbose`（PowerShell） | Ubuntu の VERSION が 2 |
| Python | `python --version` | Python 3.11.x 以上 |
| Docker | `docker --version` | Docker version 表示 |
