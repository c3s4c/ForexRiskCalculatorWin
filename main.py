from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import requests
import MetaTrader5 as mt5

class ForexRiskCalculator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("محاسبه‌گر ریسک و حجم معامله فارکس")
        self.setGeometry(300, 100, 550, 400)
        self.setStyleSheet("background-color: #1e1e2f; color: white;")
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("محاسبه حجم معامله با توجه به ریسک")
        title.setFont(QtGui.QFont("B Nazanin", 16, QtGui.QFont.Bold))
        title.setStyleSheet("color: cyan;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        form_layout = QtWidgets.QFormLayout()

        self.capital_input = QtWidgets.QLineEdit()
        self.capital_input.setPlaceholderText("مقدار سرمایه به دلار")
        form_layout.addRow("سرمایه ($):", self.capital_input)

        self.risk_input = QtWidgets.QLineEdit()
        self.risk_input.setPlaceholderText("درصد ریسک")
        form_layout.addRow("درصد ریسک (%):", self.risk_input)

        self.stop_input = QtWidgets.QLineEdit()
        self.stop_input.setPlaceholderText("استاپ لاس به پیپ")
        form_layout.addRow("استاپ لاس (پیپ):", self.stop_input)

        self.pair_combo = QtWidgets.QComboBox()
        self.pairs = [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
            "AUD/USD", "USD/CAD", "NZD/USD", "EUR/GBP",
            "EUR/JPY", "GBP/JPY", "CHF/JPY", "AUD/JPY",
            "XAU/USD", "XAG/USD", "DJI", "SPX", "NDX", "US30"
        ]
        self.pair_combo.addItems(self.pairs)
        self.pair_combo.currentTextChanged.connect(self.toggle_price_input)
        form_layout.addRow("جفت‌ارز:", self.pair_combo)

        self.price_input = QtWidgets.QLineEdit()
        self.price_input.setPlaceholderText("قیمت جفت‌ارز")
        form_layout.addRow("قیمت جفت‌ارز:", self.price_input)

        self.price_source = QtWidgets.QComboBox()
        self.price_source.addItems(["دریافت آنلاین", "ورود دستی", "متاتریدر"])
        self.price_source.currentIndexChanged.connect(self.toggle_price_input)
        form_layout.addRow("نوع دریافت قیمت:", self.price_source)

        layout.addLayout(form_layout)

        self.calc_btn = QtWidgets.QPushButton("محاسبه حجم معامله")
        self.calc_btn.setStyleSheet("background-color: #007acc; color: white; font-weight: bold;")
        self.calc_btn.clicked.connect(self.calculate_position_size)
        layout.addWidget(self.calc_btn)

        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("color: cyan;")
        self.result_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)
        self.toggle_price_input()

    def toggle_price_input(self):
        pair = self.pair_combo.currentText()
        mode = self.price_source.currentText()

        if pair in ["XAU/USD", "XAG/USD", "DJI", "SPX", "NDX", "US30"]:
            self.price_source.setCurrentText("متاتریدر")
            self.price_source.setDisabled(True)
            self.price_input.setDisabled(True)
        else:
            self.price_source.setDisabled(False)
            self.price_input.setDisabled(mode != "ورود دستی")

    def get_price_online(self, pair):
        url = f"https://api.twelvedata.com/price?symbol={pair}&apikey=ad92b5d3c6564f14b4948f75dcd8bba6"
        try:
            response = requests.get(url)
            data = response.json()
            return round(float(data['price']), 5)
        except:
            return None

    def get_price_metatrader(self, pair):
        symbol = pair.replace("/", "")
        try:
            if not mt5.initialize():
                return None, None, None, None
            if not mt5.symbol_select(symbol, True):
                mt5.shutdown()
                return None, None, None, None
            tick = mt5.symbol_info_tick(symbol)
            info = mt5.symbol_info(symbol)
            price = tick.bid if tick else None
            lot_size = info.trade_contract_size if info else 100000
            pip = info.point if info else 0.0001
            tick_value = info.trade_tick_value if info else None
            mt5.shutdown()
            return round(price, 5) if price else None, lot_size, pip, tick_value
        except:
            return None, None, None

    def calculate_position_size(self):
        try:
            capital = float(self.capital_input.text())
            risk_percent = float(self.risk_input.text())
            stop_loss = float(self.stop_input.text())
            pair = self.pair_combo.currentText()
            mode = self.price_source.currentText()

            # تعیین قیمت، لات سایز، پیپ
            if mode == "دریافت آنلاین":
                price = self.get_price_online(pair)
                if price is None:
                    self.result_label.setText("قیمت دریافت نشد.")
                    return
                pip = 0.01 if pair.endswith("JPY") else 0.0001
                lot_size = 100000
            elif mode == "متاتریدر":
                price, lot_size, pip, tick_value = self.get_price_metatrader(pair)
                if price is None:
                    self.result_label.setText("قیمت از متاتریدر دریافت نشد.")
                    return
            else:
                price = float(self.price_input.text())
                pip = 0.01 if pair.endswith("JPY") else 0.0001
                lot_size = 100000

            pip_value_per_lot = tick_value / pip if mode == "متاتریدر" and tick_value and pip else (pip * lot_size) / price if price != 1.0 else pip * lot_size
            risk_amount = capital * (risk_percent / 100)
            pip_value_needed = risk_amount / stop_loss
            position_lot = pip_value_needed / pip_value_per_lot

            self.result_label.setText(f"حجم مناسب معامله: {round(position_lot, 3)} لات\nریسک دلاری: {round(risk_amount, 2)} دلار\nقیمت فعلی: {round(price, 5)}")
        except Exception as e:
            self.result_label.setText(f"خطا در محاسبه: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ForexRiskCalculator()
    window.show()
    sys.exit(app.exec_())
