# from django.shortcuts import render
from rest_framework.decorators import api_view
# Create your views here.
from rest_framework.response import Response
import requests
from aqueronteApp.models import Ticket, Usuario
from aqueronteApp.credentials import *


@api_view(['GET', 'POST'])
# VALIDAR_TICKET:
# Recibe el ticket desde la vista por un metodo post.Luego valida dicho ticket accediendo al CAS del cual recibe los
# datos y la validez del ticket mismo. Devuelve dichos datos acompañado de un HTTP 200 si el ticket es valido. Si no lo
# es, devuelve HTTP 401, unauthorized
def validar_ticket(request):
    if request.method == 'POST':
        # Recepcion de informacion
        view_ticket = request.data.get('ticket')

        # Validacion del ticket
        url = 'https://sys21.adi.ing.uchile.cl/~jarriagada/davinci/web/batch/heimdall/check'
        params = {'ticket': view_ticket}
        extraccion = requests.get(url=url, params=params, verify=False)
        data = extraccion.json()

        # Si el ticket es valido lo guarda los datos del usuario en la BDD y retorna los datos junto a un codigo
        # HTTP 200
        if data['valid']:
            user = Usuario(rut=data["info"]['rut'], nombres=data['info']['nombres'],
                           apellidos=data['info']['apellidos'])
            user.save()
            ticket = Ticket(ticket=data['ticket'], valid=data['valid'], usuario=user)
            ticket.save()
            return Response(data, status=200)

        # Si el ticket no es valido retorna HTTP 401 unathorized
        else:
            return Response("Ticket invalido", status=401)
    else:
        return Response("Esperando", status=200)


@api_view(['GET', 'POST'])
# PUERTAS:
# Recibe el ticket desde la vista por un metodo post, lo revalida con el CAS para verificar que sigue activo. Si esta
# activo busca el nombre del usuario y pide al servidor las puertas a las cuales tiene acceso retornandolas a la vista
# con un codigo http 200
def puertas(request):
    if request.method == 'POST':
        # Recibir el ticket desde la vista
        ticket = request.data.get('ticket')
        # Revalidar el ticket con el CAS
        url_t = 'https://sys21.adi.ing.uchile.cl/~jarriagada/davinci/web/batch/heimdall/check'
        params_t = {'ticket': ticket}
        extraccion_t = requests.get(url=url_t, params=params_t, verify=False)
        data = extraccion_t.json()
        # Verificar que el ticket este valido
        if data['valid']:
            # Solicitar al servidor las puertas del usuario y retornarlas junto a un codigo HTTP 200
            url = 'https://adi2.ing.uchile.cl/~jarriagada/ucampus/web/api/0/fcfm_mantenedor_pi/puertas'
            params = {"pers_id": data['info']['rut']}
            extraccion = requests.get(url=url, params=params,
                                      auth=(usuario_servidor, password_servidor),
                                      verify=False)
            puertas_listado = extraccion.json()
            return Response(puertas_listado, status=200)
        # Si el ticket es invalido retornar HTTP 401 unauthorized
        else:
            return Response("Ticket invalido", status=401)
    else:
        return Response("Esperando", status=200)


@api_view(['GET', 'POST'])
# ABRIR_PUERTA::
# Recibe desde la vista la id de una puerta y el ticket del usuario, lo revalida con el CAS para verificar que siga
# activo y en caso de ser asi, pide al servidor abrir la puerta. Si lo logra, retorna codigo HTTP 200, sino 401
def abrir_puerta(request):
    if request.method == 'POST':
        # Recibir informacion
        id_puerta = request.data.get('id')
        ticket = request.data.get('ticket')

        # Revalidar el ticket con el CAS
        url_t = 'https://sys21.adi.ing.uchile.cl/~jarriagada/davinci/web/batch/heimdall/check'
        params_t = {'ticket': ticket}
        extraccion_t = requests.get(url=url_t, params=params_t, verify=False)
        data = extraccion_t.json()

        # Verificar que el ticket este valido
        if data['valid']:
            # Solicita al servidor abrir la puerta pedida por la vista
            id_usuario = data['info']['rut']
            url = 'https://adi2.ing.uchile.cl/~jarriagada/ucampus/web/api/0/fcfm_mantenedor_pi/abrir'
            params = {'id': id_puerta, 'pers_id': id_usuario}
            peticion_apertura = requests.get(url=url, params=params,
                                             auth=(usuario_servidor, password_servidor),
                                             verify=False)
            respuesta_servidor = peticion_apertura.json()

            # Si la puerta se abrio retorna HTTP 200
            if respuesta_servidor['estado']:
                return Response("Acceso concedido", status=200)

            # Si la puerta no se abrio, HTTP 401 unauthorized
            else:
                return Response("Acceso denegado", status=401)
        # Si el ticket no es valido HTTP 401 unauthorized
        else:
            return Response("Ticket invalido", status=401)
    else:
        return Response("Esperando", status=200)
