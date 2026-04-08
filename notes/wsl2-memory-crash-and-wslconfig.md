# WSL2 がメモリ不足でクラッシュする問題と .wslconfig による解決

Wav2Lip（PyTorch CPU 推論）処理中に WSL2 が VM ごと落ちる問題が繰り返し発生した。
原因の特定から `.wslconfig` による根本解決までの記録です。

## 問題

Wav2Lip で動画を処理中、WSL2 が突然落ちる。
- ターミナルが切断され、処理が中断される
- 次回 WSL2 起動時に journald が以下のメッセージを出力する:

```
user-1000.journal corrupted or uncleanly shut down, renaming and replacing.
```

このメッセージは **WSL2 VM が正常終了せずに強制終了した**ときの典型的なサイン。

## 原因

`.wslconfig` が未設定の状態では、WSL2 のメモリ上限は Windows（Hyper-V）が動的に管理する。

```
$ cat /proc/meminfo | grep MemTotal
MemTotal:  7585012 kB   ← ほぼ RAM 全量をWSL2が確保

$ dmesg | grep hv_balloon
hv_balloon: Max. dynamic memory size: 7648 MB
```

**クラッシュのメカニズム:**

```
Wav2Lip 処理中
  → PyTorch モデル（S3FD + Wav2Lip）+ フレームバッファでメモリ急増
  → WSL2 が 7.6GB（物理 RAM の上限近く）まで使用
  → Windows 側が他のプロセスのためにメモリを取り戻そうとする
  → Hyper-V が WSL2 VM のメモリを強制回収
  → WSL2 VM ごとクラッシュ
```

`.wslconfig` がないと WSL2 のメモリ確保量が「Windows 任せの動的制御」になり、
処理のピーク時に Windows との競合でクラッシュする。

## 対策

`C:\Users\<ユーザー名>\.wslconfig` を作成してメモリ上限を明示的に固定する:

```ini
[wsl2]
memory=5GB
swap=4GB
```

- `memory=5GB`: WSL2 専用メモリを宣言。Windows との奪い合いが起きなくなる
- `swap=4GB`: メモリが足りなくなったときの逃げ場を確保。クラッシュの代わりにスワップに落とす

設定の反映方法（PowerShell で実行）:

```powershell
wsl --shutdown
# その後 WSL を再起動すると反映される
```

反映確認:

```bash
$ free -h
       total   used   free
Mem:   4.8Gi  ...
Swap:  4.0Gi  ...
```

## 結果

- Wav2Lip 処理中のクラッシュが解消
- Swap 4GB を確保したことで、ピーク時はスワップに逃げて処理が継続するようになった
- memory=5GB（Wav2Lip のピーク使用量は 3〜4GB 程度）で問題なく収まっている

## 教訓

- **WSL2 は `.wslconfig` が未設定だとメモリ管理が不安定になる**。
  重い処理（PyTorch 推論・動画変換など）をする環境では必ず設定すること。
- journald の "corrupted or uncleanly shut down" は WSL2 VM クラッシュの確実なサイン。
  OOM kill ではなく Hyper-V レベルのクラッシュのため `dmesg` に OOM ログが出ないことがある。
- swap は「クラッシュの緩衝材」として機能する。memory 上限と合わせて設定する。

---

## 追記: 4並列 ffmpeg によるOOMと vm.swappiness 対策（2026-04-09）

### 状況

`.wslconfig` で `memory=7GB / swap=4GB` を設定済みの環境でも、動画生成中に OOM クラッシュが繰り返し発生した。

**クラッシュのメカニズム:**

```text
動画生成（4並列 ffmpeg ワーカー）
  → チャンク数=4 が同時起動（ピーク時）
  → ffmpeg 4プロセス + Python/moviepy でメモリ急増（合計 ~5〜6GB）
  → vm.swappiness=60（デフォルト）ではスワップを使い始めるのが遅い
  → RAMが突然枯渇して OOM killer が発動
  → Python の finally が動かず .generation.lock と chunk_*TEMP* が残留
```

### 対策: vm.swappiness を上げる

```bash
# 一時適用（再起動で元に戻る）
sudo sysctl vm.swappiness=80

# 永続化
echo "vm.swappiness=80" | sudo tee -a /etc/sysctl.conf
```

`vm.swappiness` はカーネルがスワップを使い始めるアグレッシブさ（0〜100）:

- デフォルト 60: RAMが残り少なくなってからスワップを使う
- 80: RAMにまだ余裕があるうちからスワップに逃がす → OOM前に緩衝が効く

### 確認方法

生成中に別ターミナルで監視:

```bash
watch -n 1 free -h
```

- **Swap used が増える** = vm.swappiness が機能している証拠
- **Swap free が 100MB 以下** = 危険水域（次の手: `swap=8GB` に増やす）

### 次の手（vm.swappiness で不十分な場合）

`.wslconfig` の swap を増やす:

```ini
[wsl2]
memory=7GB
swap=8GB   # 4GB → 8GB
```

設定反映は `wsl --shutdown` 後に再起動。
SSDへの書き込みが増えるが、生成ピークを超えるだけなので消耗リスクは現実的に低い。
