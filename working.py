"""
Ejercicio Compra-Dolar Lucas Poma
Pequeña explicacion para dar contexto a la solucion del ejercicio.
En un principio pense el problema como una especie de snapshot del mercado en un momento dado, es decir sin que hubiesen otros agentes externos operando en los bonos que seleccionamos.
Pero mientras estaba haciendo unas pruebas con la API note que el mercado se movia constantemente (no se si es que justo alguien estaria haciendo algo similar),
pero sucedia que algunas ordenes eran rechazadas ya que cambiaba la disponibilidad. Por eso se me ocurrio tener mas en cuenta esto y realizar las operaciones de compra y venta
de una manera mas atomica, por eso utilizo depth=1 para obtener los datos del mercado e intento satisfacer la cantidad minima que satisfaga una orden de compra o venta.
Tambien para reducir las posibilidades de que el mercado cambie mientras realizo operaciones, hago la compra y venta primero, y luego reviso si fueron ejecutadas o no.
Ademas esto reduce el riesgo de quedarnos con bonos en la cuenta, ya que si se ejecuta la compra pero no la venta, no se continua hasta resolver esa situacion.
Si no se ejecuta la compra, no habria problema ya que no seria posible la venta y simplemente se ignora, y se vuelve a iterar en el loop.
El caso problematico es si se ejecuta la compra pero no la venta, en ese caso intento vender los bonos antes de continuar con la operacion.
"""

import pyRofex

BUYING_BOND = "MERV - XMEV - AL30 - 24hs"
SELLING_BOND = "MERV - XMEV - AL30D - 24hs"

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

    # Metodo para obtener la cantidad maxima de bonos que se pueden comprar a un cierto precio de compra con el dinero disponible
    def get_max_quantity_buy(self, price_buy: float):
        return self.available_cash // price_buy
    
    # Metodo para obtener el promedio del tipo de cambio que obtendriamos con la cantidad y los precios de compra y venta
    def get_exchange_rate_prom(self, quantity: int, price_buy: float, price_sell: float):
        return (price_buy * quantity + self.ars_spent) / (price_sell * quantity + self.usd_bought)

    # teniendo la ecuacion exchange_rate = (price_buy * quantity + self.ars_spent) / (price_sell * quantity + self.usd_bought)
    # despejamos quantity y si utilizamos el tipo de cambio maximo promedio como exchange_rate, obtenemos
    # la cantidad de bonos que se pueden comprar sin sobrepasar ese maximo
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

# Funcion para comprar el bono de compra dados un precio y una cantidad. Utilizamos FillOrKill para que la orden se ejecute en su totalidad o se cancele inmediatamente
def buy_buying_bond(price: float, quantity: int):
    order = pyRofex.send_order(ticker=BUYING_BOND,
                        time_in_force=pyRofex.TimeInForce.FillOrKill,
                        side=pyRofex.Side.BUY,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

# Funcion para vender el bono de venta dados un precio y una cantidad. Utilizamos FillOrKill para que la orden se ejecute en su totalidad o se cancele inmediatamente
def sell_selling_bond(price: float, quantity: int):
    order = pyRofex.send_order(ticker=SELLING_BOND,
                        time_in_force=pyRofex.TimeInForce.FillOrKill,
                        side=pyRofex.Side.SELL,
                        size=quantity,
                        price=price,
                        order_type=pyRofex.OrderType.LIMIT)
    return order

# Funcion para obtener los datos de mercado del bono de compra. Podemos opcionalmente ingresar la profundidad. Si falla la llamada se lanza una excepcion
def get_market_data_buying_bond(depth=1) :
    offers_buying_bond = pyRofex.get_market_data(ticker=BUYING_BOND, entries=[pyRofex.MarketDataEntry.OFFERS], depth=depth)
    if (offers_buying_bond["status"] != "OK") :
        raise Exception
    return offers_buying_bond["marketData"]["OF"]

# Funcion para obtener los datos de mercado del bono de venta. Podemos opcionalmente ingresar la profundidad. Si falla la llamada se lanza una excepcion
def get_market_data_selling_bond(depth=1) :
    bids_selling_bond = pyRofex.get_market_data(ticker=SELLING_BOND, entries=[pyRofex.MarketDataEntry.BIDS], depth=depth)
    if (bids_selling_bond["status"] != "OK") :
        raise Exception
    return bids_selling_bond["marketData"]["BI"]

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
            [offers_buying_bond] = get_market_data_buying_bond()
            [bids_selling_bond] = get_market_data_selling_bond()
        except:
            print("No hay ofertas/bids disponibles para el bono de compra/venta, se finaliza la operacion")
            break

        buy_price_buying_bond = offers_buying_bond['price']
        sell_price_selling_bond = bids_selling_bond['price']

        quantity_buying_bond = offers_buying_bond['size']
        quantity_selling_bond = bids_selling_bond['size']
        quantity_buy = cash_flow.get_max_quantity_buy(buy_price_buying_bond)   # Cantidad de bonos de compra que se pueden comprar con el dinero disponible
        quantity = min(quantity_buy, quantity_buying_bond, quantity_selling_bond)

        # Si no es posible comprar/vender 1 bono de compra/venta finalizar la operacion
        if quantity < 1:
            break

        if cash_flow.get_exchange_rate_prom(quantity, buy_price_buying_bond, sell_price_selling_bond) > tipo_cambio:
            quantity = cash_flow.get_max_quantity_exchange_rate(buy_price_buying_bond, sell_price_selling_bond, tipo_cambio) # Maximizar la cantidad para no superar el maximo promedio de cambio
            if quantity < 1:
                break

        # Compramos el bono de compra e intentamos venderlo al bono de venta de la forma mas atomica posible para reducir las posibilidades de quedarnos con bonos en nuestra posesion.
        # Hacemos los checkeos de las ordenes luego.
        order_buy = buy_buying_bond(buy_price_buying_bond, quantity)
        order_sell = sell_selling_bond(sell_price_selling_bond, quantity)

        status_buy = pyRofex.get_order_status(order_buy["order"]["clientId"])   # Estado de la orden de compra
        if status_buy["order"]["status"] == "FILLED":

            status_sell = pyRofex.get_order_status(order_sell["order"]["clientId"])

            # Si la orden de compra se ejecuto pero la de venta no, significa que tenemos bonos en nuestra posesion, por lo tanto intentamos venderlos antes de continuar la operacion
            while (status_sell["order"]["status"] == "CANCELLED"):  
                [bids_selling_bond] = get_market_data_selling_bond()
                sell_price_selling_bond = bids_selling_bond['price']

                if cash_flow.get_exchange_rate_prom(quantity, buy_price_buying_bond, sell_price_selling_bond) > tipo_cambio:
                    print("Se supero el tipo de cambio maximo quedan bonos en posesion") # Aqui se podrian liquidar los bonos en posesion por pesos automaticamente
                    break

                order_sell = sell_selling_bond(sell_price_selling_bond, quantity)
                status_sell = pyRofex.get_order_status(order_sell["order"]["clientId"])

            cash_flow.update_spent(quantity * buy_price_buying_bond)

            if status_sell["order"]["status"] == "FILLED":
                cash_flow.update_usd_bought(quantity * sell_price_selling_bond)

    return cash_flow.get_as_dict()

def main() :
    req = pyRofex.initialize(user="lpoma20009154",
                    password="yehdvD7$",
                    account="REM9154",
                    environment=pyRofex.Environment.REMARKET)
    if req != None :
        print ("Error en la inicialización: " + req)
    print ("Inicialización exitosa")
    dict = compraDolares(250000, 29)
    print(dict)

if __name__ == "__main__":
    main()