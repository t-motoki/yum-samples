# ライブラリを1個上げたら、関係ない場所が壊れた

共通入力チェックを v1 から v2 へ更新すると、変更していないログイン画面が失敗する最小再現です。

```bash
python login.py
python record_demo.py --output /tmp/library-upgrade-record.json
```

`record_demo.py` は一時コピー内だけで `login.py` の import を v2 に差し替えます。公開される `login.py` は v1 のままなので、更新前後の実行結果を同じ入力 `yumu` で比較できます。
