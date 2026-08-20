# 1行消したら止まった再現デモ

動画 `AIが書いたコード、動いた。1行消したら、止まった。` のための最小再現コードです。

`process_data.py` は `validation.py` の `validate` 関数で入力を検証してから合計します。先頭の import を1行消すと、呼び出し時に `NameError` で停止します。

## 実行

```bash
cd samples/shorts/ai-1gyou-keshita-tomatta
python process_data.py
```

成功すると、次のように表示されます。

```text
処理完了: 3件 / 合計: 16
```

## 削除前後を記録する

```bash
python record_demo.py --output /tmp/one-line-removal.json
```

このコマンドは一時ディレクトリ内のコピーだけから import 行を削除して実行します。公開サンプルのファイル自体は変更しません。JSONには成功版の標準出力と、削除版の `NameError` を記録します。

## ファイル責務

| ファイル | 責務 |
| --- | --- |
| `validation.py` | 正の整数だけを受け入れる検証関数 |
| `process_data.py` | 検証後に合計する実行対象 |
| `record_demo.py` | 成功版と1行削除版を隔離実行し、結果をJSONへ記録 |
