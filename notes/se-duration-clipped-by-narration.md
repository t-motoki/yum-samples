# SE がナレーション長で切り詰められる問題

## 問題

SE（効果音）を鳴らしても、ナレーションより長い SE が途中で切れる。

バイオリン恐怖音（5.72秒）をオチのナレーション「……知らないです。」に設定したところ、
ナレーション（約1.5秒）が終わった時点で SE が止まった。5.72秒中の1.5秒しか再生されない。

## 原因

SE はナレーション音声と `CompositeAudioClip` でミックスされるが、
その直後に `with_duration(audio_dur + tr_ext)` でナレーション長に切り詰めていた。

```python
# 修正前（バグあり）
mixed = CompositeAudioClip([audio] + se_tracks)
padded_audio = mixed.with_duration(audio_dur + tr_ext)  # ← SE が切れる
clip = clip.with_audio(padded_audio).with_duration(audio_dur + tr_ext)  # ← 映像も短い
```

SE がナレーションより長くても、出力される音声・映像ともにナレーション長で終端される。

## 解決策

SE が存在するとき、duration を `max(narration_duration, SE終了時刻)` に変更する。

```python
# 修正後
if se_tracks:
    mixed = CompositeAudioClip([audio] + se_tracks)
    # SE の終了時刻 = offset + duration。SE がナレーションより長ければ SE 側に合わせる
    se_end = max((t.start + t.duration for t in se_tracks), default=0.0)
    mixed_dur = max(audio_dur + tr_ext, se_end)
    padded_audio = mixed.with_duration(mixed_dur)
    clip = clip.with_audio(padded_audio).with_duration(mixed_dur)  # 映像も SE に合わせる
```

**音声だけでなく映像（clip）の duration も伸ばす必要がある。**
音声だけ伸ばしても映像が短ければ SE の後半は再生されない。

## 発見のきっかけ

ユーザーが「SE が短すぎる」と指摘した後、pause シーンを追加して対応しようとしたが
「効果音が鳴り終わって数秒無音が続く」という再指摘を受けた。pause を短くしても解決しないため
原因を調査したところ、SE がシーン内で切り詰められていることが判明した。

## 教訓

- SE を追加したあと「どこで止まっているか」を確認する（シーン内か・ファイル末尾か）
- `with_duration` を使うときは「SE より長い音声ファイルが来る可能性」を考慮する
- 音声の duration を変えたら映像の duration も一致させる（片方だけ変えると再生が止まる）

## 関連

- SE と BGM を独立したフローで処理する設計: [se-bgm-independent-mixing.md](se-bgm-independent-mixing.md)
