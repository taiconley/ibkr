from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time


class IBKRConnection(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print(f"Error: {reqId}, {errorCode}, {errorString}")

    def nextValidId(self, orderId):
        self.next_order_id = orderId
        print(f"The next valid order id is: {self.next_order_id}")


def main():
    app = IBKRConnection()
    app.connect("127.0.0.1", 7497, clientId=0)

    # Start a separate thread to process the incoming messages from TWS
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # Give the API connection a moment to initialize
    time.sleep(1)

    # Do your tasks here, like requesting market data, placing orders, etc.

    # Disconnect after completing the tasks
    app.disconnect()


if __name__ == "__main__":
    main()
