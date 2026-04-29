import uuid
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine_name = models.CharField(max_length=100)
    points = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.machine_name}: {self.points}"

class Maquina(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    puntos = models.IntegerField(default=50)
    dificultad = models.CharField(max_length=20, choices=[
        ('Fácil', 'Fácil'),
        ('Media', 'Media'),
        ('Difícil', 'Difícil')
    ])

    def __str__(self):
        return self.nombre

class SOCProfile(models.Model):
    # Relación uno a uno con el usuario de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # API Key única generada automáticamente
    api_key = models.CharField(max_length=100, unique=True, blank=True)
    
    # Puntuación acumulada
    puntos_totales = models.IntegerField(default=0)
    
    # Relación para saber qué máquinas ha hecho
    maquinas_completadas = models.ManyToManyField(Maquina, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

    # --- SECCIÓN DE SEÑALES (Mágico) ---
    # Esto hace que cada vez que se cree un User, se cree su SOCProfile automáticamente
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            # Generamos una clave única estilo 'uuid'
            nueva_key = uuid.uuid4().hex
            SOCProfile.objects.create(user=instance, api_key=nueva_key)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()