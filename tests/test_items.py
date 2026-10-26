"""items.py の自動テスト。"""

import pandas as pd

from items import COLUMNS, INITIAL_ROW_COUNT, empty_row, initial_rows, rows_from_table


def test_最初は空欄の行が3行ある():
    rows = initial_rows()
    assert len(rows) == INITIAL_ROW_COUNT == 3
    assert all(row == empty_row() for row in rows)


def test_表を行の一覧に変換する():
    table = pd.DataFrame(
        [
            {"name": "デザイン制作", "quantity": 1.0, "unit": "式", "unit_price": 50000.0},
            {"name": None, "quantity": float("nan"), "unit": None, "unit_price": float("nan")},
        ],
        columns=COLUMNS,
    )
    assert rows_from_table(table) == [
        {"name": "デザイン制作", "quantity": 1.0, "unit": "式", "unit_price": 50000.0},
        empty_row(),
    ]


def test_行がない表も変換できる():
    assert rows_from_table(pd.DataFrame([], columns=COLUMNS)) == []
