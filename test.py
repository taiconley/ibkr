
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class TestWrapper(EWrapper):
    def __init__(self)


    def realtimeBar(self, reqId: TickerId, time:int, open_: float, high: float, low: float, close: float, volume: Decimal, wap: Decimal, count: int):
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        print("RealTimeBar. TickerId:", reqId, RealTimeBar(time, -1, open_, high, low, close, volume, wap, count))