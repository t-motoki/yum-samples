# ep4.2 ライフイベント家計シミュレーター — 動いた。でもFPが触ったら、渡せなかった

この回では、ep4.1 で実装したシミュレーターを FP（さばきゃん）に渡し、
実務で使えるかを検証しました。

実装コードは別リポジトリで管理しています。

**[→ t-motoki/demo-life-event-simulator](https://github.com/t-motoki/demo-life-event-simulator)**

---

## この回でわかったこと

動くシステムと、渡せるシステムは違う。  
FP が触るまで見えなかった穴が、2つあった。

### 穴1: CUI の壁

```bash
python -m src.main scenario.yaml
```

エンジニアには自然なコマンドでも、FP には渡せない。  
「ターミナルを開いて」の時点で止まる。

### 穴2: 育休中の収入減が未モデル化

配偶者の出産年（2026年）、収入が `flat` のまま動いていた。  
育休中は給与が育児休業給付金（受取額の目安: 年収の約60%）に変わるが、
シミュレーターはそれを反映していなかった。

---

## 追加した計算モデル

`BirthEvent` に育休フィールドを追加し、給与収入に減額率を適用するようにした。

### モデル定義（models.py）

```python
@dataclass
class BirthEvent(LifeEvent):
    child_count: int = 1
    client_maternity_rate: float = 1.0    # 本人の育休中収入率（0.0〜1.0）
    client_maternity_years: int = 0       # 本人の育休期間（年）
    spouse_maternity_rate: float = 1.0    # 配偶者の育休中収入率
    spouse_maternity_years: int = 0       # 配偶者の育休期間（年）
```

### 減額率の計算（cashflow.py）

```python
def _maternity_rate(events: list[LifeEvent], target: str, year: int) -> float:
    """指定年に有効な育休減額率を返す。複数の BirthEvent がある場合は最小値を使う。"""
    rate = 1.0
    for event in events:
        if not isinstance(event, BirthEvent):
            continue
        if target == "client":
            m_rate = event.client_maternity_rate
            m_years = event.client_maternity_years
        else:
            m_rate = event.spouse_maternity_rate
            m_years = event.spouse_maternity_years
        if m_rate < 1.0 and event.year <= year < event.year + m_years:
            rate = min(rate, m_rate)
    return rate
```

```python
# simulate() での適用
client_rate = _maternity_rate(scenario.events, "client", year)
income = int(_calc_income(scenario.client, year, scenario.start_year) * client_rate)
income += _calc_pension(scenario.client, year, scenario.start_year)  # 年金には適用しない
```

### シナリオ定義（scenario.yaml）

```yaml
- type: birth
  year: 2026
  child_count: 1
  spouse_maternity_rate: 0.6   # 育休中は通常年収の 60% 受取
  spouse_maternity_years: 1    # 1年間
```

---

## Claude Code に渡したプロンプト

### 育休収入減の実装依頼

```
BirthEvent に育休中の収入減を反映してください。

仕様:
- BirthEvent に client_maternity_rate / client_maternity_years /
  spouse_maternity_rate / spouse_maternity_years を追加する
- 育休期間中の給与収入に減額率を乗算する（年金収入には適用しない）
- 複数の BirthEvent が同一年に重なる場合は最小値を採用する

validator.py にも rate（0.0〜1.0）と years（0以上）のチェックを追加する。
yaml_loader.py でも新フィールドを読み込む。
```

---

## 生成されたファイル（差分）

| ファイル | 変更内容 |
|----------|----------|
| [src/domain/models.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/domain/models.py) | BirthEvent に育休フィールド4つを追加 |
| [src/domain/cashflow.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/domain/cashflow.py) | `_maternity_rate()` 追加・simulate() に適用 |
| [src/input/yaml_loader.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/input/yaml_loader.py) | birth イベントの新フィールドを読み込み |
| [src/input/validator.py](https://github.com/t-motoki/demo-life-event-simulator/blob/master/src/input/validator.py) | 育休フィールドのバリデーション追加 |
| [scenario.yaml](https://github.com/t-motoki/demo-life-event-simulator/blob/master/scenario.yaml) | spouse_maternity_rate: 0.6 / spouse_maternity_years: 1 を追加 |
