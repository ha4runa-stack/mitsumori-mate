"""calculator.py の自動テスト（requirements.md の 7.7 に対応）。"""

from calculator import calc_estimate, calc_item_amount, calc_tax


def test_計算例1_端数が出ない場合():
    items = [
        {"quantity": 1, "unit_price": 50000},
        {"quantity": 1, "unit_price": 30000},
        {"quantity": 2, "unit_price": 5000},
    ]
    result = calc_estimate(items)
    assert result["amounts"] == [50000, 30000, 10000]
    assert result["subtotal"] == 90000
    assert result["tax"] == 9000
    assert result["total"] == 99000


def test_計算例2_端数が出る場合():
    items = [
        {"quantity": 1.5, "unit_price": 3333},
        {"quantity": 2.25, "unit_price": 4445},
    ]
    result = calc_estimate(items)
    assert result["amounts"] == [5000, 10001]
    assert result["subtotal"] == 15001
    assert result["tax"] == 1500
    assert result["total"] == 16501


def test_金額は0円50銭ちょうどで切り上げる():
    assert calc_item_amount(0.5, 1) == 1
    # 一般的な四捨五入なので、2.5は3になる（Pythonのround()では2になる）
    assert calc_item_amount(2.5, 1) == 3


def test_金額は0円50銭未満で切り捨てる():
    assert calc_item_amount(0.01, 49) == 0


def test_小数の誤差で四捨五入がずれない():
    # float では 0.29 * 50 = 14.499999... になるが、正しくは 14.5 → 15
    assert calc_item_amount(0.29, 50) == 15


def test_消費税は1円未満を切り捨てる():
    assert calc_tax(999) == 99
    assert calc_tax(1009) == 100


def test_数量に小数を含む計算():
    assert calc_item_amount(1.5, 1000) == 1500
    assert calc_item_amount(0.01, 100) == 1


def test_項目が0件でも0円になる():
    result = calc_estimate([])
    assert result == {"amounts": [], "subtotal": 0, "tax": 0, "total": 0}


def test_入力上限の値でも正しく計算される():
    result = calc_estimate([{"quantity": 99999.99, "unit_price": 999_999_999}])
    # 99,999.99 × 999,999,999 = 99,999,989,900,000.01 → 四捨五入で .01 を切り捨て
    assert result["subtotal"] == 99_999_989_900_000
    assert result["tax"] == 9_999_998_990_000
    assert result["total"] == 109_999_988_890_000
