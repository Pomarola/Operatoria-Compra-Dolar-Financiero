import pyRofex
def test () :
    # data = pyRofex.get_market_data(ticker="AL30D",
    #                         entries=[pyRofex.MarketDataEntry.LAST])
    # print(data)

    # print("Hola Mundo!")
    data_AL30 = pyRofex.get_market_data(ticker="MERV - XMEV - AL30 - 48hs", entries=[pyRofex.MarketDataEntry.OFFERS], depth=5)
    print(data_AL30)

    data_AL30D = pyRofex.get_market_data(ticker="MERV - XMEV - AL30D - 48hs", entries=[pyRofex.MarketDataEntry.BIDS] , depth=5)
    print(data_AL30D)

    # order = pyRofex.send_order(ticker="MERV - XMEV - AL30 - 48hs",
    #                         side=pyRofex.Side.BUY,
    #                         size=10,
    #                         price=20201,
    #                         order_type=pyRofex.OrderType.LIMIT)
    # print(order)

    # order = pyRofex.send_order(ticker="MERV - XMEV - AL30D - 48hs",
    #                         side=pyRofex.Side.SELL,
    #                         size=2,
    #                         price=20,
    #                         order_type=pyRofex.OrderType.LIMIT)
    # print(order)

    # data = pyRofex.get_all_orders_status()
    # print(data)
    # data = pyRofex.get_segments()
    # data = pyRofex.get_all_instruments()
    # print(data)

def main() :
    req = pyRofex.initialize(user="lpoma20009154",
                    password="yehdvD7$",
                    account="REM9154",
                    environment=pyRofex.Environment.REMARKET)
    if req != None :
        print ("Error en la inicialización: " + req)
    print ("Inicialización exitosa")
    test()

if __name__ == "__main__":
    main()


"""def compraDolares(monto_pesos: float, tipo_cambio: float):
 
 Parameters
 ----------
 monto_pesos: float
 monto en pesos para comprar dólares
 tipo_cambio: float
 tipo de cambio máximo al que se compra dólares
 Returns
 -------
 resultado: dict
 diccionario con la siguiente información:
 total de pesos gastados
 total de dólares generados
 tipo de cambio promedio al que se ejecutó la operación
 """