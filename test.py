from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.utils import iswrapper


class TestApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        self.nextOrderId = orderId
        print('The next valid order id is: ', self.nextOrderId)
        self.contract = Contract()
        self.contract.symbol = "ES"
        self.contract.secType = "FUT"
        self.contract.exchange = "CME"
        self.contract.currency = "USD"
        self.contract.lastTradeDateOrContractMonth = "202309"
   

        self.order = Order()
        self.order.action = "BUY"
        self.order.totalQuantity = 1
        self.order.orderType = "MKT"
        self.order.eTradeOnly=False
        self.order.firmQuoteOnly=False


        self.placeOrder(self.nextOrderId, self.contract, self.order)


def main():
    app = TestApp()

    app.connect("127.0.0.1", 7497, 8)

    app.run()


if __name__ == "__main__":
    main()
