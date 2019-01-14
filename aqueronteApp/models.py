from django.db import models


# Create your models here.

# guarda los datos del token activo
class Tokens(models.Model):
    token = models.CharField(max_length=256)
    refresh_token = models.CharField(max_length=256)
    fecha_exp = models.DateTimeField()
    estado = models.BooleanField()
    fecha_c = models.DateTimeField()
    fecha_m = models.DateTimeField(auto_now=True)




# Guarda los datos del usuario
class Usuarios(models.Model):
    pers_id = models.CharField(max_length=60)
    nombres = models.CharField(max_length=60)
    apellidos = models.CharField(max_length=60)
    id_sesion = models.ForeignKey(Tokens, on_delete=models.CASCADE)
    fecha_c = models.DateTimeField()

    class Meta:
        unique_together = ("pers_id", "id_sesion")


# Guarda los datos del usuario asociados a su ticket
class Tickets(models.Model):
    ticket_cas = models.CharField(max_length=256)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    fecha = models.DateTimeField()
