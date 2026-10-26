"""document.py と preview.py の自動テスト。"""

from datetime import date

from document import (
    DELIVERY_MODE_DATE,
    DELIVERY_MODE_TEXT,
    build_document,
    format_date,
    format_quantity,
    format_yen,
)
from preview import render_preview_html
from validation import check_items


def make_inputs(**overrides):
    inputs = {
        "estimate_number": "MM-20261026-001",
        "issue_date": date(2026, 10, 26),
        "expiry_date": date(2026, 11, 25),
        "recipient_name": "株式会社テスト",
        "recipient_honorific": "御中",
        "issuer_name": "テスト事務所",
        "issuer_address": "",
        "issuer_contact": "",
        "delivery_mode": DELIVERY_MODE_DATE,
        "delivery_date": None,
        "delivery_text": "",
        "payment_terms": "",
        "remarks": "",
    }
    inputs.update(overrides)
    return inputs


def make_rows():
    return [
        {"name": "デザイン制作", "quantity": 1.0, "unit": "式", "unit_price": 50000.0},
        {"name": None, "quantity": 2.0, "unit": "回", "unit_price": 5000.0},
        {"name": "打ち合わせ", "quantity": 1.5, "unit": None, "unit_price": 3333.0},
    ]


def build(inputs=None, rows=None):
    rows = make_rows() if rows is None else rows
    return build_document(inputs or make_inputs(), rows, check_items(rows))


def test_表示用の書式():
    assert format_yen(99000) == "99,000円"
    assert format_quantity(1.0) == "1"
    assert format_quantity(1.5) == "1.5"
    assert format_quantity(2.25) == "2.25"
    assert format_quantity(100.0) == "100"
    assert format_quantity(99999.99) == "99,999.99"
    assert format_date(date(2026, 1, 5)) == "2026年1月5日"


def test_見積書の内容():
    document = build()
    assert document["recipient"] == "株式会社テスト 御中"
    assert document["issue_date"] == "2026年10月26日"
    # 作業名が空欄の行は載せない
    assert [item["name"] for item in document["items"]] == ["デザイン制作", "打ち合わせ"]
    assert document["items"][1] == {
        "name": "打ち合わせ",
        "quantity": "1.5",
        "unit": "",
        "unit_price": "3,333円",
        "amount": "5,000円",
    }
    assert document["subtotal"] == "55,000円"
    assert document["tax_label"] == "消費税（10%）"
    assert document["tax"] == "5,500円"
    assert document["total"] == "60,500円"


def test_敬称を選べる():
    document = build(make_inputs(recipient_name="山田 太郎", recipient_honorific="様"))
    assert document["recipient"] == "山田 太郎 様"


def test_未入力の任意項目は空にする():
    document = build(make_inputs(estimate_number="  ", issuer_address=""))
    assert document["estimate_number"] is None
    assert document["issuer_address"] is None
    assert document["delivery"] is None
    assert document["remarks"] is None


def test_納期は入力方法に合わせて表示する():
    by_date = build(make_inputs(delivery_date=date(2026, 11, 30), delivery_text="無視される"))
    assert by_date["delivery"] == "2026年11月30日"
    by_text = build(
        make_inputs(delivery_mode=DELIVERY_MODE_TEXT, delivery_date=date(2026, 11, 30), delivery_text="ご発注から2週間以内")
    )
    assert by_text["delivery"] == "ご発注から2週間以内"


def test_項目が0件でもプレビューを作れる():
    document = build(rows=[])
    assert document["items"] == []
    assert document["total"] == "0円"
    assert "見積もり項目を入力すると" in render_preview_html(document)


def test_プレビューに入力内容が表示される():
    html = render_preview_html(build(make_inputs(remarks="1行目\n2行目")))
    assert "株式会社テスト 御中" in html
    assert "MM-20261026-001" in html
    assert "60,500円" in html
    assert "1行目<br>2行目" in html


def test_宛先の下に御見積金額を表示する():
    html = render_preview_html(build())
    assert '<span class="mm-grand-total-label">御見積金額</span>60,500円' in html
    assert html.index("株式会社テスト 御中") < html.index("御見積金額") < html.index("作業名・商品名")


def test_未入力の項目は見出しも表示しない():
    html = render_preview_html(build())
    assert "支払条件" not in html
    assert "備考" not in html


def test_入力した記号はHTMLとして解釈されない():
    html = render_preview_html(build(make_inputs(recipient_name="<b>A&B</b>")))
    assert "&lt;b&gt;A&amp;B&lt;/b&gt;" in html
    assert "<b>A&B</b>" not in html
