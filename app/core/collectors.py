# app/core/collectors.py
import backtrader as bt

class TradeCollector(bt.Analyzer):
    """Coleta trades fechados com preço, size (>0) e pnl (com comissão)."""
    def start(self):
        self._rows = []

    def _first_event_size(self, trade):
        # tenta pegar o size do 1º evento com size != 0
        try:
            for h in trade.history:
                sz = None
                # alguns builds trazem .event.size; outros, .size
                if hasattr(h, "event") and getattr(h.event, "size", None):
                    sz = h.event.size
                elif hasattr(h, "size"):
                    sz = h.size
                if sz and sz != 0:
                    return int(sz)
        except Exception:
            pass
        return 0

    def _sum_abs_sizes(self, trade):
        # soma absoluta dos tamanhos executados no histórico
        total = 0
        try:
            for h in trade.history:
                sz = 0
                if hasattr(h, "event") and getattr(h.event, "size", None):
                    sz = h.event.size
                elif hasattr(h, "size"):
                    sz = h.size
                total += abs(int(sz or 0))
        except Exception:
            pass
        return int(total)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        # data do fechamento
        dt = bt.num2date(trade.dtclose).date().isoformat()

        # tenta inferir direção a partir do 1º evento
        sz0 = self._first_event_size(trade)
        if sz0 > 0:
            side_exit = "SELL"   # abriu LONG -> fecha com SELL
        elif sz0 < 0:
            side_exit = "BUY"    # abriu SHORT -> fecha com BUY
        else:
            # fallback: se não achou, deduza pelo pnl + movimento (último recurso)
            side_exit = "SELL" if trade.pnlcomm >= 0 else "BUY"

        # tenta preço do último evento; fallback = close da barra
        px = None
        try:
            if trade.history and getattr(trade.history[-1].status, "price", None):
                px = float(trade.history[-1].status.price)
        except Exception:
            px = None
        if px is None:
            px = float(self.strategy.data.close[0])

        # quantidade: soma absoluta dos eventos; se 0, force 1
        qty = self._sum_abs_sizes(trade)
        if qty == 0:
            qty = 1

        self._rows.append({
            "date": dt,
            "side": side_exit,
            "price": px,
            "size": int(qty),
            "pnl": float(trade.pnlcomm),
        })

    def get_analysis(self):
        return self._rows


class EquityDailyCollector(bt.Analyzer):
    """Série diária de posição, caixa e equity."""
    def start(self):
        self._rows = []

    def next(self):
        dt = bt.num2date(self.strategy.datas[0].datetime[0]).date().isoformat()
        self._rows.append({
            "date": dt,
            "position": int(self.strategy.position.size),
            "cash": float(self.strategy.broker.getcash()),
            "equity": float(self.strategy.broker.getvalue()),
        })

    def get_analysis(self):
        return self._rows
