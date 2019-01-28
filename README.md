__DJANGO__


¿Por qué usarlo?


Es un framework para poder hacer desarrollo web desde una base, sin la necesidad de "reinventar la rueda". Trae todos los esquemas necesarios para poder desarrollar de forma ordenada, rápida y segura. Separa desde el inicio el MVC de forma de "forzar" al desarrollador a regirse por el patrón de diseño, volviendo el código legible y escalable por otra persona.


__DJANGO REST__


Framework especializado de Django para aplicaciones web. Algunas de sus principales ventajas son:
Tiene una app en browser para poder trabajar con el backend aunque no este implementada la vista.
 Es flexible con las views, tiene herramientas poderosas como hacerlas en clases pero no deja de perimitir hacerlas basadas en métodos que es lo que se requiere para este backend.
 
 
__REQUERIMIENTOS__


   Python (2.7, 3.4, 3.5, 3.6, 3.7)
   
   
   Django (1.11, 2.0, 2.1)
   
   

__CONFIGURACION__


Inicializar un proyecto en Django


Para utilizar REST-FRAMEWORK es necesario agregarlo a las INSTALLED APPS en settings.py junto al nombre de la aplicacion que se está creando.



Los models se mantienen como se usan en django



__VISTAS:__


Se pueden hacer de dos formas, como una clase que extiende a APIView, o utilizando el decorator @api_view que permite atrapar algunos errores de parseo.


Los metodos request.POST  y request.DATA  pasan a ser request.data y request .query_params respectivamente los cuales parsean ademas de POST, PUT y PATCH en el primero caso. (Ademas que request.POST ya no funciona). En el caso de GET es solo un nombre más adecuado.



__CONEXIÓN CON LAS VISTA:__


Para conectar con la vista hecha por otra persona, como en flutter por ejemplo, es necesario permitir a la IP que utilizara el backend acceso al mismo, para ello es necesario editar los  ALLOWED HOSTS en settings.py
 



__RECIBIR INFORMACION DE UNA API EXTERNA (cas, servicios, etc)__


Es necesario utilizar la libreria requests, con la cual dandole la url, los parametros y la autenticación (de ser necesaria) extrae la información de la pagina. Los cuales luego se pueden parsear a un JSON
 
 
 __DESCRIPCIÓN DEL PROBLEMA__


Diseñar el implementar un backend para una aplicación movil encargada de manejar las puertas cuyo sistema de acceso son cajasQL con Inferno. Las vistas de dicha aplicación son implementadas en Flutter por otra persona por lo que el backend tiene que ser lo suficientemente abierto para poder ser utilizado por dicha persona (o cualquiera).


El backend tiene que tener la capacidad de validar a un usuario con una api externa (CAS), registrarlo en una base de datos. Al mismo tiempo debe ser capaz de obtener las puertas a las cuales tiene acceso el usuario desde Servicios enviando sus datos y autenticandose en el servidor. Finalmente debe ser capaz de, si la vist se lo pide, abrir una determinada puerta.



__DESCRIPCIÓN DE LA SOLUCIÓN__


__Modelo:__


Para guardar los datos de forma consistente, se especifican 3 modelos de datos


__Usuarios__(pers_id<string>, nombres<string>, apellidos<string>, fecha_c<dateTime>)


-pers_id rut o pasaporte de la persona


-fecha_c fecha de creacion del usuario




__Token__(Token<string> , refresh_token<string>, fecha_exp<dateTime>, estado<Boolean>, fecha_c<dateTime>, fecha_m<dateTime>, usuario<Usuarios>)


-Token y refresh token son las credenciales temporales que tiene el usuario


-fecha exp es cuando vence el token activo


-Estado es el estado en que se encuentra el token


-fecha_c y fecha_m son las fechas de creación y modificación del token


-Usuario es el usuario al cual se encuentra asociado el token




__Tickets__(ticket_cas<string>, usuario<Usuarios>, fecha<dateTime>) 


-Ticket: validación para el CAS


-Usuario : a quien pertenece dicho ticket


-fecha: ultima fecha de acceso



De esta forma se puede mantener un registro del usuario, su acceso y sus tokens.



__ENDPOINTS__


notas:


Activo: Token con estado True


No activo: Token con estado False


Expirado: Token con estado True pero con fecha de expiración anterior a la actual, debe ser actualizado.


Se proponen 4 endpoints con los cuales se comunicara la vista.


__validar_ticket()__


-Recibe por metodo post el ticket del usuario desde la vista, lo valida con el CAS utilizando la libreria requests  (enfrascada en una función auxiliar) y si es un ticket valido genera un token y refresh token con hash256 utilizando la libreria hashlib.  Con los tokens y los datos del usuario, apoyandose en las librerias timezone y datatime para las fechas, provee los datos necesesarios para las tres tablas del modelo.


Devuelve a la vista la información del token y el nombre y apellido del usuario junto a un codigo http 200.


Si el tiket no está disponible en el CAS o está inválido devuelve http 401


Si la data provista por la vista es inválida devuelve http 400

Si la data se envia por un metodo que no es POST http 405

__Puertas()__


-Clase dedicada al manejo de las puertas (obterneras y abrirlas). Conta de dos métodos, GET encargado de obtener el
listado de puertas al que tiene acceso una persona de acuerdo a su token y POST que se encarga de abrir una
determinada puerta.

__GET:__


Recibe por metodo GET(URL) (en REST framework query_params), si se recibe la data correcta utiliza la funcion auxiliar
VERIFICAR_TOKEN para buscarlo en la base de datos.Luego verifica si es valido (no esta expirado y su estado es True)
con una funcion de la clase Tokens. Utiliza el pers_id de usuario asociado al token para pedir a SERVICIOS (utilizando
la libreria REQUESTS) el listado de puertas asociadas al usuario, lo parsea en una lista de diccionarios y la retorna.



__POST:__


Recibe por metodo POST (en REST Framework data) la id de una puerta y el token del usuario, si se recibe la data
correcta utiliza la funcion auxiliar VERIFICAR_TOKEN para buscarlo en la base de datos.Luego verifica si es valido
(no esta expirado y su estado es True) con una funcion de la clase Tokens. Utiliza el pers_id de usuario asociado
al token junto al id de la puerta para pedir a SERVICIOS (utilizando la libreria REQUESTS) la apertura de dicho acceso
SERVICIOS responde true si la puerta se abre y FALSE si no y en base a eso se le responde a la vista. Si la puerta se abre retorna http 200, sino http 401

En ambas clases ocurren las siguientes excepciones

Si el token está expirado,  hhtp 403

Si el token es inválido, hhtp 401

Si la data enviada desde la vista es erronea, http 400



__refrescar_token():__


-Función pensada para ser utilizada por la vista cuando un token esté vencido. Recibe por metodo POST el token y el refresh_token (segunda capa de seguridad), los busca en la base de datos, los desactiva (Cambia su estado a False), crea un nuevo par utiizando la libreria hashlib (sha256)  y los guarda en la base de datos. Actualiza las referencias al usuario y devuelve el nuevo par acompañado de un http 200.


Si el token o el refresh token son incorrectos, http 401


Si el token no es válido, http 401


Si los datos enviados por la vista no son correctos http 400


Si la informacion llega por un metodo que no es POST 405


__cerrar_sesión()__


-Recibe por metodo post el token del usuario y lo invalida en la base de datos (le cambia el estado a False), retorna http 200


Si el token ya estaba inactivo retorna http  401


Si la data enviada por la vista no es correcta http 400


Si la informacion llega por un metodo que no es POST 405


__FUNCIONES AUXILIARES__


__consulta_cas()__


-utiliza la libreria requests para consultar al cas sobre un ticket en particular. Retorna la información parseada a un json.


__verificar_token():__


-Extrae un token de la base de datos y lo retorna. Si no está retorna None


__REFERENCIAS:__
Django REST Framework
https://www.django-rest-framework.org/


Django vs Flask: https://www.excella.com/insights/creating-a-restful-api-django-rest-framework-vs-flask
			https://www.quora.com/Should-I-use-Flask-or-Django-for-Python-backend-which-I-will-expose-as-REST-to-be-consumed-in-Android
			
			
			https://gearheart.io/blog/flask-vs-django-which-is-better-for-your-web-app/
			
			
			https://www.netguru.com/blog/flask-vs-django-comparison-which-python-framework-is-better-for-your-app


get and post in flask: https://scotch.io/bar-talk/processing-incoming-request-data-in-flask	

python vs php: https://hackr.io/blog/python-vs-php-in-2018

best option for web developing: https://www.quora.com/What-is-the-best-option-for-web-development-PHP-Django-Node-js-Java

restful mobile app: https://savvyapps.com/blog/how-to-build-restful-api-mobile-app	

autenticación: https://www.django-rest-framework.org/api-guide/authentication/ ----> TOKEN AUTHENTICATION, REMOTE USER AUTHENTICATION

token based authentication: https://medium.com/quick-code/token-based-authentication-for-django-rest-framework-44586a9a56fb

get/post django + flutter: https://www.techiediaries.com/flutter-http/ 

djangorest for mobile apps: https://www.sitepoint.com/building-simple-rest-api-mobile-applications/	

Serializers: https://www.django-rest-framework.org/api-guide/serializers/

Request and Responses: https://www.django-rest-framework.org/tutorial/2-requests-and-responses/

extraer Json del CAS= https://www.geeksforgeeks.org/get-post-requests-using-python/

Sesión de usuario:
https://stackoverflow.com/questions/51849550/how-to-keep-user-logged-in-django

Remote api conection:
https://ultimatedjango.com/blog/how-to-consume-rest-apis-with-django-python-reques/
