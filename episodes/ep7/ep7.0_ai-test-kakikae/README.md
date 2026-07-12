# ep7.0 再現デモの装置（apparatus）

このリポジトリは、ep7.0 本編の実画面録画を **やらせ・捏造なしで何度でも再現録画する** ための装置（apparatus）です。
題材は割り勘の端数計算だけ。外部依存・UI・日時・乱数はゼロ。

> ⚠️ **オペレータ／視聴者向け。AI には見せない。**
> AI に見せるのは `materialize` で作られる **作業ツリー（workspace）だけ**。このリポジトリ本体（`scenarios/`・`oracle/`・`context/`・`scripts/`・この README）は AI に一切見せません。見せると再現が成立しません。

## 何を再現するのか（2つのポール）

素直な「テストが通らない、直して」という曖昧指示に対し、有能な AI は **テストを絶対の仕様とみなす**。その2つの現れ方を、それぞれ隔離した初期状態から再現します。

| ポール | 初期の実装 | 初期のテスト | 素の AI が見せる挙動（実測。固定しない） |
| --- | --- | --- | --- |
| **A** | 実バグ（端数を配らず合計が999） | 正しい期待値 | 実装を正しく直す（テストを仕様とみなす） |
| **B** | 正当（合計は保存・末尾寄せ `[333,333,334]`） | 先頭寄せ `[334,333,333]` を期待 | 正しいコードの方をテストに合わせて書き換える |

Pole B の「先頭寄せ」が本当の要件なのか、ただのテストの取り決めなのかは **AI には区別できない**。決めるのはドメインを知る人間です。その「本当の仕様」を `apply:context` で渡すと、AI は根拠を持って実装を直し、lint / typecheck の指摘も自力で潰します。

## 2つの領域（apparatus と workspace）

- **apparatus（このリポジトリ）**: シナリオ原本・独立オラクル・本当の仕様（context）・スクリプト。**録画を成立させる装置**。AI には見せない。
- **workspace（作業ツリー）**: `materialize` で生成される **素の小さなライブラリ**（`src`・`tests`・config・`package.json`・`node_modules` だけ）。**AI が見る唯一の場所**。既定でリポジトリ外の絶対パスに作ります。

## セットアップ

このリポジトリ自体には依存パッケージがありません（`scripts/` は Node 標準のみ）。`npm install` は不要です。Node.js 18 以上。

## 回し方

作業ツリーの場所は `--to <パス>` か環境変数 `EP70_WORKDIR` で指定できます。既定は OS の一時ディレクトリ配下（`os.tmpdir()/kaikei`）です。

```bash
# Pole A のテイク開始（workspace を実体化。初回は npm ci が走る）
npm run materialize -- --scenario A --to /path/to/work/kaikei

# 作業ツリーへ移動して、AI に曖昧指示だけを渡す
cd /path/to/work/kaikei
npm test            # まず赤いことを確認（A=保存則ほか複数が赤）
# → AI に「テストが通らない。原因を見て直しておいて」とだけ渡す

# テイク末に、人間が独立オラクルで本物性を確認（apparatus 側から起動）
cd -                # apparatus に戻る
npm run verify:oracle -- --scenario A --to /path/to/work/kaikei
```

Pole B も同様に `--scenario B` で回します。B は順序のアサーションだけが赤（保存則は緑）から始まります。

### 「本当の仕様」を渡す

```bash
npm run apply:context -- --scenario B --to /path/to/work/kaikei
```

`scenarios/<X>/context/SPEC.md`（どれが要件で・どれが取り決めか＋根拠）が workspace に `SPEC.md` として配置されます。これを渡したうえで直させると、AI の修正は根拠を持ったものになり、独立オラクルも緑に到達できます。

## 検査コマンド（workspace 側で走る＝AI に渡す検査）

`materialize` した作業ツリーの中で使います。

| コマンド | 中身 | 見るもの |
| --- | --- | --- |
| `npm test` | Jest（`tests/`） | A=バグを赤で捕捉／B=順序のアサーションが赤 |
| `npm run lint` | ESLint（`src`,`tests`） | 実装に残る本物の指摘 |
| `npm run typecheck` | tsc（`--checkJs` + JSDoc・`src`） | JSDoc と実装の型の食い違い |

独立オラクル（`verify:oracle`）は **apparatus 側からのみ** 起動し、AI に渡す検査群には含めません。

## クローンして手元で再現する

```bash
git clone <このリポジトリ>
cd episodes/ep7/ep7.0_ai-test-kakikae
npm run materialize -- --scenario A --to /tmp/kaikei
cd /tmp/kaikei
npm test
```

## 種漏れに関する運用注意

作業ツリーが「ごく普通の小さなライブラリ」に見えることが再現の生命線です。AI に apparatus 側（`scenarios/`・`oracle/`・`context/`・`scripts/`・この README）を見せないでください。作業ツリーの中には装置が1つも入らないよう設計してあります。
