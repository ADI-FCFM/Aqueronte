# CONSULTA_CAS:
# Funcion auxiliar para realizar la validacion del ticket en el CAS, evita la reutilizacion de codigo ya que el
# ticket se revalida constantemente
import requests
from aqueronteApp.configuracion import URL_CAS
from aqueronteApp.models import Tokens


# CONSULTA_CAS::
# Valida el ticket del usuario con CAS y retorna su informacion parseada en un JSON
def consulta_cas(ticket):
    params = {'ticket': ticket}
    extraccion = requests.get(url=URL_CAS, params=params, verify=False)
    data = extraccion.json()
    return data


# Verificar token:
# Funcion auxiliar destinada a evitar codigo repetido en la validacion del token. Lo busca en la base de datos y si
# existe lo extrae
def verificar_token(token):
    token_bdd = Tokens.objects.filter(token=token, estado=True)
    if token_bdd.exists():
        # Extraer el token actual
        token_bdd = Tokens.objects.get(token=token, estado=True)
        return token_bdd
    else:
        return None
