
import backtrader as bt

"""
Três estratégias trend following para o case:

1) SmaCrossRiskATR
   - Entra comprado quando SMA(fast) cruza ACIMA da SMA(slow).
   - Sai quando cruza PARA BAIXO.
   - Tamanho = floor( equity * risk_perc / (atr_k * ATR) ).

2) DonchianBreakout
   - Entra comprado no breakout da máxima N (Highest(N)).
   - Sai quando fecha abaixo da mínima M (Lowest(M)).
   - Tamanho = floor( equity * risk_perc / (atr_k * ATR) ).

3) MomentumTF
   - Entra quando o retorno de lookback excede um limiar (threshold).
   - Sai quando momentum <= 0 (zeragem simples).
   - Tamanho = floor( equity * risk_perc / (atr_k * ATR) ).
"""


def _position_size_by_risk(strategy: bt.Strategy, atr_value: float, atr_k: float, risk_perc: float) -> int:
    """Calcula o tamanho da posição pelo risco (% do equity) e distância de stop (k * ATR)."""
    equity = float(strategy.broker.getvalue())
    atr = max(1e-6, float(atr_value))
    stop_distance = atr_k * atr
    if stop_distance <= 0:
        return 0
    size = int((equity * risk_perc) / stop_distance)
    return max(size, 0)


class SmaCrossRiskATR(bt.Strategy):
    params = dict(
        sma_fast=20,
        sma_slow=50,
        atr_window=14,
        atr_k=2.0,
        risk_perc=0.01, 
    )

    def __init__(self):
        close = self.datas[0].close
        self.sma_fast = bt.ind.SMA(close, period=self.p.sma_fast)
        self.sma_slow = bt.ind.SMA(close, period=self.p.sma_slow)
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)
        self.atr = getattr(self.datas[0], "atr", bt.ind.ATR(self.data, period=self.p.atr_window))

    def next(self):
        size = _position_size_by_risk(self, self.atr[0], self.p.atr_k, self.p.risk_perc)

        if not self.position:
            if self.crossover > 0 and size > 0:
                self.buy(size=size)
        else:
            if self.crossover < 0:
                self.close()


class DonchianBreakout(bt.Strategy):
    params = dict(
        n_high=20,          
        n_low=10,           
        atr_window=14,
        atr_k=2.0,
        risk_perc=0.01,
    )

    def __init__(self):
        self.dc_high = bt.ind.Highest(self.data.high, period=self.p.n_high)
        self.dc_low = bt.ind.Lowest(self.data.low, period=self.p.n_low)
        self.atr = getattr(self.datas[0], "atr", bt.ind.ATR(self.data, period=self.p.atr_window))

    def next(self):
        size = _position_size_by_risk(self, self.atr[0], self.p.atr_k, self.p.risk_perc)

        if not self.position:
            if self.data.close[0] > self.dc_high[0] and size > 0:
                self.buy(size=size)
        else:
            if self.data.close[0] < self.dc_low[0]:
                self.close()


class MomentumTF(bt.Strategy):
    params = dict(
        lookback=60,        
        threshold=0.0,      
        atr_window=14,
        atr_k=2.0,
        risk_perc=0.01,
    )

    def __init__(self):
        self.mom = (self.data.close / self.data.close(-self.p.lookback)) - 1.0
        self.atr = getattr(self.datas[0], "atr", bt.ind.ATR(self.data, period=self.p.atr_window))

    def next(self):
        size = _position_size_by_risk(self, self.atr[0], self.p.atr_k, self.p.risk_perc)
        mom_today = float(self.mom[0]) if self.mom[0] is not None else float("nan")

        if not self.position:
            if mom_today > self.p.threshold and size > 0:
                self.buy(size=size)
        else:
            if mom_today <= 0:
                self.close()
