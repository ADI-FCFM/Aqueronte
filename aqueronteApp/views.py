# from django.shortcuts import render
from rest_framework.decorators import api_view
# Create your views here.
from rest_framework.response import Response
import requests

from aqueronteApp.configuracion import *
from aqueronteApp.models import Tickets, Usuarios
from aqueronteApp.credentials import *




# CONSULTA_CAS:
# Funcion auxiliar para realizar la validacion del ticket en el CAS, evita la reutilizacion de codigo ya que el
# ticket se revalida constantemente
def consulta_cas(ticket):
    # Validacion del ticket
    params = {'ticket': ticket}
    extraccion = requests.get(url=url_cas, params=params, verify=False)
    data = extraccion.json()
    return data

# Refrescar_token:
#Busca un token expirado en la base de datos y si esta expirado lo cambia por un token nuevo y lo retorna
@api_view(['GET', 'POST'])
def refrescar_token(request):
    if request.method=='POST':
        token_actual= request.data.get('token')
        r_token_actual= request.data.get('refresh_token')
    return





@api_view(['GET', 'POST'])
# VALIDAR_TICKET:
# Recibe el ticket desde la vista por un metodo post.Luego valida dicho ticket accediendo al CAS del cual recibe los
# datos y la validez del ticket mismo. Devuelve dichos datos acompañado de un HTTP 200 si el ticket es valido. Si no lo
# es, devuelve HTTP 401, unauthorized
def validar_ticket(request):
    if request.method == 'POST':
        # Recepcion de informacion
        view_ticket = request.data.get('ticket')
        if view_ticket is not None:
            # Validacion del ticket
            data = consulta_cas(view_ticket)
            # Si el ticket es valido lo guarda los datos del usuario en la BDD y retorna los datos junto a un codigo
            # HTTP 200
            if data['valid']:
                user = Usuarios(rut=data["info"]['rut'], nombres=data['info']['nombres'],
                                apellidos=data['info']['apellidos'])
                user.save()
                ticket = Tickets(ticket=data['ticket'], valid=data['valid'], usuario=user)
                ticket.save()
                return Response(data, status=200)

            # Si el ticket no es valido retorna HTTP 401 unathorized
            else:
                return Response("Ticket invalido", status=401)
        # Si no llega la data pedida error 400 bad request
        else:
            return Response("Error en la data", status=400)
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
        if ticket is not None:
            # Revalidar el ticket con el CAS
            data = consulta_cas(ticket)
            # Verificar que el ticket este valido
            if data['valid']:
                # Solicitar al servidor las puertas del usuario y retornarlas junto a un codigo HTTP 200
                params = {"pers_id": data['info']['rut']}
                extraccion = requests.get(url=url_puertas, params=params,
                                          auth=(usuario_servidor, password_servidor),
                                          verify=False)
                puertas_listado = extraccion.json()
                return Response(puertas_listado, status=200)
            # Si el ticket es invalido retornar HTTP 401 unauthorized
            else:
                return Response("Ticket invalido", status=401)
        # Si no llega la data pedida error 400 bad request
        else:
            return Response("Error en la data", status=400)
    else:
        return Response("Esperando", status=200)


@api_view(['GET', 'POST'])
# ABRIR_PUERTA:
# Recibe desde la vista la id de una puerta y el ticket del usuario, lo revalida con el CAS para verificar que siga
# activo y en caso de ser asi, pide al servidor abrir la puerta. Si lo logra, retorna codigo HTTP 200, sino 401
def abrir_puerta(request):
    if request.method == 'POST':
        # Recibir informacion
        id_puerta = request.data.get('id')
        ticket = request.data.get('ticket')
        if ticket is not None and id_puerta is not None:
            # Revalidar el ticket con el CAS
            data = consulta_cas(ticket)
            # Verificar que el ticket este valido
            if data['valid']:
                # Solicita al servidor abrir la puerta pedida por la vista
                id_usuario = data['info']['rut']
                params = {'id': id_puerta, 'pers_id': id_usuario}
                peticion_apertura = requests.get(url=url_abrir, params=params,
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
            return Response("Error en la data", status=400)
    else:
        return Response("Esperando", status=200)
