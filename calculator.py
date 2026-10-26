"""金額計算の処理をまとめたファイル。

画面表示とは切り離し、計算だけを行う。
計算ルールは requirements.md の「7. 計算ルール」に従う。

小数の計算には Decimal（10進数で正確に計算できる型）を使う。
Python の float（普通の小数）は 0.29 * 50 が 14.499999... になるなど
わずかな誤差が出るため、四捨五入の結果がずれることがある。
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

# 消費税率（初期版は10%で固定）
TAX_RATE = Decimal("0.10")


def to_decimal(value):
    """数値を Decimal に変換する。

    float をそのまま Decimal にすると誤差も引き継ぐため、
    いったん文字列にしてから変換する。
    """
    return Decimal(str(value))


def calc_item_amount(quantity, unit_price):
    """項目ごとの金額（数量 × 単価）を計算し、1円未満を四捨五入する。"""
    amount = to_decimal(quantity) * to_decimal(unit_price)
    # ROUND_HALF_UP：0.5以上を切り上げる一般的な四捨五入
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calc_subtotal(amounts):
    """小計（四捨五入後の各項目の金額の合計）を計算する。"""
    return sum(amounts)


def calc_tax(subtotal):
    """消費税額（小計 × 消費税率）を計算し、1円未満を切り捨てる。"""
    tax = to_decimal(subtotal) * TAX_RATE
    # ROUND_DOWN：切り捨て
    return int(tax.quantize(Decimal("1"), rounding=ROUND_DOWN))


def calc_total(subtotal, tax):
    """合計金額（小計 ＋ 消費税額）を計算する。"""
    return subtotal + tax


def calc_estimate(items):
    """見積もり全体の金額をまとめて計算する。

    items には、入力チェックを通過した項目だけを渡す。
    各項目は "quantity"（数量）と "unit_price"（単価）を持つ辞書とする。
    """
    amounts = [calc_item_amount(item["quantity"], item["unit_price"]) for item in items]
    subtotal = calc_subtotal(amounts)
    tax = calc_tax(subtotal)
    total = calc_total(subtotal, tax)
    return {
        "amounts": amounts,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }
