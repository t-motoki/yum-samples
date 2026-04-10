# 育休収入をシミュレーターに組み込む — 給付金への切り替えを年単位で反映する

家計シミュレーターで育児休業を扱うとき、
「育休中も給与収入は同じ」で動かしてしまいがちです。
FP 実務では育休中の受取額は通常給与と大きく異なるため、
シミュレーションの精度に直接影響します。

## 問題: flat モデルは育休を無視する

```yaml
# scenario.yaml
- type: birth
  year: 2026
  child_count: 1
```

上記だけでは出産年の収入は変わらない。
income_model: flat の場合、育休中も年収がそのまま計上されてしまう。

```text
2025年: 収入 350万（配偶者）
2026年: 収入 350万 ← 育休中なのに変わっていない
2027年: 収入 350万
```

## 育児休業給付金の実態

育休中は雇用保険から「育児休業給付金」が支給される。

| 期間 | 給付率（賃金日額に対して） |
|------|--------------------------|
| 育休開始〜180日目 | 67% |
| 181日目〜 | 50% |

年間を通じた受取額の目安は年収の約 **60%** とされることが多い（180日67% + 185日50% の平均）。

ただし上限額があるため、高収入者ほど実質的な給付率は低くなる。

## 解決策: BirthEvent に減額率と期間を持たせる

```python
@dataclass
class BirthEvent(LifeEvent):
    child_count: int = 1
    client_maternity_rate: float = 1.0    # 本人の育休中収入率（0.0〜1.0）
    client_maternity_years: int = 0       # 本人の育休期間（年）
    spouse_maternity_rate: float = 1.0    # 配偶者の育休中収入率
    spouse_maternity_years: int = 0       # 配偶者の育休期間（年）
```

```yaml
- type: birth
  year: 2026
  child_count: 1
  spouse_maternity_rate: 0.6   # 年収の 60% を受け取る
  spouse_maternity_years: 1    # 1年間
```

```text
2025年: 収入 350万（配偶者）
2026年: 収入 210万 ← 350万 × 0.6
2027年: 収入 350万（育休終了）
```

## 減額率の適用ロジック

育休期間のチェックは「`birth.year <= 対象年 < birth.year + 育休年数`」で判定する。

```python
def _maternity_rate(events: list[LifeEvent], target: str, year: int) -> float:
    rate = 1.0
    for event in events:
        if not isinstance(event, BirthEvent):
            continue
        m_rate = event.client_maternity_rate if target == "client" else event.spouse_maternity_rate
        m_years = event.client_maternity_years if target == "client" else event.spouse_maternity_years
        if m_rate < 1.0 and event.year <= year < event.year + m_years:
            rate = min(rate, m_rate)
    return rate
```

複数の BirthEvent が同一年に重なる場合は最小値（より厳しい方）を採用する。

## 年金収入には適用しない

育休減額は給与収入にのみ適用する。

```python
client_rate = _maternity_rate(scenario.events, "client", year)
income = int(_calc_income(client, year, start_year) * client_rate)
income += _calc_pension(client, year, start_year)  # 年金はそのまま
```

年金受給年齢（65歳〜）と育休が重なるケースは実務上ほぼないが、
設計として明示的に分離しておくと将来の変更に強い。

## rate=1.0 のときは計算コストなし

`client_maternity_years: 0`（デフォルト）の場合、期間チェックで `0 <= year < 0` が常に偽になるため、
rate は 1.0 のまま変わらない。既存シナリオへの後方互換性が保たれる。

## 設計のポイント

「育休年数を float にしない」——月単位で設定したい誘惑があるが、
年単位の家計シミュレーターでは年単位で十分。単位を合わせないとバグの原因になる。
