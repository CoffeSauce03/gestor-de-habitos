from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    username = models.CharField(max_length=150, unique=True, verbose_name="Nome de Usuário")
    password = models.CharField(max_length=128, verbose_name="Senha")

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

class Habito(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name="Usuário")
    nome = models.CharField(max_length=200)

    def __str__(self): 
        return self.nome

class Registro(models.Model):
    habito = models.ForeignKey(Habito, on_delete=models.CASCADE)
    data_registro = models.DateField(default=timezone.now)

    def __str__(self): 
        return f"{self.habito.nome} - {self.data_registro}"