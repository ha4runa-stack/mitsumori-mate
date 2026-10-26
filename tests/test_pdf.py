"""PDF出力（pdf_export.py と document.build_pdf_filename）の自動テスト。"""

from datetime import date

from document import build_document, build_pdf_filename
from pdf_export import build_pdf
from validation import check_items


def make_document(item_count):
    inputs = {
        "estimate_number": "MM-20261026-001",
        "issue_date": date(2026, 10, 26),
        "expiry_date": date(2026, 11, 25),
        "recipient_name": "株式会社テスト",
        "recipient_honorific": "御中",
        "issuer_name": "テスト事務所",
        "issuer_address": "東京都千代田区1-2-3\nテストビル4階",
        "issuer_contact": "",
        "delivery_mode": "文章で入力",
        "delivery_date": None,
        "delivery_text": "ご発注から2週間以内",
        "payment_terms": "",
        "remarks": "",
    }
    rows = [
        {"name": f"作業 {i}", "quantity": 1.5, "unit": "時間", "unit_price": 3333.0}
        for i in range(1, item_count + 1)
    ]
    return build_document(inputs, rows, check_items(rows))


def count_pages(pdf_bytes):
    return pdf_bytes.count(b"/Type /Page") - pdf_bytes.count(b"/Type /Pages")


def test_PDFを作れる():
    pdf_bytes = build_pdf(make_document(3))
    assert pdf_bytes.startswith(b"%PDF")
    assert count_pages(pdf_bytes) == 1


def test_項目が多いと複数ページになる():
    assert count_pages(build_pdf(make_document(60))) >= 2


def test_項目が0件でもPDFを作れる():
    assert build_pdf(make_document(0)).startswith(b"%PDF")


def test_ファイル名():
    assert build_pdf_filename("MM-20261026-001") == "見積書_MM-20261026-001.pdf"
    assert build_pdf_filename("") == "見積書.pdf"
    assert build_pdf_filename("   ") == "見積書.pdf"


def test_ファイル名に使えない文字は置き換える():
    assert build_pdf_filename("MM/001") == "見積書_MM_001.pdf"
    assert build_pdf_filename('a\\b:c*d?e"f<g>h|i') == "見積書_a_b_c_d_e_f_g_h_i.pdf"
