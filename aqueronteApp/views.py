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
    extraccion = requests.get(url=url_cas, params=params, verify=False)
    data = extraccion.json()
    return data


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
            token_actual_bdd = Tokens.objects.filter(token=token_actual, estado=True)
            if token_actual_bdd.exists():
                # Extraer el token actual
                token_actual_bdd = Tokens.objects.get(token=token_actual)
                print(token_actual_bdd)
                token_bdd = token_actual_bdd.token
                r_token_bdd = token_actual_bdd.refresh_token
                if token_bdd == token_actual and r_token_bdd == r_token_actual:
                    # Generar nuevo token y refresh token
                    print(token_actual_bdd)
                    usuario_original = Usuarios.objects.get(id_sesion=token_actual_bdd)
                    old_ticket = Tickets.objects.get(usuario=usuario_original).ticket_cas
                    nuevo_token = hashlib.sha256(
                        (old_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                            'utf-8')).hexdigest()
                    print(nuevo_token)
                    nuevo_refresh_token = hashlib.sha256(
                        (old_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                            'utf-8')).hexdigest()

                    # Deshabilitar el token actual
                    token_actual_bdd.estado = False
                    token_actual_bdd.fecha_m = timezone.now()
                    token_actual_bdd.save()
                    fecha = timezone.now()
                    fecha_exp = (timezone.now() + dt.timedelta(minutes=5))
                    # Crear una nueva fila en la lista de tokens
                    token_actualizado = Tokens(token=nuevo_token, refresh_token=nuevo_refresh_token,
                                               fecha_exp=fecha_exp,
                                               estado=True, fecha_c=fecha, fecha_m=fecha)
                    token_actualizado.save()
                    # Actualizar token asociado al usuario guardandolo en una nueva fila
                    usuario = copy.deepcopy(usuario_original)
                    usuario.id_sesion = token_actualizado
                    usuario.save()

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
        return Response("Esperando", status=200)


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
                fecha_exp = (timezone.now() + dt.timedelta(minutes=5))
                bd_token = Tokens(token=token, refresh_token=refresh_token,
                                  fecha_exp=fecha_exp,
                                  estado=True, fecha_c=fecha, fecha_m=fecha)
                bd_token.save()

                user = Usuarios(pers_id=data["info"]['rut'], nombres=data['info']['nombres'],
                                apellidos=data['info']['apellidos'], id_sesion=bd_token, fecha_c=fecha)
                user.save()
                ticket = Tickets(ticket_cas=data['ticket'], usuario=user, fecha=fecha)
                ticket.save()
                response_data = {
                    "token_data": {"token": token, "refresh_token": refresh_token, "fecha_exp": str(fecha_exp)},
                    "user_data": data}
                return Response(response_data, status=200)

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
                    extraccion = requests.get(url=url_puertas, params=params,
                                              auth=(usuario_servidor, password_servidor),
                                              verify=False)
                    puertas_listado = extraccion.json()
                    return Response(puertas_listado, status=200)
                # Si el ticket es invalido retornar HTTP 403 unauthorized
                else:
                    return Response("Token invalido", status=403)
            else:
                return Response("Token invalido", status=401)
        # Si no llega la data pedida error 400 bad request
        else:
            return Response("Error en la data", status=400)
    else:
        return Response("Esperando", status=200)


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
            if token_bd.exist():
                #extraer el token
                token_bd = Tokens.objects.get(token=token, estado=True)
                if token_bd.fecha_exp > timezone.now():
                    # Solicita al servidor abrir la puerta pedida por la vista
                    id_usuario = Usuarios.objects.get(id_sesion=token_bd).pers_id
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
                    return Response("Token invalido", status=403)
            else:
                return Response("Token invalido", status=401)
        else:
            return Response("Error en la data", status=400)
    else:
        return Response("Esperando", status=200)


@api_view(['GET', 'POST'])
# CERRAR-SESION:
# Inhabilita el token activo del usuario
def cerrar_sesion(request):
    if request.method == 'POST':
        token = request.data.get('token')
        if token is not None:
            bd_token = Tokens.objects.get(token=token)
            bd_token.estado = False
            return Response("Tokens desactivados", status=200)
        else:
            return Response("Data erronea", status=400)
    else:
        return Response("Esperando", status=200)
