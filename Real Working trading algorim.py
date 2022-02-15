from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance.enums import *
import decimal


class PositionStatus:
    base_asset = "XXX"
    base_asset_min_step = 0.01
    quote_asset = "XXX"
    quote_asset_min_step = 0.01
    status_activated = False
    start_index = float(0)
    current_index = float(0)
    entry_price = float(0)
    long_status = True
    stop_limit = float(0)
    stop_loss_order_id = float(0)
    take_profit_order_id = float(0)

    def get_total_coin_dept(self):

        for i in client.get_isolated_margin_account(symbol=self.getSymbol()).get("assets"):
            symbolForTrade = i.get("baseAsset").get("asset") + i.get("quoteAsset").get("asset")
            coinAmount = float(i.get("baseAsset").get("borrowed"))

            if symbolForTrade in self.getSymbol() and self.getSymbol() in symbolForTrade:
                return self.getFormatedCoinAmount(coinAmount)

    def getFormatedCoinAmount(self, fullvalue):
        def getLotSize(symbol):
            data = client.get_symbol_info(symbol=symbol)
            filters = data.get("filters")
            for i in filters:
                filterType = i.get("filterType")
                if filterType in "LOT_SIZE" and "LOT_SIZE" in filterType:
                    self.base_asset_min_step = float(i.get("minQty"))
                    return self.base_asset_min_step

        def round_down(value, decimals):
            with decimal.localcontext() as ctx:
                d = decimal.Decimal(value)
                ctx.rounding = decimal.ROUND_DOWN
                return round(d, decimals)

        def convertLotSizetoDecimals(lotsize):
            counter = 0
            while lotsize != 1:
                lotsize = lotsize * 10
                counter = counter + 1
            return counter

        return round_down(fullvalue, convertLotSizetoDecimals(float(getLotSize(self.getSymbol()))))

    def getFormatedUSDAmount(self, fullvalue):
        def getLotSize(symbol):
            data = client.get_symbol_info(symbol=symbol)
            for i in data.get("filters"):
                if i.get("filterType") in "PRICE_FILTER":
                    self.quote_asset_min_step = float((i.get("minPrice")))
                    return self.quote_asset_min_step

        def round_down(value, decimals):
            with decimal.localcontext() as ctx:
                d = decimal.Decimal(value)
                ctx.rounding = decimal.ROUND_DOWN
                return round(d, decimals)

        def convertLotSizetoDecimals(lotsize):
            counter = 0
            while lotsize != 1:
                lotsize = lotsize * 10
                counter = counter + 1
            return counter

        return round_down(fullvalue, convertLotSizetoDecimals(float(getLotSize(self.getSymbol()))))

    def getBuyableCoinAmout(self):
        try:
            coinPrice = client.get_symbol_ticker(symbol=self.getSymbol())

            return self.getFormatedCoinAmount(0.98 * (self.getCurrentUsdAmount() / float(coinPrice['price'])))
        except Exception as inst:
            print(inst)
            print("getBuyableCoinAmout error")

    def getSymbol(self):
        return self.base_asset + self.quote_asset

    def getUsdLimitToBarrow(self):
        details = client.get_max_margin_loan(asset=self.quote_asset, isolatedSymbol=self.getSymbol())
        return details.get("amount")

    def getCoinLimitToBarrow(self):
        # get max baroow amount for Coin
        details = client.get_max_margin_loan(asset=self.base_asset, isolatedSymbol=self.getSymbol())
        return details.get("amount")

    def getCurrentCoinAmount(self):

        for i in client.get_isolated_margin_account(symbol=self.getSymbol()).get("assets"):
            symbolForTrade = i.get("baseAsset").get("asset") + i.get("quoteAsset").get("asset")
            coinAmount = float(i.get("baseAsset").get("free"))

            if symbolForTrade in self.getSymbol() and self.getSymbol() in symbolForTrade:
                return self.getFormatedCoinAmount(coinAmount)

    def getCurrentUsdAmount(self):
        for i in client.get_isolated_margin_account(symbol=self.getSymbol()).get("assets"):

            symbolForTrade = i.get("baseAsset").get("asset") + i.get("quoteAsset").get("asset")
            coinAmount = float(i.get("baseAsset").get("free"))
            usdAmount = float(i.get("quoteAsset").get("free"))
            print(symbolForTrade)
            print(self.getSymbol())
            if symbolForTrade in self.getSymbol() and self.getSymbol() in symbolForTrade:
                print("i am happy")
                return usdAmount

    def write(self):
        total = "base_asset =" \
                "" + self.base_asset + ",quote_asset =" \
                                       "" + self.quote_asset + ",status_activated =" \
                                                               "" + str(self.status_activated) + ",start_index =" \
                                                                                                 "" + str(
            self.start_index) + ",entry_price =" \
                                "" + str(self.entry_price) + ",long_status =" \
                                                             "" + str(self.long_status) + ",stop_limit =" \
                                                                                          "" + str(
            self.stop_limit) + ",stop_loss_order_id =" \
                               "" + str(self.stop_loss_order_id) + str(self.long_status) + ",stop_limit =" \
                                                                                           "" + str(
            self.stop_limit) + ",take_profit_order_id =" \
                               "" + str(self.take_profit_order_id)
        with open('PositionStatus.txt', 'w') as f:
            f.write(total)


client = Client("Secred",
                "secred")
positionStatus = PositionStatus()


def sortCoin():
    barrowMaxCoin()

    order = client.create_margin_order(
        isIsolated='TRUE',
        symbol=positionStatus.getSymbol(),
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=str(positionStatus.getCurrentCoinAmount())
    )
    positionStatus.status_activated = True
    positionStatus.long_status = False

    print("coin sorted")
    #   sell all coins at maret price
    # OCO POZİSYONU KOYAR BUY coin SORT KAPATMA
    # #otomatik olarak aslında pozisyon kapatma emri verir
    print(str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 90 / 100)))
    print(str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 101 / 100)))
    print(str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 102 / 100)))
    order = client.create_margin_oco_order(
        symbol=positionStatus.getSymbol(),
        isIsolated="True",
        side="BUY",
        sideEffectType="AUTO_REPAY",
        quantity=positionStatus.get_total_coin_dept(),
        price=str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 90 / 100)),
        stopPrice=str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 101 / 100)),
        stopLimitPrice=str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 102 / 100)),
        stopLimitTimeInForce='FOK')

    positionStatus.long_status = False
    print(order)
    exit()


def longCoin():
    barrowMaxBUSD()
    order = client.create_margin_order(
        isIsolated='TRUE',
        symbol=positionStatus.getSymbol(),
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=str(positionStatus.getBuyableCoinAmout())
    )
    positionStatus.status_activated = True
    positionStatus.long_status = True
    print("coin longed")

    print(str(positionStatus.getFormatedUSDAmount((positionStatus.start_index * 110 / 100))))
    print(str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 99 / 100)))
    print(str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 98 / 100)))
    # buy all coins at market price
    order = client.create_margin_oco_order(
        symbol=positionStatus.getSymbol(),
        isIsolated="True",
        side="SELL",
        sideEffectType="AUTO_REPAY",
        quantity=positionStatus.getCurrentCoinAmount(),
        price=str(positionStatus.getFormatedUSDAmount((positionStatus.start_index * 110 / 100))),
        stopPrice=str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 99 / 100)),
        stopLimitPrice=str(positionStatus.getFormatedUSDAmount(positionStatus.start_index * 98 / 100)),
        stopLimitTimeInForce='FOK')
    print(order)
    exit()


def barrowMaxCoin():
    #   Coin  boçlanır
    transaction = client.create_margin_loan(asset=positionStatus.base_asset, isIsolated='TRUE',
                                            symbol=positionStatus.getSymbol(),
                                            amount=positionStatus.getCoinLimitToBarrow())
    print("Coin barrowed")


def repayCoin():
    # Coin borcunu öder
    transaction = client.repay_margin_loan(asset=positionStatus.base_asset, isIsolated='TRUE',
                                           symbol=positionStatus.getSymbol(), amount='1000000000')
    print("coin has been repayed")


def barrowMaxBUSD():
    print("hello form barrrow")
    transaction = client.create_margin_loan(asset=positionStatus.quote_asset, isIsolated='TRUE',
                                            symbol=positionStatus.getSymbol(),
                                            amount=positionStatus.getUsdLimitToBarrow())
    print("usd baroowed")


def repayUSD():
    # Para borcunu öder
    transaction = client.repay_margin_loan(asset=positionStatus.quote_asset, isIsolated='TRUE', symbol="ETHBUSD",
                                           amount='100000000')
    print("usd has been repayed")


def yaci_function(baseAsset, quoteAsset):
    baseAsset = baseAsset.upper()
    quoteAsset = quoteAsset.upper()
    #  Start Assignment
    positionStatus.base_asset = baseAsset
    positionStatus.quote_asset = quoteAsset
    positionStatus.start_index = float(
        client.get_margin_price_index(symbol=baseAsset + quoteAsset, isIsolated='TRUE').get("price"))
    positionStatus.write()

    failCounter = 0

    while True:

        try:

            positionStatus.current_index = float(
                client.get_margin_price_index(symbol=baseAsset + quoteAsset, isIsolated='TRUE').get("price"))
            """
            if positionStatus.status_activated:
                # pozisiyonun hala gecerli olup olmadıgını kontrol et!

                if positionStatus.long_status:
                    if positionStatus.current_index < positionStatus.start_index:  # Current_index < positionStatus.stop_limit:
                        print("#################OUTCAME#################")
                        print("#################LONGED##################")
                        print("Start\t\tIndex\t\t=\t", positionStatus.start_index)
                        print("Entry\t\tPrice\t\t=\t", positionStatus.entry_price)
                        print("Stop\t\tLimit\t\t=\t", positionStatus.stop_limit)
                        print("Current\t\tLimit\t\t=\t", positionStatus.current_index)
                        print("Fibonacci\tLevel\t\t=\t", positionStatus.fib_level)
                        print("#########################################")

                        failCounter = failCounter + 1

                        positionStatus.status_activated = False
                        positionStatus.entry_price = 0
                        positionStatus.stop_limit = 0
                        positionStatus.write()

                else:
                    if positionStatus.current_index > positionStatus.start_index:
                        print("#################OUTCAME#################")
                        print("#################SORTED##################")
                        print("Start\t\tIndex\t\t=\t", positionStatus.start_index)
                        print("Entry\t\tPrice\t\t=\t", positionStatus.entry_price)
                        print("Stop\t\tLimit\t\t=\t", positionStatus.stop_limit)
                        print("Current\t\tLimit\t\t=\t", positionStatus.current_index)
                        print("Fibonacci\tLevel\t\t=\t", positionStatus.fib_level)
                        print("#########################################")

                        failCounter = failCounter + 1

                        positionStatus.status_activated = False
                        positionStatus.entry_price = 0
                        positionStatus.stop_limit = 0
                        positionStatus.write()
            """
            if positionStatus.status_activated == False:
                # Daha önce posisyon açılmadıysa posisyonun açılıp açılmayacagını kontrol et

                if positionStatus.current_index >= ((positionStatus.start_index * 1002) / 1000):
                    # log posizyon gir

                    longCoin()

                    positionStatus.entry_price = positionStatus.current_index
                    positionStatus.status_activated = True
                    positionStatus.long_status = True
                    positionStatus.stop_limit = positionStatus.start_index
                    positionStatus.stop_order_id = 000000000
                    positionStatus.write()

                elif positionStatus.current_index <= ((positionStatus.start_index * 998) / 1000):
                    # sort pozisyon gir

                    sortCoin()

                    positionStatus.entry_price = positionStatus.current_index
                    positionStatus.status_activated = True
                    positionStatus.long_status = False
                    positionStatus.stop_limit = positionStatus.start_index
                    positionStatus.stop_order_id = 000000000
                    positionStatus.write()

            print("Activated\t=\t", positionStatus.status_activated)
            print("FailCounter\t=\t", failCounter)
            if positionStatus.status_activated:
                if positionStatus.long_status:
                    print("Long")
                    print("% olarak degişim:")
                    print(((
                                   positionStatus.current_index - positionStatus.entry_price) / positionStatus.entry_price) * 100)
                else:
                    print("Sort")
                    print("% olarak degişim:")
                    print((((
                                    positionStatus.entry_price - positionStatus.current_index) / positionStatus.entry_price) * 100))


        except Exception as inst:
            print(inst)


#yaci_function("ANY", "BUSD")

order = client.create_margin_oco_order(
        symbol="ANYBUSD",
        isIsolated="True",
        side="BUY",
        sideEffectType="AUTO_REPAY",
        quantity=1.2,
        price="25.11",
        stopPrice="30.11",
        stopLimitPrice="31.11",
        stopLimitTimeInForce='FOK')



id1=-1
id2=-2
print(order)
print(type(order))
print(order["orders"])
print(type(order["orders"]))

id1=order["orders"][0]["orderId"]
id2=order["orders"][1]["orderId"]
print(id1,id2)

currentOrder1 = client.get_margin_order(symbol="ANYBUSD",isIsolated="True",orderId=id1)
print(currentOrder1)
currentOrder2 = client.get_margin_order(symbol="ANYBUSD",isIsolated="True",orderId=id2)
print(currentOrder2)