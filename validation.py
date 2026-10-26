"""入力内容のチェックをまとめたファイル。

requirements.md の「4.1.9 入力内容のチェック」に従う。
チェック結果は、画面に表示する案内文（文字列）として返す。
"""

import math
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

# 数量・単価の入力範囲
QUANTITY_MIN = Decimal("0.01")
QUANTITY_MAX = Decimal("99999.99")
UNIT_PRICE_MIN = 0
UNIT_PRICE_MAX = 999_999_999


def is_empty(value):
    """値が未入力かどうかを判定する。

    表の空欄は None、数値の空欄は NaN（「数値ではない」を表す特別な値）になることがある。
    """
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _to_decimal_or_none(value):
    """数値に変換できれば Decimal を、できなければ None を返す。"""
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        return None
    # 「無限大」なども数値として扱わない
    if not number.is_finite():
        return None
    return number


def check_quantity(value):
    """数量をチェックし、問題があれば案内文を返す。問題がなければ None を返す。"""
    if is_empty(value):
        return "数量を入力してください。"
    number = _to_decimal_or_none(value)
    if number is None:
        return "数量は数字で入力してください。"
    if number <= 0:
        return "数量は0より大きい値を入力してください。"
    if number > QUANTITY_MAX:
        return "数量は99,999.99以下で入力してください。"
    if number != number.quantize(QUANTITY_MIN):
        return "数量は小数第2位まで入力してください。"
    return None


def check_unit_price(value):
    """単価をチェックし、問題があれば案内文を返す。問題がなければ None を返す。"""
    if is_empty(value):
        return "単価を入力してください。"
    number = _to_decimal_or_none(value)
    if number is None:
        return "単価は数字で入力してください。"
    if number < UNIT_PRICE_MIN:
        return "単価は0円以上で入力してください。"
    if number > UNIT_PRICE_MAX:
        return "単価は999,999,999円以下で入力してください。"
    if number != number.to_integral_value():
        return "単価は1円単位（整数）で入力してください。"
    return None


@dataclass
class ItemsCheckResult:
    """見積もり項目のチェック結果。"""

    # 計算に使える行の番号（0から数える）
    valid_indexes: list = field(default_factory=list)
    # 直す必要がある入力エラー
    errors: list = field(default_factory=list)
    # 作業名が空欄で計算に含めていない行の案内
    notices: list = field(default_factory=list)


def check_items(rows):
    """見積もり項目の全行をチェックする。

    - すべて空欄の行は、何も案内せずに無視する。
    - 作業名が空欄の行は、計算に含めず、その旨を案内する。
    - 作業名がある行は、数量と単価をチェックする。
    """
    result = ItemsCheckResult()

    for index, row in enumerate(rows):
        row_number = index + 1
        name = row.get("name")
        other_values = [row.get("quantity"), row.get("unit"), row.get("unit_price")]

        if is_empty(name):
            if not all(is_empty(value) for value in other_values):
                result.notices.append(
                    f"{row_number}行目：作業名が空欄のため、計算に含めていません。"
                )
            continue

        row_errors = [
            message
            for message in (check_quantity(row.get("quantity")), check_unit_price(row.get("unit_price")))
            if message is not None
        ]
        if row_errors:
            for message in row_errors:
                result.errors.append(f"{row_number}行目（{name.strip()}）：{message}")
        else:
            result.valid_indexes.append(index)

    return result


def check_required(recipient_name, issuer_name, items_result):
    """必須項目のうち、入力が足りないものの名前を一覧で返す。"""
    missing = []
    if is_empty(recipient_name):
        missing.append("宛先の名称")
    if is_empty(issuer_name):
        missing.append("発行者名・屋号")
    if not items_result.valid_indexes and not items_result.errors:
        missing.append("見積もり項目（作業名・数量・単価を1行以上）")
    return missing


def check_dates(issue_date, expiry_date):
    """有効期限が発行日より前の場合に、注意メッセージを返す。"""
    if issue_date is None or expiry_date is None:
        return None
    if expiry_date < issue_date:
        return "有効期限が発行日より前の日付になっています。日付をご確認ください。"
    return None
