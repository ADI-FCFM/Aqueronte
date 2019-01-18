# from django.shortcuts import render
import copy
import datetime as dt
from datetime import *
from random import randint
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import hashlib
from aqueronteApp.configuracion import *
from aqueronteApp.models import Tickets, Usuarios, Tokens
from aqueronteApp.credentials import *


# Create your views here.

# CONSULTA_CAS:
# Funcion auxiliar para realizar la validacion del ticket en el CAS, evita la reutilizacion de codigo ya que el
# ticket se revalida constantemente
def consulta_cas(ticket):
    # Validacion del ticket
    params = {'ticket': ticket}
    extraccion = requests.get(url=URL_CAS, params=params, verify=False)
    data = extraccion.json()
    return data


# Verificar token:
# Funcion auxiliar destinada a evistar codigo repetido en la validacion del token
def verificar_token(token):
    token_bdd = Tokens.objects.filter(token=token, estado=True)
    if token_bdd.exists():
        # Extraer el token actual
        token_bdd = Tokens.objects.get(token=token, estado= True)
        return token_bdd
    else:
        return None


# Refrescar_token:
# Busca un token expirado en la base de datos y si esta expirado lo cambia por un token nuevo y lo retorna
@api_view(['GET', 'POST'])
def refrescar_token(request):
    if request.method == 'POST':
        # Recibir informacion
        token_actual = request.data.get('token')
        r_token_actual = request.data.get('refresh_token')
        # Si la informacion existe
        if token_actual is not None and r_token_actual is not None:
            # Buscar el Token actual
            token_actual_bdd = verificar_token(token_actual)
            if token_actual_bdd is not None:
                # Extraer el token actual
                token_bdd = token_actual_bdd.token
                r_token_bdd = token_actual_bdd.refresh_token
                if token_bdd == token_actual and r_token_bdd == r_token_actual:
                    # Generar nuevo token y refresh token
                    # obtener al usuario
                    usuario = token_actual_bdd.usuario
                    old_ticket = Tickets.objects.filter(usuario=usuario)[0].ticket_cas
                    nuevo_token = hashlib.sha256(
                        (old_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                            'utf-8')).hexdigest()
                    nuevo_refresh_token = hashlib.sha256(
                        (old_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                            'utf-8')).hexdigest()

                    # Deshabilitar el token actual
                    token_actual_bdd.estado = False
                    token_actual_bdd.fecha_m = timezone.now()
                    token_actual_bdd.save()
                    #Crear un nuevo token
                    fecha = timezone.now()
                    fecha_exp = (timezone.now() + dt.timedelta(minutes=DURACION_TOKEN))
                    token_actualizado = Tokens(token=nuevo_token, refresh_token=nuevo_refresh_token,
                                               fecha_exp=fecha_exp,
                                               estado=True, fecha_c=fecha, fecha_m=fecha, usuario=usuario)
                    token_actualizado.save()

                    # Responder con la informacion actualizada
                    data = {"token": nuevo_token, "refresh_token": nuevo_refresh_token, "fecha_exp": fecha_exp}
                    return Response(data, status=200)
                else:
                    return Response('Credenciales incorrectas', status=401)
            else:
                return Response("Token inválido", status=401)
        else:
            return Response('Data erronea', status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)


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
            # Si el ticket es valido actualiza la base de datos con la información recibida y retorna los datos junto a
            # un codigo HTTP 200
            if data['valid']:
                # Genera el token y refresh token con hash256
                token_hash = hashlib.sha256(
                    (view_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                        'utf-8'))
                token = token_hash.hexdigest()
                print("El token generado es", token)
                refresh_token_hash = hashlib.sha256(
                    (view_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                        'utf-8'))
                refresh_token = refresh_token_hash.hexdigest()
                fecha = timezone.now()
                fecha_exp = (timezone.now() + dt.timedelta(minutes=DURACION_TOKEN))
                usuario, created = Usuarios.objects.get_or_create(pers_id=data["info"]['rut'],
                                                                  defaults={"nombres": data['info']['nombres'],
                                                                            "apellidos": data['info']['apellidos'],
                                                                            "fecha_c": fecha})
                usuario.save()
                bd_token = Tokens(token=token, refresh_token=refresh_token,
                                  fecha_exp=fecha_exp,
                                  estado=True, fecha_c=fecha, fecha_m=fecha, usuario=usuario)
                bd_token.save()

                ticket = Tickets(ticket_cas=data['ticket'], usuario=usuario, fecha=fecha)
                ticket.save()
                response_data = {
                    "token_data": {"token": token, "refresh_token": refresh_token, "fecha_exp": str(fecha_exp)},
                    "user_data": {"nombres": data['info']['nombres'], "apellidos": data['info']['apellidos']}}
                return Response(response_data, status=200)

            # Si el ticket no es valido retorna HTTP 401 unathorized
            else:
                return Response("Ticket invalido", status=401)
        # Si no llega la data pedida error 400 bad request
        else:
            return Response("Error en la data", status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)


@api_view(['GET', 'POST'])
# PUERTAS:
# Recibe el token desde de la vista por un metodo post, Verifica que este activo en la base de datos. Si esta
# activo busca el nombre del usuario y pide al servidor las puertas a las cuales tiene acceso retornandolas a la vista
# con un codigo http 200
def puertas(request):
    if request.method == 'GET':
        # Recibir el ticket desde la vista
        token = request.query_params.get('token')
        if token is not None:
            token_bd = Tokens.objects.filter(token=token, estado=True)
            if token_bd.exists():
                token_bd = Tokens.objects.get(token=token, estado=True)
                if token_bd.fecha_exp > timezone.now():
                    # Solicitar al servidor las puertas del usuario y retornarlas junto a un codigo HTTP 200
                    pers_id = Usuarios.objects.get(id_sesion=token_bd).pers_id
                    params = {"pers_id": pers_id}
                    extraccion = requests.get(url=URL_PUERTAS, params=params,
                                              auth=(USUARIO_SERVICIOS, CLAVE_SERVICIOS),
                                              verify=False)
                    puertas_json = extraccion.json()
                    puertas_lista = []
                    for key, value in puertas_json.items():
                        puertas_lista.append(value)

                    return Response(puertas_lista, status=200)
                # Si el ticket esta expirado retornar HTTP 403 unauthorized
                else:
                    return Response("Token expirado", status=403)
            else:
                return Response("Token invalido", status=401)
        # Si no llega la data pedida error 400 bad request
        else:
            return Response("Error en la data", status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)


@api_view(['GET', 'POST'])
# ABRIR_PUERTA:
# Recibe desde la vista la id de una puerta y el token del usuario, verifica que este activo en la base de datos
#  y en caso de ser asi, pide al servidor abrir la puerta. Si lo logra, retorna codigo HTTP 200, sino 401
def abrir_puerta(request):
    if request.method == 'POST':
        # Recibir informacion
        id_puerta = request.data.get('id')
        token = request.data.get('token')
        if token is not None and id_puerta is not None:
            # Verificar que el token este activo
            token_bd = Tokens.objects.filter(token=token, estado=True)
            if token_bd.exists():
                # extraer el token
                token_bd = Tokens.objects.get(token=token, estado=True)
                if token_bd.fecha_exp > timezone.now():
                    # Solicita al servidor abrir la puerta pedida por la vista
                    id_usuario = Usuarios.objects.get(id_sesion=token_bd).pers_id
                    params = {'id': id_puerta, 'pers_id': id_usuario}
                    peticion_apertura = requests.get(url=URL_ABRIR, params=params,
                                                     auth=(USUARIO_SERVICIOS, CLAVE_SERVICIOS),
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
                    return Response("Token expirado", status=403)
            else:
                return Response("Token invalido", status=401)
        else:
            return Response("Error en la data", status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)


@api_view(['GET', 'POST'])
# CERRAR-SESION:
# Inhabilita el token activo del usuario
def cerrar_sesion(request):
    if request.method == 'POST':
        token = request.data.get('token')
        if token is not None:
            bd_token = Tokens.objects.filter(token=token, estado=True)
            if bd_token.exists():
                bd_token = Tokens.objects.get(token=token)
                bd_token.estado = False
                bd_token.fecha_m = timezone.now()
                bd_token.save()
                return Response("Tokens desactivados", status=200)
            else:
                return Response("Token inválido", status=401)
        else:
            return Response("Data erronea", status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)
