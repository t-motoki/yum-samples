# yum-samples

**[▶ YouTube「ゆる系エンジニアの手記」](https://www.youtube.com/channel/UCE1rHqZ5UvXkc0ZBLNiX6bA)** のサンプルコードリポジトリです。

## このリポジトリについて

動画の中で実際に動かしているコードを、エピソードごとにフォルダに整理しています。
**すべて無料・OSS・Python だけで動きます。** 有料ツールや課金サービスは一切使いません。

チャンネルのコンセプトは「お金をかけずにソリューションを作る泥臭いプロセスをそのまま見せる」こと。
初級〜中級エンジニアの方が「自分でもできそう」と思えるコードを目指しています。

---

## エピソード一覧

| エピソード | タイトル | 主な技術 | フォルダ |
| --- | --- | --- | --- |
| ep0.0 | Pythonとフリーツールだけでアバターを無料で作る | rembg / Pillow | [ep0.0_avatar-creation](./episodes/ep0.0_avatar-creation/) |
| ep1.0 | アバターを動画に合成してナレーション付き動画を自動生成する | VOICEVOX / Pillow / MoviePy | [ep1.0_avatar-video-synthesis](./episodes/ep1.0_avatar-video-synthesis/) |
| ep2.0 | IP-Adapterで1枚のアバターから表情バリエーションを生成する（失敗実録） | IP-Adapter / Diffusers | [ep2.0_avatar-variant-generation](./episodes/ep2.0_avatar-variant-generation/) |
| ep2.1 | 同一キャラクターの表情だけを変える — 表情モーフィング再挑戦 | THA3 / rembg / Pillow | [ep2.1_avatar-expression-morphing](./episodes/ep2.1_avatar-expression-morphing/) |
| ep3.0 | 紙芝居スタイル動画パイプライン — 台本を書けばゆむが感情豊かに話す仕組みを作る | Pillow / VOICEVOX | [ep3.0_kamishibai-pipeline](./episodes/ep3.0_kamishibai-pipeline/) |
| ep3.1 | テロップフェードインアニメーション — 静止テロップに「動き」を加える | Pillow / MoviePy | [ep3.1_telop-animation](./episodes/ep3.1_telop-animation/) |
| ep2.2 | さばきゃん登場 — 聞いてくれる人がいるだけで、こんなに違う | Pillow（2キャラサムネイル）/ VOICEVOX | [ep2.2_sabacyan-introduction](./episodes/ep2.2_sabacyan-introduction/) |
| ep3.2 | BGMフェードイン・フェードアウト — 台本から音量曲線を制御する | MoviePy | [ep3.2_bgm-fade](./episodes/ep3.2_bgm-fade/) |
| ep3.3 | Wav2Lip でリップシンク — アニメキャラに口パクをつける | Wav2Lip / PyTorch | [ep3.3_wav2lip-lipsync](./episodes/ep3.3_wav2lip-lipsync/) |
| ep3.4.1 | AIで静止画を動かす実験、13分待って気づいたこと | SadTalker / PyTorch | [ep3.4.1_sadtalker-cpu](./episodes/ep3.4.1_sadtalker-cpu/) |
| ep3.4.2 | CPU・無料でアニメキャラの口を動かす — Rhubarb Lip Sync 調査記録 | Rhubarb Lip Sync | [ep3.4.2_rhubarb-lipsync](./episodes/ep3.4.2_rhubarb-lipsync/) |
| ep3.4.3 | 口だけ動いて体が固まる問題 — 表情補間とアイドルアニメーションで人形感を解消する | Pillow | [ep3.4.3_expression-blend-idle](./episodes/ep3.4.3_expression-blend-idle/) |
| ep3.4.4 | 感情ラベルが体を動かす — joy で弾んで、surprise で揺れる仕組み | Pillow | [ep3.4.4_emotion-action](./episodes/ep3.4.4_emotion-action/) |
| ep3.5.1 | シーンの切れ目が気になっていた — 台本1行で全シーンにフェードトランジションを適用する | MoviePy | [ep3.5.1_fade-transition](./episodes/ep3.5.1_fade-transition/) |
| ep3.5.2 | 怒ると揺れて、悲しむと沈む — 感情ごとに動きが変わる仕組みを作った | Pillow | [ep3.5.2_emotion-actions-extended](./episodes/ep3.5.2_emotion-actions-extended/) |
| ep3.5.3 | zoom ディレクティブ — 任意のシーンに「寄り・引き」をつける | Pillow | [ep3.5.3_zoom-directive](./episodes/ep3.5.3_zoom-directive/) |
| ep3.5.4 | カメラワーク演出 — パン・Ken Burns・画面シェイクを台本から制御する | Pillow | [ep3.5.4_camera-work](./episodes/ep3.5.4_camera-work/) |
| ep3.5.5 | 台本に1行書くだけで効果音を鳴らせるようにした | MoviePy | [ep3.5.5_se-directive](./episodes/ep3.5.5_se-directive/) |
| ep3.6 | スクリーン録画をアバター解説に重ねる — PiP ディレクティブで台本から制御する | Pillow / MoviePy / ffmpeg | [ep3.6_pip-directive](./episodes/ep3.6_pip-directive/) |
| ep3.5.6 | テロップを動かす — 4種類のアニメーションを台本から制御する | Pillow | [ep3.5.6_telop-effect](./episodes/ep3.5.6_telop-effect/) |

---

## 技術メモ

動画制作中に得た知見をまとめたノートです。コードより「考え方」が中心です。

| タイトル | 内容 |
| --- | --- |
| [動画生成の高速化](./notes/video-generation-speedup.md) | マルチプロセス化と VOICEVOX ロードバランシングで生成時間を大幅改善 |
| [VOICEVOX 音量チューニング](./notes/voicevox-volume-tuning.md) | YouTube -14 LUFS に合わせた volumeScale の設定方法 |
| [WAV キャッシュをコンテンツハッシュで管理する](./notes/wav-cache-with-content-hash.md) | テキスト変更を自動検知するキャッシュキー設計 |
| [AI 技術選定: 生成か変形か](./notes/ai-generation-vs-transformation.md) | IP-Adapter 失敗 → THA3 成功から学んだ「変形」アプローチの考え方 |
| [ImageClip と VideoClip の使い分け](./notes/imageclip-vs-videoclip.md) | MoviePy でアニメーションなしのシーンを高速化するパターン |
| [台本ディレクティブの設計](./notes/script-directive-design.md) | Markdown コメントで動画演出を制御する設計とパース実装 |
| [コードスクロール演出](./notes/code-scroll-animation.md) | 全体→キーの一行に絞る二段構成の実装パターン |
| [WSL2 メモリクラッシュと .wslconfig](./notes/wsl2-memory-crash-and-wslconfig.md) | Wav2Lip 処理中の WSL2 VM クラッシュを .wslconfig で根本解決した記録 |
| [リップシンクツール選定: 映像出力型 vs データ出力型](./notes/lipsync-data-vs-video-output.md) | Rhubarb vs Wav2Lip — 既存パイプラインへの統合コストが変わる設計の考え方 |
| [CPU・アニメ向けリップシンクツール調査記録](./notes/cpu-anime-lipsync-tool-survey.md) | THA4・MuseTalk・LatentSync・Rhubarb を比較した選定記録と教訓 |
| [感情連動アニメーションの設計](./notes/emotion-driven-animation.md) | 感情ラベルから体の動きを決める設計と「既存の sin 波を流用する」実装パターン |
| [crossfade で音声がずれる問題と解決策](./notes/crossfade-audio-timing.md) | MoviePy の padding=-tr_sec が音声 duration を変えないために起きるズレと、CompositeAudioClip による無音バッファの付け方 |
| [感情アクション拡張: 振れ幅・周波数・累積で区別する](./notes/emotion-animation-parameter-design.md) | 同じ方向の動きが増えたときに方向以外の軸（振れ幅・周波数・累積型）で感情を区別する設計パターン |
| [clip-relative time vs scene-elapsed time](./notes/clip-relative-time-vs-scene-elapsed.md) | アニメーション関数で「何を起点とした時刻か」を使い分ける設計判断 |
| [ディレクティブのスコープ設計](./notes/directive-scope-design.md) | 台本ディレクティブが「どこまで影響するか」を per-clip 追跡で制御する設計パターン |
| [ffmpeg xfade で音声がずれる問題と解決策](./notes/ffmpeg-xfade-audio-concat.md) | filter_complex で累積ストリームに atrim すると後半が消える問題と、個別 atrim + 多入力 concat による修正 |
| [カメラワークディレクティブの設計](./notes/camera-work-directives.md) | 拡大クロップでフレームサイズ不変のまま移動・elapsed 分離・非整数比率シェイクの設計パターン |
| [SE と BGM を独立したフローで処理する設計](./notes/se-bgm-independent-mixing.md) | CompositeAudioClip（シーン内）と ffmpeg amix（最終出力）を分離して SE と BGM の干渉をなくす |
| [動画生成時にチャプタータイムスタンプを記録する設計](./notes/chapter-timestamps-from-generation.md) | WAV 合計からの後計算はずれる — 生成プロセス内で chapters.json を出力する設計と教訓 |
| [PiP オーバーレイ設計](./notes/pip-overlay-design.md) | 台本1行でスクリーン録画をアバターシーンに重ねる — Phase 3b 後処理・テロップ非重複クランプ・amix 音声ミックスの設計パターン。section END-state バグ・local-t 問題・AAC 末尾切れの修正記録も含む |
| [ショート diagonal レイアウトの設計](./notes/shorts-diagonal-layout.md) | 等サイズ斜め配置スタイルの座標設計・デフォルト変更の判断・chibi 表情との注意点 |
| [ショートコメディの間（ポーズ）設計](./notes/short-comedy-pacing.md) | 間に意味を持たせる設計・キャラ設定と会話の整合性・creator への制約の渡し方 |
| [テロップエフェクトアニメーションの設計](./notes/telop-effect-animation.md) | `t` 純粋関数・bounce の位相設計・pill typewriter のガタつき対策・不正値の寛容な扱い |

---

## セットアップ

- Python 3.11 以上が必要です（pyenv 推奨）
- 各エピソードの README に必要なライブラリとセットアップ手順が書いてあります
- 初めての方は [docs/setup.md](./docs/setup.md) を参照してください（WSL / Python / Docker の環境構築手順）

---

## 方針・制約

- 使用するライブラリはすべて **無料・OSS**
- メイン言語は **Python**
- 外部の有料 API・クラウド課金サービスは使わない
- 「動画を見て手元で再現できる」を最優先にする

---

## チャンネル

### [▶ ゆる系エンジニアの手記](https://www.youtube.com/channel/UCE1rHqZ5UvXkc0ZBLNiX6bA)

コードへの質問・フィードバックは Issue または動画のコメント欄でどうぞ。
