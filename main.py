import pyRofex
from script import compraDolares

def main() :
    req = pyRofex.initialize(user="username",
                    password="password",
                    account="account",
                    environment=pyRofex.Environment.REMARKET)
    if req != None :
        print ("Error en la inicialización: " + req)
    print ("Inicialización exitosa")
    dict = compraDolares(10000, 1500)
    print(dict)

if __name__ == "__main__":
    main()