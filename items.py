"""見積もり項目の表（行の一覧）を扱う処理をまとめたファイル。

各行は次のキーを持つ辞書で表す。
    name       : 作業名・商品名
    quantity   : 数量
    unit       : 単位
    unit_price : 単価（税抜）

金額は表には持たせず、必要なときに calculator.py で計算する。
"""

from validation import is_empty

COLUMNS = ["name", "quantity", "unit", "unit_price"]

# 最初に表示する空欄の行数
INITIAL_ROW_COUNT = 3


def empty_row():
    """空欄の行を1つ作る。"""
    return {column: None for column in COLUMNS}


def initial_rows():
    """最初に表示する空欄の行を作る。"""
    return [empty_row() for _ in range(INITIAL_ROW_COUNT)]


def rows_from_table(table):
    """表（DataFrame）を行の一覧に変換する。

    表の空欄は NaN（「数値ではない」を表す特別な値）になることがあるため、None にそろえる。
    """
    rows = []
    for record in table.to_dict("records"):
        rows.append({column: None if is_empty(record.get(column)) else record.get(column) for column in COLUMNS})
    return rows
