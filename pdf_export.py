"""見積書のPDFを作るファイル。

document.build_document で作った内容をもとに、A4縦のPDFを作る。
プレビューと同じ内容を使うため、掲載内容が一致する。

PDFの作成には fpdf2 というライブラリを使う。
日本語が文字化けしないよう、fonts フォルダの BIZ UDゴシック をPDFに埋め込む。
（フォントのライセンス：fonts/OFL.txt）
"""

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import WrapMode
from fpdf.fonts import FontFace

FONT_DIR = Path(__file__).parent / "fonts"
FONT_FAMILY = "BIZUDGothic"

# 余白と本文の幅（単位：mm）。A4の幅は210mm。
MARGIN = 15
CONTENT_WIDTH = 210 - MARGIN * 2

TEXT_COLOR = (31, 35, 40)
BORDER_COLOR = (140, 149, 159)
HEADING_FILL = (234, 238, 242)

# 見積もり項目の表の列：見出し、幅（mm）、文字のそろえ方
ITEM_COLUMNS = [
    ("作業名・商品名", 79, "LEFT"),
    ("数量", 21, "RIGHT"),
    ("単位", 18, "LEFT"),
    ("単価", 31, "RIGHT"),
    ("金額", 31, "RIGHT"),
]


class EstimatePDF(FPDF):
    """見積書用のPDF。各ページの下にページ番号を付ける。"""

    def footer(self):
        self.set_y(-12)
        self.set_font(FONT_FAMILY, size=9)
        # {nb} は、PDFを作り終えたときに総ページ数に置き換わる
        self.cell(0, 6, f"{self.page_no()} / {{nb}}", align="C")


def create_pdf():
    """フォントや余白を設定した、空のPDFを作る。"""
    pdf = EstimatePDF(orientation="P", unit="mm", format="A4")
    pdf.add_font(FONT_FAMILY, style="", fname=FONT_DIR / "BIZUDGothic-Regular.ttf")
    pdf.add_font(FONT_FAMILY, style="B", fname=FONT_DIR / "BIZUDGothic-Bold.ttf")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    # 下から20mmの位置まで来たら、自動で次のページに移る
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_text_color(*TEXT_COLOR)
    pdf.set_draw_color(*BORDER_COLOR)
    pdf.set_creator("Mitsumori Mate")
    return pdf


def draw_title(pdf, document):
    """タイトル（御見積書）。"""
    pdf.set_font(FONT_FAMILY, style="B", size=20)
    pdf.set_char_spacing(4)
    pdf.cell(0, 12, document["title"], align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_char_spacing(0)
    pdf.ln(6)


def draw_right_block(pdf, document, top):
    """右上：見積書番号・発行日・有効期限と、発行者情報。描き終えた位置（高さ）を返す。"""
    width = 75
    x = MARGIN + CONTENT_WIDTH - width
    pdf.set_xy(x, top)

    pdf.set_font(FONT_FAMILY, size=10)
    for label, key in (("見積書番号", "estimate_number"), ("発行日", "issue_date"), ("有効期限", "expiry_date")):
        if document[key]:
            pdf.set_x(x)
            pdf.multi_cell(width, 5.5, f"{label}：{document[key]}", align="R", new_x="LEFT", new_y="NEXT", wrapmode=WrapMode.CHAR)

    pdf.ln(3)
    if document["issuer_name"]:
        pdf.set_x(x)
        pdf.set_font(FONT_FAMILY, style="B", size=11)
        pdf.multi_cell(width, 6, document["issuer_name"], align="R", new_x="LEFT", new_y="NEXT", wrapmode=WrapMode.CHAR)
    pdf.set_font(FONT_FAMILY, size=10)
    for key in ("issuer_address", "issuer_contact"):
        if document[key]:
            pdf.set_x(x)
            pdf.multi_cell(width, 5.5, document[key], align="R", new_x="LEFT", new_y="NEXT", wrapmode=WrapMode.CHAR)
    return pdf.get_y()


def draw_left_block(pdf, document, top):
    """左上：宛先と御見積金額。描き終えた位置（高さ）を返す。"""
    width = 98
    pdf.set_xy(MARGIN, top)

    if document["recipient"]:
        pdf.set_font(FONT_FAMILY, style="B", size=14)
        pdf.multi_cell(width, 8, document["recipient"], new_x="LMARGIN", new_y="NEXT", wrapmode=WrapMode.CHAR)
        pdf.set_draw_color(*TEXT_COLOR)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + width, pdf.get_y())
        pdf.set_draw_color(*BORDER_COLOR)
    pdf.ln(8)

    pdf.set_font(FONT_FAMILY, style="B", size=16)
    pdf.cell(28, 10, "御見積金額")
    pdf.cell(50, 10, document["total"], align="R")
    pdf.set_font(FONT_FAMILY, size=10)
    pdf.cell(20, 10, "（税込）", new_x="LMARGIN", new_y="NEXT")
    # 二重線の下線
    pdf.set_draw_color(*TEXT_COLOR)
    y = pdf.get_y()
    pdf.line(MARGIN, y, MARGIN + width, y)
    pdf.line(MARGIN, y + 0.8, MARGIN + width, y + 0.8)
    pdf.set_draw_color(*BORDER_COLOR)
    return pdf.get_y() + 1


def draw_items(pdf, document):
    """見積もり項目の表。ページをまたぐときは、次のページにも見出しを付ける。"""
    pdf.set_font(FONT_FAMILY, size=10)
    with pdf.table(
        width=CONTENT_WIDTH,
        col_widths=[width for _, width, _ in ITEM_COLUMNS],
        text_align=[align for _, _, align in ITEM_COLUMNS],
        headings_style=FontFace(emphasis="BOLD", fill_color=HEADING_FILL),
        line_height=6,
        padding=1.5,
        repeat_headings=1,
        # 日本語は単語の区切りに空白がないため、1文字単位で折り返す
        wrapmode=WrapMode.CHAR,
    ) as table:
        heading = table.row()
        for label, _, _ in ITEM_COLUMNS:
            heading.cell(label, align="CENTER")
        if not document["items"]:
            table.row().cell("見積もり項目はありません。", colspan=len(ITEM_COLUMNS), align="CENTER")
        for item in document["items"]:
            row = table.row()
            for key in ("name", "quantity", "unit", "unit_price", "amount"):
                row.cell(item[key])
    pdf.ln(4)


def draw_summary(pdf, document):
    """小計・消費税・合計金額（表の右下）。"""
    pdf.set_font(FONT_FAMILY, size=11)
    bold = FontFace(emphasis="BOLD")
    with pdf.table(
        width=80,
        col_widths=[40, 40],
        text_align=["LEFT", "RIGHT"],
        align="RIGHT",
        first_row_as_headings=False,
        line_height=7,
        padding=1.5,
    ) as table:
        for label, value in (("小計", document["subtotal"]), (document["tax_label"], document["tax"])):
            row = table.row()
            row.cell(label)
            row.cell(value)
        row = table.row(style=bold)
        row.cell("合計金額")
        row.cell(document["total"])
    pdf.ln(6)


def draw_terms(pdf, document):
    """納期・支払条件・備考（入力されているものだけ）。"""
    for label, key in (("納期", "delivery"), ("支払条件", "payment_terms"), ("備考", "remarks")):
        if not document[key]:
            continue
        pdf.set_font(FONT_FAMILY, style="B", size=10)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(FONT_FAMILY, size=10)
        pdf.set_x(MARGIN + 4)
        pdf.multi_cell(CONTENT_WIDTH - 4, 5.5, document[key], new_x="LMARGIN", new_y="NEXT", wrapmode=WrapMode.CHAR)
        pdf.ln(2)


def build_pdf(document):
    """見積書のPDFを作り、ファイルの中身（バイト列）を返す。"""
    pdf = create_pdf()
    pdf.set_title(document["title"])
    pdf.add_page()

    draw_title(pdf, document)
    top = pdf.get_y()
    right_end = draw_right_block(pdf, document, top)
    left_end = draw_left_block(pdf, document, top)
    pdf.set_y(max(left_end, right_end) + 8)

    draw_items(pdf, document)
    draw_summary(pdf, document)
    draw_terms(pdf, document)
    return bytes(pdf.output())
