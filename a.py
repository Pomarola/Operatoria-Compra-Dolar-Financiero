import pyRofex
def get_account_available_ARS() :
    acc = pyRofex.get_account_report()
    return acc["accountData"]["detailedAccountReports"]["0"]["availableToOperate"]["cash"]["detailedCash"]["ARS"]


def buy_AL30(price: float, quantity: int):
    order = pyRofex.send_order(ticker="MERV - XMEV - AL30 - 48hs",
                        side=pyRofex.Side.BUY,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

def sell_AL30D(price: float, quantity: int):
    order = pyRofex.send_order(ticker="MERV - XMEV - AL30D - 48hs",
                        side=pyRofex.Side.SELL,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

def main() :
    req = pyRofex.initialize(user="lpoma20009154",
                    password="yehdvD7$",
                    account="REM9154",
                    environment=pyRofex.Environment.REMARKET)
    if req != None :
        print ("Error en la inicialización: " + req)
    print ("Inicialización exitosa")
    return compraDolares(1000, 5)

def get_market_data() :
    offers_AL30 = pyRofex.get_market_data(ticker="MERV - XMEV - AL30 - 48hs", entries=[pyRofex.MarketDataEntry.OFFERS], depth=5)
    bids_AL30D = pyRofex.get_market_data(ticker="MERV - XMEV - AL30D - 48hs", entries=[pyRofex.MarketDataEntry.BIDS] , depth=5)

    return (offers_AL30 , bids_AL30D)

    # for offer in data_AL30D["marketData"]["BI"]:
    #     print(f"Precio unitario : {(offer['price']/100)} - Cantidad {offer['size']}.")


def compraDolares(monto_pesos: float, tipo_cambio: float):
    """
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
    saldo_ARS = get_account_available_ARS()
    if saldo_ARS < monto_pesos:
        print("No hay saldo suficiente para comprar dólares")
        return None
    
    (offers_AL30 , bids_AL30D) = get_market_data()
    print(offers_AL30)
    print(bids_AL30D)



    resultado = {}
    resultado["total_pesos"] = 0
    resultado["total_dolares"] = 0
    resultado["tipo_cambio_promedio"] = 0
    return resultado

if __name__ == "__main__":
    main()