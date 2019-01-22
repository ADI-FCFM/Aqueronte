# from django.shortcuts import render
import datetime as dt
from datetime import *
from random import randint
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import hashlib

from rest_framework.views import APIView

from aqueronteApp.FuncionesAuxiliares import verificar_token, consulta_cas
from aqueronteApp.configuracion import *
from aqueronteApp.models import Tickets, Usuarios, Tokens
from aqueronteApp.credentials import *


# Create your views here.


# Refrescar_token:
# Busca un token expirado en la base de datos con la funcion auxiliar VERIFICAR_TOKEN,lo cambia por un token nuevo
# y lo retorna
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
                # Verificar que credenciales esten correctas
                if token_bdd == token_actual and r_token_bdd == r_token_actual:
                    # obtener al usuario
                    usuario = token_actual_bdd.usuario
                    # Generar nuevo token y refresh token utilizando funcion de hash
                    old_ticket = Tickets.objects.filter(usuario=usuario)[0].ticket_cas
                    nuevo_token = hashlib.sha256(
                        (old_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                            'utf-8')).hexdigest()
                    nuevo_refresh_token = hashlib.sha256(
                        (old_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                            'utf-8')).hexdigest()

                    # Deshabilitar el token actual
                    token_actual_bdd.estado = False
                    token_actual_bdd.save()
                    # Crear un nuevo token
                    fecha_exp = (timezone.now() + dt.timedelta(minutes=DURACION_TOKEN))
                    token_actualizado = Tokens(token=nuevo_token, refresh_token=nuevo_refresh_token,
                                               fecha_exp=fecha_exp,
                                               estado=True, usuario=usuario)
                    token_actualizado.save()

                    # Responder con la informacion actualizada
                    data = {"token": nuevo_token, "refresh_token": nuevo_refresh_token, "fecha_exp": fecha_exp}
                    return Response(data, status=200)
                # Token o refresh token no coinciden con la base de datos
                else:
                    return Response('Credenciales incorrectas', status=401)
            # Token no existe en la base de datos
            else:
                return Response("Token inválido", status=401)
        # No se envian los datos correctos en el metodo POST
        else:
            return Response('Data erronea', status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)


@api_view(['GET', 'POST'])
# VALIDAR_TICKET:
# Recibe el ticket desde la vista por metodo POST.Luego valida dicho ticket accediendo al CAS con la funcion auxiliar
# CONSULTA_CAS  del cual recibe los datos y la validez del ticket mismo.
# Guarda los datos del ticket y el usuario en la base de datos acompañado de un token y refresh_token creados con
# funciones de hash yen la base de datos y retornar los datos del token y del usuario acompañado de un código
# HTTP 200 si el ticket es valido o distintos errores http dependiendo del motivo de la falla.
def validar_ticket(request):
    if request.method == 'POST':
        # Recepcion de informacion
        view_ticket = request.data.get('ticket')
        # Si llega la informacion
        if view_ticket is not None:
            # Validacion del ticket con CAS
            data = consulta_cas(view_ticket)
            # Verifica que el ticket esté valido
            if data['valid']:
                # Genera el token y refresh token con hash256
                token = hashlib.sha256(
                    (view_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                        'utf-8')).hexdigest()

                refresh_token = hashlib.sha256(
                    (view_ticket + str(datetime.timestamp(timezone.now())) + str(randint(0, 1000000))).encode(
                        'utf-8')).hexdigest()
                # Actualiza la base de datos
                fecha_exp = (timezone.now() + dt.timedelta(minutes=DURACION_TOKEN))
                # Utiliza el metodo get_or_create de forma que si el usuario ya existe no lo intente crear de nuevo.
                usuario, created = Usuarios.objects.get_or_create(pers_id=data["info"]['rut'],
                                                                  defaults={"nombres": data['info']['nombres'],
                                                                            "apellidos": data['info']['apellidos'],
                                                                            })
                usuario.save()
                bd_token = Tokens(token=token, refresh_token=refresh_token,
                                  fecha_exp=fecha_exp,
                                  estado=True, usuario=usuario)
                bd_token.save()

                ticket = Tickets(ticket_cas=data['ticket'], usuario=usuario)
                ticket.save()
                # Devuelve informacion requerida por la vista (token y datos de usuario)
                response_data = {
                    "info_token": {"token": token, "refresh_token": refresh_token, "fecha_exp": str(fecha_exp)},
                    "info_usuario": {"nombres": data['info']['nombres'], "apellidos": data['info']['apellidos']}}
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


# PUERTAS:
# Clase dedicada al manejo de las puertas (obterneras y abrirlas). Conta de dos métodos, GET encargado de obtener el
# listado de puertas al que tiene acceso una persona de acuerdo a su token y POST que se encarga de abrir una
# determinada puerta.
# GET:
# Recibe por metodo GET (en REST framework query_params), si se recibe la data correcta utiliza la funcion auxiliar
# VERIFICAR_TOKEN para buscarlo en la base de datos.Luego verifica si es valido (no esta expirado y su estado es True)
# con una funcion de la clase Tokens. Utiliza el pers_id de usuario asociado al token para pedir a SERVICIOS (utilizando
# la libreria REQUESTS) el listado de puertas asociadas al usuario, lo parsea en una lista de diccionarios y la retorna.
# POST:
# Recibe por metodo POST (en REST Framework data) la id de una puerta y el token del usuario, si se recibe la data
# correcta utiliza la funcion auxiliar VERIFICAR_TOKEN para buscarlo en la base de datos.Luego verifica si es valido
# (no esta expirado y su estado es True) con una funcion de la clase Tokens. Utiliza el pers_id de usuario asociado
# al token junto al id de la puerta para pedir a SERVICIOS (utilizando la libreria REQUESTS) la apertura de dicho acceso
# SERVICIOS responde true si la puerta se abre y FALSE si no y en base a eso se le responde a la vista.

class Puertas(APIView):
    # obtener listado de puertas
    @staticmethod
    def get(request):
        # Recibir el token desde la vista
        token = request.query_params.get('token')
        # Si la informacion es correcta
        if token is not None:
            # Busca el token en la base de datos
            token_bd = verificar_token(token)
            # Si se encuentra
            if token_bd is not None:
                # Si el token no esta expirado
                if token_bd.is_valido():
                    # Solicita a SERVICIOS las puertas del usuario
                    pers_id = Tokens.objects.get(token=token_bd.token).usuario.pers_id
                    params = {"pers_id": pers_id}
                    extraccion = requests.get(url=URL_PUERTAS, params=params,
                                              auth=(USUARIO_SERVICIOS, CLAVE_SERVICIOS),
                                              verify=False)
                    puertas_json = extraccion.json()
                    puertas_lista = []
                    if puertas_json:
                        # Parsea las puertas en una lista
                        for key, value in puertas_json.items():
                            puertas_lista.append(value)

                    return Response(puertas_lista, status=200)
                # Si el ticket esta expirado retornar HTTP 403 unauthorized
                else:
                    return Response("Token expirado", status=403)
            # si el ticket no existe en la base de datos o esta inactivo
            else:
                return Response("Token invalido", status=401)
        # Si no llega la data pedida error 400 bad request
        else:
            return Response("Error en la data", status=400)

    # Abrir una puerta
    @staticmethod
    def post(request):
        # Recibir informacion
        id_puerta = request.data.get('id')
        token = request.data.get('token')
        # Si la informacion es correxta
        if token is not None and id_puerta is not None:
            # Verificar que el token en la base de datos
            token_bd = verificar_token(token)
            # Si esta y es activo
            if token_bd is not None:
                # Verificar que no este expirado
                if token_bd.is_valido():
                    # Solicita al servidor abrir la puerta pedida por la vista
                    pers_id = Tokens.objects.get(token=token_bd.token).usuario.pers_id
                    params = {'id': id_puerta, 'pers_id': pers_id}
                    peticion_apertura = requests.get(url=URL_ABRIR, params=params,
                                                     auth=(USUARIO_SERVICIOS, CLAVE_SERVICIOS),
                                                     verify=False)
                    respuesta_servidor = peticion_apertura.json()
                    if respuesta_servidor:
                        # Si la puerta se abrio retorna HTTP 200
                        if respuesta_servidor['estado']:
                            return Response("Acceso concedido", status=200)

                        # Si la puerta no se abrio, HTTP 401 unauthorized
                        else:
                            return Response("Acceso denegado", status=401)
                    else:
                        return Response("Acceso Denegado", status=401)
                # Si el token esta expirado
                else:
                    return Response("Token expirado", status=403)
            # Si el token no esta valido
            else:
                return Response("Token invalido", status=401)
        # Si la data recibida no es correcta
        else:
            return Response("Error en la data", status=400)


# CERRAR_CESION
# EndPoint diseñado para cuando el usuario sale de la aplicacion, invalida su token actual
@api_view(['GET', 'POST'])
def cerrar_sesion(request):
    # Recibir informacion
    if request.method == 'POST':
        token = request.data.get('token')
        # Si la data es correcta
        if token is not None:
            # Busca el token en la base de datos
            token_bd = verificar_token(token)
            # Si lo encuentra lo desactiva
            if token_bd is not None:
                token_bd.estado = False
                token_bd.save()
                return Response("Tokens desactivados", status=200)
            # si el token esta invalido
            else:
                return Response("Token inválido", status=401)
        # si la data es incorrecta
        else:
            return Response("Data erronea", status=400)
    else:
        # Si la informacion llega por un metodo que no es POST
        return Response("Metodo no permitido", status=405)
