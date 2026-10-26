"""見積書プレビューの HTML（Webページを作るための言語）を作るファイル。

document.build_document で作った内容を、見積書の形に並べる。
利用者が入力した文字は、そのまま HTML に入れると表示が崩れたり
意図しない動作につながったりするため、必ず escape（無害な文字に変換）してから入れる。
"""

from html import escape

# プレビューの見た目。class 名には「mm-」を付けて、Streamlit の画面と混ざらないようにする。
# 紙の見積書に近づけるため、画面がダークモードでも白い背景に黒い文字で表示する。
STYLE = """
<style>
.mm-paper {
    background: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    padding: 24px;
    font-size: 14px;
    line-height: 1.6;
}
.mm-title {
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 0.3em;
    margin: 0 0 20px;
}
.mm-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
}
.mm-recipient {
    font-size: 17px;
    font-weight: bold;
    border-bottom: 1px solid #1f2328;
    padding-bottom: 2px;
}
.mm-grand-total {
    display: inline-block;
    font-size: 20px;
    font-weight: bold;
    border-bottom: 3px double #1f2328;
    padding: 4px 8px 2px 0;
    margin-bottom: 20px;
}
.mm-grand-total-label {
    margin-right: 1em;
}
.mm-grand-total-note {
    font-size: 14px;
    font-weight: normal;
    margin-left: 0.3em;
}
.mm-meta, .mm-issuer {
    text-align: right;
}
.mm-meta div, .mm-issuer div {
    margin: 0;
}
.mm-issuer-name {
    font-weight: bold;
    margin-top: 8px;
}
.mm-table-wrap {
    overflow-x: auto;
}
.mm-items {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 12px;
}
.mm-items th, .mm-items td {
    border: 1px solid #8c959f;
    padding: 6px 8px;
}
.mm-items th {
    background: #eaeef2;
    font-weight: bold;
    text-align: center;
    white-space: nowrap;
}
.mm-num {
    text-align: right;
    white-space: nowrap;
}
.mm-empty {
    text-align: center;
    color: #57606a;
}
.mm-summary {
    margin-left: auto;
    border-collapse: collapse;
    min-width: 240px;
    margin-bottom: 20px;
}
.mm-summary th, .mm-summary td {
    padding: 4px 8px;
    border-bottom: 1px solid #d0d7de;
}
.mm-summary th {
    text-align: left;
    font-weight: normal;
}
.mm-summary .mm-total th, .mm-summary .mm-total td {
    font-size: 17px;
    font-weight: bold;
    border-top: 2px solid #1f2328;
    border-bottom: 2px solid #1f2328;
}
.mm-terms dt {
    font-weight: bold;
    margin-top: 8px;
}
.mm-terms dd {
    margin: 0 0 0 1em;
}
</style>
"""


def text(value):
    """入力された文字を escape し、改行を HTML の改行に変える。"""
    return escape(value).replace("\n", "<br>")


def render_meta(document):
    """見積書番号・発行日・有効期限（入力されているものだけ）。"""
    lines = []
    if document["estimate_number"]:
        lines.append(f"<div>見積書番号：{text(document['estimate_number'])}</div>")
    if document["issue_date"]:
        lines.append(f"<div>発行日：{text(document['issue_date'])}</div>")
    if document["expiry_date"]:
        lines.append(f"<div>有効期限：{text(document['expiry_date'])}</div>")
    return "".join(lines)


def render_issuer(document):
    """発行者情報（入力されているものだけ）。"""
    lines = []
    if document["issuer_name"]:
        lines.append(f'<div class="mm-issuer-name">{text(document["issuer_name"])}</div>')
    if document["issuer_address"]:
        lines.append(f"<div>{text(document['issuer_address'])}</div>")
    if document["issuer_contact"]:
        lines.append(f"<div>{text(document['issuer_contact'])}</div>")
    return "".join(lines)


def render_grand_total(document):
    """宛先の下に大きく表示する御見積金額（合計金額・税込）。"""
    return (
        '<div class="mm-grand-total">'
        '<span class="mm-grand-total-label">御見積金額</span>'
        f'{text(document["total"])}<span class="mm-grand-total-note">（税込）</span>'
        "</div>"
    )


def render_items(document):
    """見積もり項目の表。"""
    if document["items"]:
        rows = "".join(
            "<tr>"
            f"<td>{text(item['name'])}</td>"
            f'<td class="mm-num">{text(item["quantity"])}</td>'
            f"<td>{text(item['unit'])}</td>"
            f'<td class="mm-num">{text(item["unit_price"])}</td>'
            f'<td class="mm-num">{text(item["amount"])}</td>'
            "</tr>"
            for item in document["items"]
        )
    else:
        rows = '<tr><td class="mm-empty" colspan="5">見積もり項目を入力すると、ここに表示されます。</td></tr>'
    return (
        '<div class="mm-table-wrap"><table class="mm-items">'
        "<thead><tr><th>作業名・商品名</th><th>数量</th><th>単位</th><th>単価</th><th>金額</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


def render_summary(document):
    """小計・消費税・合計金額。"""
    return (
        '<table class="mm-summary">'
        f'<tr><th>小計</th><td class="mm-num">{text(document["subtotal"])}</td></tr>'
        f'<tr><th>{text(document["tax_label"])}</th><td class="mm-num">{text(document["tax"])}</td></tr>'
        f'<tr class="mm-total"><th>合計金額</th><td class="mm-num">{text(document["total"])}</td></tr>'
        "</table>"
    )


def render_terms(document):
    """納期・支払条件・備考（入力されているものだけ）。"""
    terms = [
        ("納期", document["delivery"]),
        ("支払条件", document["payment_terms"]),
        ("備考", document["remarks"]),
    ]
    entries = "".join(
        f"<dt>{label}</dt><dd>{text(value)}</dd>" for label, value in terms if value
    )
    if not entries:
        return ""
    return f'<dl class="mm-terms">{entries}</dl>'


def render_preview_html(document):
    """見積書プレビュー全体の HTML を作る。"""
    recipient = (
        f'<div class="mm-recipient">{text(document["recipient"])}</div>' if document["recipient"] else "<div></div>"
    )
    return (
        STYLE
        + '<div class="mm-paper">'
        + f'<div class="mm-title">{text(document["title"])}</div>'
        + '<div class="mm-header">'
        + recipient
        + f'<div><div class="mm-meta">{render_meta(document)}</div>'
        + f'<div class="mm-issuer">{render_issuer(document)}</div></div>'
        + "</div>"
        + render_grand_total(document)
        + render_items(document)
        + render_summary(document)
        + render_terms(document)
        + "</div>"
    )
