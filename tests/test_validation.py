"""validation.py の自動テスト。"""

from datetime import date

from validation import check_dates, check_items, check_quantity, check_required, check_unit_price


def row(name=None, quantity=None, unit=None, unit_price=None):
    return {"name": name, "quantity": quantity, "unit": unit, "unit_price": unit_price}


def test_数量の正しい値():
    assert check_quantity(1) is None
    assert check_quantity(0.01) is None
    assert check_quantity(99999.99) is None
    assert check_quantity(1.5) is None


def test_数量の不正な値():
    assert check_quantity(None) == "数量を入力してください。"
    assert check_quantity(float("nan")) == "数量を入力してください。"
    assert check_quantity(0) == "数量は0より大きい値を入力してください。"
    assert check_quantity(-1) == "数量は0より大きい値を入力してください。"
    assert check_quantity(100000) == "数量は99,999.99以下で入力してください。"
    assert check_quantity(0.001) == "数量は小数第2位まで入力してください。"
    assert check_quantity("abc") == "数量は数字で入力してください。"


def test_単価の正しい値():
    assert check_unit_price(0) is None
    assert check_unit_price(50000) is None
    assert check_unit_price(50000.0) is None
    assert check_unit_price(999_999_999) is None


def test_単価の不正な値():
    assert check_unit_price(None) == "単価を入力してください。"
    assert check_unit_price(-1) == "単価は0円以上で入力してください。"
    assert check_unit_price(1_000_000_000) == "単価は999,999,999円以下で入力してください。"
    assert check_unit_price(1.5) == "単価は1円単位（整数）で入力してください。"
    assert check_unit_price("abc") == "単価は数字で入力してください。"


def test_すべて空欄の行は無視する():
    result = check_items([row(), row(), row()])
    assert result.valid_indexes == []
    assert result.errors == []
    assert result.notices == []


def test_作業名が空欄の行は計算対象外として案内する():
    result = check_items([row("デザイン制作", 1, "式", 50000), row(None, 2, "回", 5000)])
    assert result.valid_indexes == [0]
    assert result.notices == ["2行目：作業名が空欄のため、計算に含めていません。"]


def test_作業名が空白だけの行も空欄として扱う():
    result = check_items([row("   ", 2, "回", 5000)])
    assert result.valid_indexes == []
    assert len(result.notices) == 1


def test_作業名がある行の入力エラー():
    result = check_items([row("修正対応", 0, "回", None)])
    assert result.valid_indexes == []
    assert result.errors == [
        "1行目（修正対応）：数量は0より大きい値を入力してください。",
        "1行目（修正対応）：単価を入力してください。",
    ]


def test_項目が0件でもエラーにならない():
    result = check_items([])
    assert result.valid_indexes == []
    assert result.errors == []


def test_必須項目がすべて入力されている():
    items_result = check_items([row("デザイン制作", 1, "式", 50000)])
    assert check_required("株式会社〇〇", "〇〇デザイン事務所", items_result) == []


def test_必須項目が足りない():
    items_result = check_items([row()])
    assert check_required("", "  ", items_result) == [
        "宛先の名称",
        "発行者名・屋号",
        "見積もり項目（作業名・数量・単価を1行以上）",
    ]


def test_有効期限が発行日より前なら注意する():
    assert check_dates(date(2026, 10, 26), date(2026, 10, 25)) is not None
    assert check_dates(date(2026, 10, 26), date(2026, 10, 26)) is None
    assert check_dates(date(2026, 10, 26), date(2026, 11, 25)) is None
