"""画面（app.py）の自動テスト。

Streamlit の AppTest（画面を開かずにアプリを動かして確認する仕組み）を使い、
requirements.md の「11. 動作確認・受け入れ条件」のうち、画面の操作で確認できるものを確かめる。
見積もり項目の表への直接入力は AppTest で再現できないため、ブラウザで確認する。
"""

from datetime import date, timedelta
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "app.py")
PROJECT_DIR = str(Path(__file__).parent.parent)


def run_app():
    return AppTest.from_file(APP_PATH, default_timeout=30).run()


def run_preview_with_items(rows, **inputs):
    """見積もり項目を入力した状態で、プレビューとPDFボタンの部分を動かす。"""
    script = f"""
import sys
sys.path.insert(0, {PROJECT_DIR!r})
import app
from validation import check_items
app.init_state()
rows = {rows!r}
app.render_preview(rows, check_items(rows))
"""
    at = AppTest.from_string(script, default_timeout=30)
    for key, value in inputs.items():
        at.session_state[key] = value
    return at.run()


def preview_html(at):
    return at.get("html")[0].proto.body


def test_初期表示():
    at = run_app()
    assert not at.exception
    today = date.today()
    assert at.text_input(key="estimate_number").value == f"MM-{today:%Y%m%d}-001"
    assert at.date_input(key="issue_date").value == today
    assert at.date_input(key="expiry_date").value == today + timedelta(days=30)
    assert at.checkbox(key="auto_expiry").value is True
    assert at.date_input(key="expiry_date").disabled is True
    assert any("保存されません" in info.value for info in at.info)


def test_発行日を変えると有効期限が自動で変わり番号は変わらない():
    at = run_app()
    number = at.text_input(key="estimate_number").value
    at.date_input(key="issue_date").set_value(date(2026, 12, 1)).run()
    assert at.date_input(key="expiry_date").value == date(2026, 12, 31)
    assert at.text_input(key="estimate_number").value == number


def test_手動で設定した有効期限は上書きされない():
    at = run_app()
    at.checkbox(key="auto_expiry").uncheck().run()
    assert at.date_input(key="expiry_date").disabled is False
    at.date_input(key="expiry_date").set_value(date(2027, 1, 15)).run()
    at.date_input(key="issue_date").set_value(date(2026, 12, 1)).run()
    assert at.date_input(key="expiry_date").value == date(2027, 1, 15)


def test_有効期限が発行日より前なら注意が出る():
    at = run_app()
    at.checkbox(key="auto_expiry").uncheck().run()
    at.date_input(key="expiry_date").set_value(date(2020, 1, 1)).run()
    assert any("有効期限が発行日より前" in warning.value for warning in at.warning)


def test_見積書番号は自由に編集できる():
    at = run_app()
    at.text_input(key="estimate_number").input("A-123").run()
    assert "A-123" in preview_html(at)


def test_敬称を選べる():
    at = run_app()
    assert at.radio(key="recipient_honorific").options == ["御中", "様"]
    at.text_input(key="recipient_name").input("山田 太郎")
    at.radio(key="recipient_honorific").set_value("様").run()
    assert "山田 太郎 様" in preview_html(at)


def test_納期は日付と文章のどちらでも入力でき切り替えても消えない():
    at = run_app()
    at.date_input(key="delivery_date").set_value(date(2026, 11, 30)).run()
    assert "2026年11月30日" in preview_html(at)
    at.radio(key="delivery_mode").set_value("文章で入力").run()
    at.text_input(key="delivery_text").input("ご発注から2週間以内").run()
    assert "ご発注から2週間以内" in preview_html(at)
    at.radio(key="delivery_mode").set_value("日付で指定").run()
    assert at.date_input(key="delivery_date").value == date(2026, 11, 30)


def test_項目がなく必須項目も未入力ならPDFボタンは押せない():
    at = run_app()
    assert not at.exception
    warning = next(w.value for w in at.warning if "PDFを出力するには" in w.value)
    assert "宛先の名称" in warning
    assert "発行者名・屋号" in warning
    assert "見積もり項目" in warning
    button = next(b for b in at.button if b.label == "PDFをダウンロード")
    assert button.disabled is True


def test_必須項目がそろうとPDFをダウンロードできる():
    rows = [{"name": "デザイン制作", "quantity": 1.0, "unit": "式", "unit_price": 50000.0}]
    at = run_preview_with_items(rows, recipient_name="株式会社テスト", issuer_name="テスト事務所")
    assert not at.exception
    assert len(at.get("download_button")) == 1
    assert "55,000円" in preview_html(at)


def test_項目に入力エラーがあるとPDFボタンは押せない():
    rows = [{"name": "デザイン制作", "quantity": 0.0, "unit": "式", "unit_price": 50000.0}]
    at = run_preview_with_items(rows, recipient_name="株式会社テスト", issuer_name="テスト事務所")
    assert not at.exception
    assert len(at.get("download_button")) == 0
    assert any("入力エラーの修正" in w.value for w in at.warning)
