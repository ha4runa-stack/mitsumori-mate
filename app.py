"""Mitsumori Mate の画面を作るファイル。

起動方法（ターミナルで実行）：
    streamlit run app.py

計算は calculator.py、入力チェックは validation.py、
見積もり項目の表の処理は items.py、見積書に載せる内容は document.py、
プレビューの表示は preview.py、PDFの作成は pdf_export.py にまとめている。
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from calculator import calc_estimate
from document import (
    DELIVERY_MODE_DATE,
    DELIVERY_MODE_TEXT,
    build_document,
    build_pdf_filename,
    format_yen,
)
from items import COLUMNS, initial_rows, rows_from_table
from pdf_export import build_pdf
from preview import render_preview_html
from validation import check_dates, check_items, check_required

# 有効期限を自動で設定するときの日数
EXPIRY_DAYS = 30

# 見積書に載せる入力欄の key の一覧
INPUT_KEYS = [
    "estimate_number",
    "issue_date",
    "expiry_date",
    "recipient_name",
    "recipient_honorific",
    "issuer_name",
    "issuer_address",
    "issuer_contact",
    "delivery_mode",
    "delivery_date",
    "delivery_text",
    "payment_terms",
    "remarks",
]


def init_state():
    """入力欄の初期値を st.session_state に用意する。

    st.session_state は、画面が更新されても値を保持しておく入れ物。
    すでに値がある場合（2回目以降の画面更新）は上書きしない。
    """
    today = date.today()
    defaults = {
        # 見積書番号の日付は、アプリを開いた日を使う
        "estimate_number": f"MM-{today:%Y%m%d}-001",
        "issue_date": today,
        "auto_expiry": True,
        "expiry_date": today + timedelta(days=EXPIRY_DAYS),
        "recipient_name": "",
        "recipient_honorific": "御中",
        "issuer_name": "",
        "issuer_address": "",
        "issuer_contact": "",
        "delivery_mode": DELIVERY_MODE_DATE,
        "delivery_date": None,
        "delivery_text": "",
        "payment_terms": "",
        "remarks": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Streamlit は、画面に表示されていない入力欄の値を自動で消してしまう。
    # 納期は入力方法を切り替えると片方の入力欄が表示されなくなるため、
    # 毎回値を入れ直して、切り替えても入力した内容が残るようにする。
    for key in ("delivery_date", "delivery_text"):
        st.session_state[key] = st.session_state[key]


def render_basic_info():
    """1. 見積書の基本情報"""
    st.subheader("1. 見積書の基本情報")
    st.text_input(
        "見積書番号",
        key="estimate_number",
        help="自動で入力されています。必要に応じて自由に変更できます。",
    )
    st.date_input("発行日", key="issue_date", format="YYYY/MM/DD")

    st.checkbox(f"有効期限を発行日の{EXPIRY_DAYS}日後に自動で設定する", key="auto_expiry")
    # チェックが入っている間は、発行日から有効期限を計算し直す。
    # 有効期限の入力欄を作る前に値を入れておく必要がある。
    if st.session_state["auto_expiry"] and st.session_state["issue_date"] is not None:
        st.session_state["expiry_date"] = st.session_state["issue_date"] + timedelta(
            days=EXPIRY_DAYS
        )
    st.date_input(
        "有効期限",
        key="expiry_date",
        format="YYYY/MM/DD",
        disabled=st.session_state["auto_expiry"],
        help="自分で日付を決めたいときは、上のチェックを外してください。",
    )

    date_warning = check_dates(st.session_state["issue_date"], st.session_state["expiry_date"])
    if date_warning:
        st.warning(date_warning)


def render_recipient():
    """2. 宛先情報"""
    st.subheader("2. 宛先情報")
    st.text_input(
        "宛先の名称 *",
        key="recipient_name",
        placeholder="例：株式会社〇〇、山田 太郎",
    )
    st.radio(
        "敬称",
        ["御中", "様"],
        key="recipient_honorific",
        horizontal=True,
        help="会社・団体宛ては「御中」、個人宛ては「様」が一般的です。",
    )


def render_issuer():
    """3. 発行者情報"""
    st.subheader("3. 発行者情報")
    st.text_input("発行者名・屋号 *", key="issuer_name", placeholder="例：〇〇デザイン事務所")
    st.text_area("住所", key="issuer_address", placeholder="必要な場合のみ入力してください")
    st.text_input("連絡先", key="issuer_contact", placeholder="例：電話番号、メールアドレス")


def render_items():
    """4. 見積もり項目

    入力された行の一覧と、そのチェック結果を返す。
    """
    st.subheader("4. 見積もり項目")
    st.caption(
        "表のマスをクリックして入力します。行は表の右上のボタンで追加・削除できます。"
        "金額は表の下に自動で表示されます。"
    )

    # 表の元になるデータ（最初の空欄3行）。毎回同じデータを渡すことで、
    # Streamlit が表を作り直さず、入力中のカーソルが外れないようにしている。
    # 利用者が入力した内容は、st.data_editor の戻り値として受け取る。
    base_table = pd.DataFrame(initial_rows(), columns=COLUMNS).astype(
        {"name": "object", "unit": "object", "quantity": "float64", "unit_price": "float64"}
    )
    edited_table = st.data_editor(
        base_table,
        key="items_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_order=COLUMNS,
        column_config={
            "name": st.column_config.TextColumn("作業名・商品名 *"),
            # 入力範囲は表では制限せず、validation.py でチェックして案内を表示する
            # （表で制限すると、範囲外の値が黙って直され、案内が出ないため）
            "quantity": st.column_config.NumberColumn(
                "数量 *", help="0.01〜99,999.99（小数第2位まで）"
            ),
            "unit": st.column_config.TextColumn("単位", help="例：式、回、時間"),
            "unit_price": st.column_config.NumberColumn(
                "単価（税抜）*", help="0〜999,999,999円（1円単位）", format="localized"
            ),
        },
    )
    rows = rows_from_table(edited_table)

    items_result = check_items(rows)
    if items_result.errors:
        st.error("入力内容を確認してください。\n\n" + "\n".join(f"- {m}" for m in items_result.errors))
    if items_result.notices:
        st.info("\n".join(f"- {m}" for m in items_result.notices))
    render_amounts(rows, items_result)
    return rows, items_result


def render_amounts(rows, items_result):
    """表の下に、行ごとの金額と小計を表示する。"""
    st.markdown("**金額（自動計算）**")
    if not items_result.valid_indexes:
        st.caption("作業名・数量・単価を入力すると、ここに金額が表示されます。")
        return

    valid_rows = [rows[index] for index in items_result.valid_indexes]
    summary = calc_estimate(valid_rows)
    amounts_table = pd.DataFrame(
        {
            "行": [f"{index + 1}行目" for index in items_result.valid_indexes],
            "作業名・商品名": [row["name"] for row in valid_rows],
            "金額": [format_yen(amount) for amount in summary["amounts"]],
        }
    )
    st.dataframe(
        amounts_table,
        hide_index=True,
        width="stretch",
        column_config={"金額": st.column_config.TextColumn(alignment="right")},
    )
    st.markdown(f"小計：**{format_yen(summary['subtotal'])}**（1円未満は四捨五入）")


def render_terms():
    """5. 納期・支払条件・備考"""
    st.subheader("5. 納期・支払条件・備考")
    st.radio(
        "納期の入力方法",
        [DELIVERY_MODE_DATE, DELIVERY_MODE_TEXT],
        key="delivery_mode",
        horizontal=True,
    )
    if st.session_state["delivery_mode"] == DELIVERY_MODE_DATE:
        st.date_input("納期", key="delivery_date", format="YYYY/MM/DD")
    else:
        st.text_input("納期", key="delivery_text", placeholder="例：ご発注から2週間以内")
    st.text_input("支払条件", key="payment_terms", placeholder="例：納品月の翌月末までに銀行振込")
    st.text_area("備考", key="remarks")


def render_preview(rows, items_result):
    """見積書プレビューと、PDF出力に必要な入力の確認を表示する。"""
    inputs = {key: st.session_state.get(key) for key in INPUT_KEYS}
    document = build_document(inputs, rows, items_result)

    st.subheader("見積書プレビュー")
    st.caption("入力した内容が、見積書の形でここに表示されます。")
    st.html(render_preview_html(document))

    missing = check_required(
        st.session_state["recipient_name"], st.session_state["issuer_name"], items_result
    )
    if items_result.errors:
        missing.append("見積もり項目の入力エラーの修正")
    if missing:
        st.warning(
            "PDFを出力するには、次の入力が必要です。\n\n" + "\n".join(f"- {m}" for m in missing)
        )
        st.button("PDFをダウンロード", type="primary", disabled=True, width="stretch")
    else:
        # 必須項目がそろっているときだけPDFを作る
        st.download_button(
            "PDFをダウンロード",
            data=build_pdf(document),
            file_name=build_pdf_filename(st.session_state["estimate_number"]),
            mime="application/pdf",
            type="primary",
            width="stretch",
        )


def main():
    st.set_page_config(page_title="Mitsumori Mate", page_icon="📄", layout="wide")
    init_state()

    st.title("Mitsumori Mate")
    st.markdown("**見積もり作成を、もっと簡単に。**")
    st.info("入力内容は保存されません。ページを再読み込みすると、入力した内容は消えます。")

    # PCでは左右に並び、スマートフォンなど幅が狭い画面では自動で縦に並ぶ
    form_column, preview_column = st.columns(2, gap="large")
    with form_column:
        st.caption("「*」が付いている項目は必須です。")
        render_basic_info()
        render_recipient()
        render_issuer()
        rows, items_result = render_items()
        render_terms()
    with preview_column:
        render_preview(rows, items_result)


# streamlit run app.py で起動したときだけ画面を作る（テストから読み込んだときは作らない）
if __name__ == "__main__":
    main()
