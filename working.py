import pyRofex

# Clase donde se almacena el flujo de caja de la operacion
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

    def get_max_quantity_buy(self, price_buy: float):
        return self.available_cash // price_buy
    
    def get_exchange_rate_prom(self, quantity: int, price_buy: float, price_sell: float):
        return (price_buy * quantity + self.ars_spent) / (price_sell * quantity + self.usd_bought)

    # exchange_rate = (price_buy * quantity + self.ars_spent) / (price_sell * quantity + self.usd_bought)
    # para maximizar la cantidad de bonos que se pueden comprar utilizando el tipo de cambio maximo promedio dado
    def get_max_quantity_exchange_rate(self, price_buy: float, price_sell: float, max_exchange_rate: float):
        return (self.ars_spent - max_exchange_rate * self.usd_bought) // (max_exchange_rate * price_sell - price_buy)

    def get_as_dict(self):
        return {
            "total_pesos_gastados": self.ars_spent / 100,
            "total_dolares_generados": self.usd_bought / 100,
            "tipo_cambio_promedio": self.ars_spent / self.usd_bought if self.usd_bought != 0 else None
        }

# Funcion para obtener el saldo de la cuenta disponible para operar
def get_account_available_ARS() :
    acc = pyRofex.get_account_report()
    return acc["accountData"]["detailedAccountReports"]["0"]["availableToOperate"]["cash"]["detailedCash"]["ARS"]

# Funcion para comprar el bono AL30 dados un precio y una cantidad. Utilizamos FillOrKill para que la orden se ejecute en su totalidad o se cancele inmediatamente
def buy_AL30(price: float, quantity: int):
    order = pyRofex.send_order(ticker="MERV - XMEV - AL30 - 48hs",
                        time_in_force=pyRofex.TimeInForce.FillOrKill,
                        side=pyRofex.Side.BUY,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

# Funcion para vender el bono AL30D dados un precio y una cantidad. Utilizamos FillOrKill para que la orden se ejecute en su totalidad o se cancele inmediatamente
def sell_AL30D(price: float, quantity: int):
    order = pyRofex.send_order(ticker="MERV - XMEV - AL30D - 48hs",
                        time_in_force=pyRofex.TimeInForce.FillOrKill,
                        side=pyRofex.Side.SELL,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

# Funcion para obtener los datos de mercado del bono AL30. Podemos opcionalmente ingresar la profundidad.
def get_market_data_AL30(depth=1) :
    offers_AL30 = pyRofex.get_market_data(ticker="MERV - XMEV - AL30 - 48hs", entries=[pyRofex.MarketDataEntry.OFFERS], depth=depth)
    if (offers_AL30["status"] != "OK") :
        raise Exception
    return offers_AL30["marketData"]["OF"]

# Funcion para obtener los datos de mercado del bono AL30D. Podemos opcionalmente ingresar la profundidad.
def get_market_data_AL30D(depth=1) :
    bids_AL30D = pyRofex.get_market_data(ticker="MERV - XMEV - AL30D - 48hs", entries=[pyRofex.MarketDataEntry.BIDS], depth=depth)
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
    # Se obtiene el saldo disponible en la cuenta y se confirma que se puede realizar la operacion con el monto ingresado
    saldo_ARS = get_account_available_ARS()
    if saldo_ARS < monto_pesos:
        raise Exception("El saldo de la cuenta es insuficiente para el monto requerido")
    
    cash_flow = CashFlow(monto_pesos)

    while cash_flow.available_cash > 0:
        try:
            [offers_AL30] = get_market_data_AL30()
            [bids_AL30D] = get_market_data_AL30D()
        except:
            print("Error al obtener datos de mercado - No hay ofertas/bids disponibles para AL30/AL30D")
            break

        buy_price_AL30 = offers_AL30['price']
        sell_price_AL30D = bids_AL30D['price']

        quantity_AL30 = offers_AL30['size']
        quantity_AL30D = bids_AL30D['size']
        quantity_buy = cash_flow.get_max_quantity_buy(buy_price_AL30)   # Cantidad de bonos AL30 que se pueden comprar con el dinero disponible
        quantity = min(quantity_buy, quantity_AL30, quantity_AL30D)

        if cash_flow.get_exchange_rate_prom(quantity, buy_price_AL30, sell_price_AL30D) > tipo_cambio:
            quantity = cash_flow.get_max_quantity_exchange_rate(buy_price_AL30, sell_price_AL30D, tipo_cambio) # Maximizar la cantidad para no superar el maximo promedio de cambio

        # Si no es posible comprar/vender 1 bono AL30/AL30D finalizar la operacion
        if quantity < 1:
            break

        # Compramos AL30 e intentamos venderlo como AL30D de la forma mas atomica posible para reducir las posibilidades de quedarnos con bonos en nuestra posesion
        # Es preferible hacer los checkeos de las ordenes luego.
        order_buy = buy_AL30(buy_price_AL30, quantity)
        order_sell = sell_AL30D(sell_price_AL30D, quantity)

        status_buy = pyRofex.get_order_status(order_buy["order"]["clientId"])   # Estado de la orden de compra
        if status_buy["order"]["status"] == "FILLED":

            status_sell = pyRofex.get_order_status(order_sell["order"]["clientId"])

            # Si la orden de compra se ejecuto pero la de venta no, significa que tenemos bonos en nuestra posesion, por lo tanto intentamos venderlos antes de continuar la operacion
            while (status_sell["order"]["status"] == "CANCELLED"):  
                print("No se logro completar la orden de venta, se intenta nuevamente") # Eliminar
                [bids_AL30D] = get_market_data_AL30D()
                sell_price_AL30D = bids_AL30D['price']

                if cash_flow.get_exchange_rate_prom(quantity, buy_price_AL30, sell_price_AL30D) > tipo_cambio:
                    print("Se supero el exchange rate maximo quedan bonos en posesion") # Aqui se podrian liquidar los bonos en posesion por pesos
                    break

                order_sell = sell_AL30D(sell_price_AL30D, quantity)
                status_sell = pyRofex.get_order_status(order_sell["order"]["clientId"])

            cash_flow.update_spent(quantity * buy_price_AL30)

            if status_sell["order"]["status"] == "FILLED":
                cash_flow.update_usd_bought(quantity * sell_price_AL30D)

    return cash_flow.get_as_dict()

def main() :
    req = pyRofex.initialize(user="lpoma20009154",
                    password="yehdvD7$",
                    account="REM9154",
                    environment=pyRofex.Environment.REMARKET)
    if req != None :
        print ("Error en la inicialización: " + req)
    print ("Inicialización exitosa")
    dict = compraDolares(20000, 27.5)
    print(dict)

if __name__ == "__main__":
    main()