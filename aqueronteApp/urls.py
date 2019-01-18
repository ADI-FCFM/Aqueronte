from django.urls import path

from . import views

app_name = 'aqueronteApp'

urlpatterns = (
    path('', views.validar_ticket, name='validar_ticket'),
    path('puertas', views.Puertas.as_view(), name='puertas'),
    path('puertas/<str:token>', views.Puertas.as_view(), name='puertas'),
    path('refrescar_token', views.refrescar_token, name='refrescar_token'),
    path('salir', views.cerrar_sesion, name='cerrar_sesion'),

)
