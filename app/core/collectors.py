import backtrader as bt

class TradeCollector(bt.Analyzer):
    """Coleta trades fechados (pnl já com comissão)."""
    def __init__(self):
        self.trades = []

    def notify_trade(self, trade):
        if trade.isclosed:
            d = self.strategy.data.datetime.date(0)
            # tamanho do evento inicial (positivo = buy, negativo = sell)
            size0 = trade.history[0].event.size if trade.history else 0
            side = "BUY" if size0 > 0 else "SELL"
            price = float(trade.history[0].status.price) if trade.history else float("nan")
            self.trades.append({
                "date": d,
                "side": side,
                "price": price,
                "size": int(abs(size0)),
                "pnl": float(trade.pnlcomm),
            })

    def get_analysis(self):
        return self.trades


class EquityDailyCollector(bt.Analyzer):
    """Coleta posição, caixa e equity a cada barra."""
    def __init__(self):
        self.daily = []

    def next(self):
        d = self.strategy.data.datetime.date(0)
        self.daily.append({
            "date": d,
            "position": int(self.strategy.position.size),
            "cash": float(self.strategy.broker.getcash()),
            "equity": float(self.strategy.broker.getvalue()),
        })

    def get_analysis(self):
        return self.daily