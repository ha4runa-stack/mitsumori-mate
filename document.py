"""見積書に載せる内容をまとめるファイル。

入力内容から「見積書に表示する文字」を作る。
プレビューとPDFは、どちらもここで作った内容を使って表示するため、
掲載内容が一致する（requirements.md の 4.1.8）。

未入力の任意項目は None にしておき、表示側で None の項目は表示しない。
"""

import re
from decimal import Decimal

from calculator import TAX_RATE, calc_estimate
from validation import is_empty

TITLE = "御見積書"

DELIVERY_MODE_DATE = "日付で指定"
DELIVERY_MODE_TEXT = "文章で入力"

# Windows のファイル名に使えない文字
INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def format_yen(amount):
    """金額を「90,000円」のような桁区切り付きの文字列にする。"""
    return f"{amount:,}円"


def format_quantity(quantity):
    """数量を表示用の文字列にする（例：1.0 → "1"、2.50 → "2.5"）。"""
    text = format(Decimal(str(quantity)).quantize(Decimal("0.01")), ",f")
    # 小数点以下の不要な 0 を取り除く
    return text.rstrip("0").rstrip(".")


def format_date(value):
    """日付を「2026年10月26日」の形式にする。"""
    if value is None:
        return None
    return f"{value.year}年{value.month}月{value.day}日"


def clean_text(value):
    """文字列の前後の空白を取り除く。空欄なら None を返す。"""
    if is_empty(value):
        return None
    return str(value).strip()


def build_delivery(inputs):
    """納期の表示用の文字列を作る。"""
    if inputs.get("delivery_mode") == DELIVERY_MODE_TEXT:
        return clean_text(inputs.get("delivery_text"))
    return format_date(inputs.get("delivery_date"))


def build_recipient(inputs):
    """宛先を敬称付きで作る（例：「株式会社〇〇 御中」）。"""
    name = clean_text(inputs.get("recipient_name"))
    if name is None:
        return None
    return f"{name} {inputs.get('recipient_honorific', '御中')}"


def build_pdf_filename(estimate_number):
    """PDFのファイル名を作る。

    見積書番号があれば「見積書_見積書番号.pdf」、空欄なら「見積書.pdf」とする。
    ファイル名に使えない文字は「_」に置き換える（PDF内の表示はそのまま）。
    """
    number = clean_text(estimate_number)
    if number is None:
        return "見積書.pdf"
    return f"見積書_{INVALID_FILENAME_CHARS.sub('_', number)}.pdf"


def build_document(inputs, rows, items_result):
    """見積書に表示する内容を辞書にまとめる。

    inputs       : 入力欄の値（キーは app.py の入力欄の key と同じ）
    rows         : 見積もり項目の行の一覧
    items_result : validation.check_items の結果
    """
    valid_rows = [rows[index] for index in items_result.valid_indexes]
    summary = calc_estimate(valid_rows)

    items = []
    for row, amount in zip(valid_rows, summary["amounts"]):
        items.append(
            {
                "name": clean_text(row["name"]),
                "quantity": format_quantity(row["quantity"]),
                "unit": clean_text(row.get("unit")) or "",
                "unit_price": format_yen(int(row["unit_price"])),
                "amount": format_yen(amount),
            }
        )

    return {
        "title": TITLE,
        "estimate_number": clean_text(inputs.get("estimate_number")),
        "issue_date": format_date(inputs.get("issue_date")),
        "expiry_date": format_date(inputs.get("expiry_date")),
        "recipient": build_recipient(inputs),
        "issuer_name": clean_text(inputs.get("issuer_name")),
        "issuer_address": clean_text(inputs.get("issuer_address")),
        "issuer_contact": clean_text(inputs.get("issuer_contact")),
        "items": items,
        "subtotal": format_yen(summary["subtotal"]),
        "tax_label": f"消費税（{int(TAX_RATE * 100)}%）",
        "tax": format_yen(summary["tax"]),
        "total": format_yen(summary["total"]),
        "delivery": build_delivery(inputs),
        "payment_terms": clean_text(inputs.get("payment_terms")),
        "remarks": clean_text(inputs.get("remarks")),
    }
