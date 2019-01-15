from django.urls import path

from . import views

app_name = 'aqueronteApp'

urlpatterns = (
    path('', views.validar_ticket, name='validar_ticket'),
    path('puertas', views.puertas, name='puertas'),
    path('puertas/<str:token>', views.puertas, name='puertas'),
    path('abrir', views.abrir_puerta, name='abrir_puerta'),
    path('refrescar_token', views.refrescar_token, name='refrescar_token'),

)
