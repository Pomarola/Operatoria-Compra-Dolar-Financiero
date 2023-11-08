import pyRofex

class CashFlow:
    def __init__(self, cash: float):
        self.available_cash = cash * 100 # Se opera multiplicando por 100 para evitar tener que calcular el precio unitario de los bonos
        self.ars_spent = 0
        self.usd_bought = 0

    def update_spent(self, cash: float):
        self.ars_spent += cash
        self.available_cash -= cash

    def update_usd_bought(self, cash: float):
        self.usd_bought += cash
        

def get_account_available_ARS() :
    acc = pyRofex.get_account_report()
    return acc["accountData"]["detailedAccountReports"]["0"]["availableToOperate"]["cash"]["detailedCash"]["ARS"]


def buy_AL30(price: float, quantity: int):
    order = pyRofex.send_order(ticker="MERV - XMEV - AL30 - 48hs",
                        time_in_force=pyRofex.TimeInForce.FillOrKill,
                        side=pyRofex.Side.BUY,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

def sell_AL30D(price: float, quantity: int):
    order = pyRofex.send_order(ticker="MERV - XMEV - AL30D - 48hs",
                        time_in_force=pyRofex.TimeInForce.FillOrKill,
                        side=pyRofex.Side.SELL,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

def get_market_data_AL30(depth=1) :
    offers_AL30 = pyRofex.get_market_data(ticker="MERV - XMEV - AL30 - 48hs", entries=[pyRofex.MarketDataEntry.OFFERS], depth=depth)
    if (offers_AL30["status"] != "OK") :
        raise Exception
    return offers_AL30["marketData"]["OF"]

def get_market_data_AL30D(depth=1) :
    bids_AL30D = pyRofex.get_market_data(ticker="MERV - XMEV - AL30D - 48hs", entries=[pyRofex.MarketDataEntry.BIDS] , depth=depth)
    if (bids_AL30D["status"] != "OK") :
        raise Exception
    return bids_AL30D["marketData"]["BI"]

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
        raise Exception("El saldo de la cuenta es insuficiente para el monto requerido")
    
    cash_flow = CashFlow(monto_pesos)

    while cash_flow.available_cash > 0:
        try:
            [offers_AL30] = get_market_data_AL30()
            [bids_AL30D] = get_market_data_AL30D()
        except:
            print("Error al obtener datos de mercado")
            break

        if cash_flow.available_cash < offers_AL30['price']:
            break

        cantidadAL30D = bids_AL30D['size']
        cantidadAL30 = cash_flow.available_cash // offers_AL30['price']

        if cantidadAL30 > offers_AL30['size']:
            cantidadAL30 = offers_AL30['size']
        
        cantidad = min(cantidadAL30 , cantidadAL30D)

        tentativo_ars = cantidad * offers_AL30['price']
        tentativo_usd = cantidad * bids_AL30D['price']
        prom_cambio = (tentativo_ars + cash_flow.ars_spent) / (tentativo_usd + cash_flow.usd_bought)

        if prom_cambio > tipo_cambio:
            print("Se supero el maximo tipo de cambio deseado, se detuvo la operacion")
            # Maximizar la cantidad para que de el promedio de cambio si ya con 1 bono se supera el tipo de cambio romper
            break

        # Compramos AL30 e intentamos venderlo como AL30D de la forma mas atomica posible para reducir las posibilidades de quedarnos con bonos en nuestra posesion
        order_buy = buy_AL30(offers_AL30['price'] , cantidad)
        order_sell = sell_AL30D(bids_AL30D['price'] , cantidad)

        status_buy = pyRofex.get_order_status(order_buy["order"]["clientId"])
        if status_buy["order"]["status"] == "FILLED":
            cash_flow.update_spent(cantidad * offers_AL30['price'])

            status_sell = pyRofex.get_order_status(order_sell["order"]["clientId"])
            while (status_sell["order"]["status"] == "CANCELLED"):
                print("No se logro completar la orden de venta, se intenta nuevamente")
                [bids_AL30D] = get_market_data_AL30D()
                tentativo_usd = cantidad * bids_AL30D['price']
                prom_cambio = cash_flow.ars_spent / (tentativo_usd + cash_flow.usd_bought)

                if prom_cambio > tipo_cambio:
                    print("Se supero el maximo tipo de cambio deseado, quedan bonos AL30 en la cuenta")
                    # ver de vender por pesos los bonos restantes
                    break

                order_sell = sell_AL30D(bids_AL30D['price'] , cantidad)
                status_sell = pyRofex.get_order_status(order_sell["order"]["clientId"])

            if status_sell["order"]["status"] == "FILLED":
                cash_flow.update_usd_bought(cantidad * bids_AL30D['price'])

    total_pesos = cash_flow.ars_spent / 100
    total_usd = cash_flow.usd_bought / 100

    if total_usd == 0:
        tipo_cambio_promedio = None
    else:
        tipo_cambio_promedio = total_pesos / total_usd

    resultado = {}
    resultado["total_pesos"] = total_pesos
    resultado["total_dolares"] = total_usd
    resultado["tipo_cambio_promedio"] = tipo_cambio_promedio
    return resultado

def main() :
    req = pyRofex.initialize(user="lpoma20009154",
                    password="yehdvD7$",
                    account="REM9154",
                    environment=pyRofex.Environment.REMARKET)
    if req != None :
        print ("Error en la inicialización: " + req)
    print ("Inicialización exitosa")
    dict = compraDolares(30000, 30)
    print(dict)

if __name__ == "__main__":
    main()