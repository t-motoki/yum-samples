# ショート diagonal レイアウトの設計

## 問題

`shorts_style=asymmetric`（デフォルト）は左大・右小の非対称配置。`dialogue_order` の順番を変えれば左右を入れ替えられるが、片方が常に小さくなる。

「2キャラを等サイズで表示しながら、どちらが主役かを画面の位置で伝えたい」という要件に対応できなかった。

## 解決策: diagonal スタイル

`dialogue_order[0]` を右上・`[1]` を左下に等サイズで配置する。

```markdown
<!-- config: shorts_style=diagonal -->
<!-- config: dialogue_order=sabacyan,yumu -->
```

この設定で sabacyan が右上（目線が自然に向く位置）、yumu が左下に配置される。

## 座標設計

`layout.py` の `SHORTS_VERTICAL_POSITION_PRESETS` に2つのプリセットを追加:

```python
"right_upper_eq": VerticalPositionSpec(center_x=840, bottom_y=1350, max_w=650, max_h=1150),
"left_lower_eq":  VerticalPositionSpec(center_x=270, bottom_y=1600, max_w=650, max_h=1150),
```

- `max_w=650 / max_h=1150` を両プリセットで統一 → 等サイズを保証
- `right_upper_eq`: bottom_y=1350 → 上部に配置（テロップエリア 1560px に干渉しない）
- `left_lower_eq`: bottom_y=1600 → 下部に配置（テロップエリアには侵入しない）
- center_x は `equal` スタイルと同じ 840 / 270 を流用

## 実装の設計判断

### `vertical` の派生として実装した理由

`_draw_avatar_dialogue_shorts_vertical` はプリセット名をリストで受け取る設計になっており、diagonal も「プリセットで座標を決める」という構造が同じ。`equal`（水平固定・同 bottom_y）ではなく `vertical` の派生として実装することで Y 座標の自由度を保てる。

専用メソッド `_draw_avatar_dialogue_shorts_diagonal` を作り、`_DIAGONAL_POSITIONS = ["right_upper_eq", "left_lower_eq"]` をモジュール定数で固定した。`video.vertical_positions`（台本の `<!-- config: vertical_positions=... -->`）との干渉を防ぐため、参照先を切り離した。

### デフォルトを diagonal に変更した理由

asymmetric は片方が大きく片方が小さい配置で、「2キャラが対等に話す」場面に使いにくい。diagonal は等サイズで画面に動きがあり、デフォルトとして自然。

## char_scales・char_flip との組み合わせ

diagonal でも `char_scales` と `char_flip` は有効。`vertical` と同じロジックで処理される。

```markdown
<!-- config: shorts_style=diagonal -->
<!-- config: char_scales=1.2,1.0 -->  # dialogue_order[0] を少し大きく
```

## chibi 表情との注意点

equal や diagonal の等倍サイズでは chibi 表情（顔アップ・上半身なし）が小さく見えて「体が消えた」印象になる。chibi を使う場合は `char_scales` で対象キャラを大きくするか、別の表情（sad / surprise）を検討する。

## 教訓

- **主役を決めてから `dialogue_order` を設定する**: `dialogue_order[0]` が右上（視線が向きやすい位置）になるため、目立たせたいキャラを index=0 に置く
- **asymmetric は「主役と聞き役」が明確な場面に使う**: 喋り手が大きく、受け手が小さい配置なので、主役が固定の場面向き
- **diagonal は「対等な掛け合い」に使う**: どちらも等サイズなので、ツッコミとボケが交互に入れ替わる場面に向いている
