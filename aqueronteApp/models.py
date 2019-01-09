from django.db import models


# Create your models here.
# Guarda los datos del usuario
class Usuario(models.Model):
    rut = models.IntegerField()
    nombres = models.CharField(max_length=60)
    apellidos = models.CharField(max_length=60)


# Guarda los datos del usuario asociados a su ticket
class Ticket(models.Model):
    ticket = models.CharField(max_length=256)
    valid = models.BooleanField()
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
