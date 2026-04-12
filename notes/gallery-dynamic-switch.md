# ギャラリー動的切り替え — セクション内で gallery を複数使う設計

## 問題

台本のセクション内に `<!-- gallery: 画像A -->` と `<!-- gallery: 画像B -->` を複数書いても、最後の gallery しか全シーンに反映されなかった。

```markdown
## S05: コードの核心

<!-- speaker: yumu -->
1か所目はリダイレクトするだけ。

<!-- gallery: 06_code_redirect.png -->

<!-- speaker: yumu -->
2か所目はトークンを受け取るだけ。

<!-- gallery: 07_code_token.png -->
```

この場合、「1か所目」のシーンに `07_code_token.png` が表示されてしまっていた。

## 原因

`markdown_reader.py` が gallery をセクション単位で1回だけ取得していたため。

```python
gallery = section.get("gallery")  # セクション開始時に1回だけ取得
```

`pip` や `mermaid` ディレクティブは動的アイテムとして処理されているのに、`gallery` だけがセクション属性として扱われていた。

## 解決策

`pip` / `mermaid` と同じパターンで、`gallery` をアイテムレベルで動的処理する。

```python
# _flush_text() でアイテムとして追加
current_items.append({
    "type": "gallery",
    "value": gallery_buf,
    "order": gallery_order_buf,
})

# シーン構築ループで動的更新
elif isinstance(item, dict) and item.get("type") == "gallery":
    gallery = item["value"]
    gallery_order = item["order"]
```

セクション初期値（`initial_gallery`）は維持して後方互換を確保する。

## 使い方（台本）

gallery → narration の順に書く。gallery はその直後の narration シーンに適用される。

```markdown
<!-- gallery: 06_code_redirect.png -->

<!-- speaker: yumu -->
<!-- expression: normal -->
1か所目はリダイレクトするだけ。

<!-- pause: 1.0 -->

<!-- gallery: 07_code_token.png -->

<!-- speaker: yumu -->
<!-- expression: normal -->
2か所目はトークンを受け取るだけ。
```

gallery の前に narration を置くと、そのシーンには前の gallery が引き継がれる。

## 関連

- `src/infrastructure/input/markdown_reader.py`
- `tests/infrastructure/input/test_markdown_reader_gallery_dynamic.py`
