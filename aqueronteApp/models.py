from django.utils import timezone

from django.db import models


# Create your models here.

# Guarda los datos del usuario
class Usuarios(models.Model):
    pers_id = models.CharField(max_length=60, primary_key=True)
    nombres = models.CharField(max_length=60)
    apellidos = models.CharField(max_length=60)
    fecha_c = models.DateTimeField(auto_now_add=True)

# guarda los datos del token activo
class Tokens(models.Model):
    token = models.CharField(max_length=256)
    refresh_token = models.CharField(max_length=256)
    fecha_exp = models.DateTimeField()
    estado = models.BooleanField()
    fecha_c = models.DateTimeField(auto_now_add=True)
    fecha_m = models.DateTimeField(auto_now=True)
    usuario= models.ForeignKey(Usuarios, on_delete=models.CASCADE)

    def is_valido(self):
        if self.fecha_exp > timezone.now():
            return True
        else:
            return False

# Guarda los datos del usuario asociados a su ticket
class Tickets(models.Model):
    ticket_cas = models.CharField(max_length=256)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
