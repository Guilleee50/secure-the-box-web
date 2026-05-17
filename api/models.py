import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.models import Sum

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


class Flag(models.Model):
    """
    FLAG de un solo uso generada por el script de validación.
    Vincula una máquina concreta a un token HMAC firmado con caducidad.
    """
    token     = models.CharField(max_length=200, unique=True)  # STB-<maquina>-<ts>-<hmac>
    maquina   = models.ForeignKey(Maquina, on_delete=models.CASCADE)
    creada_en = models.DateTimeField()                         # Timestamp extraído del propio token
    usada     = models.BooleanField(default=False)
    usada_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    usada_en  = models.DateTimeField(null=True, blank=True)

    FLAG_TTL_MINUTOS = 30  # La FLAG caduca a los 30 minutos

    def __str__(self):
        estado = "usada" if self.usada else "disponible"
        return f"FLAG {self.maquina.nombre} [{estado}]"

    class Meta:
        verbose_name = "Flag"
        verbose_name_plural = "Flags"


class SOCProfile(models.Model):
    # Relación uno a uno con el usuario de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # API Key única generada automáticamente
    api_key = models.CharField(max_length=100, unique=True, blank=True)
    
    # Puntuación acumulada
    puntos_totales = models.IntegerField(default=0)
    
    # Relación para saber qué máquinas ha hecho
    maquinas_completadas = models.ManyToManyField(Maquina, blank=True)

    # Normativa
    normativa_aceptada = models.BooleanField(default=False)

    def __str__(self):
        return f"Perfil de {self.user.username}"


# =========================================================
# --- SECCIÓN DE SEÑALES (Mágico) ---
# ¡Las señales van SIEMPRE fuera de las clases!
# =========================================================

# 1. Crea el perfil y la API Key cuando se registra un usuario nuevo
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        nueva_key = uuid.uuid4().hex
        SOCProfile.objects.create(user=instance, api_key=nueva_key)

# 2. Guarda el perfil si el usuario se actualiza
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# 3. Recalcula los puntos automáticamente si se añaden/quitan máquinas
@receiver(m2m_changed, sender=SOCProfile.maquinas_completadas.through)
def actualizar_puntos_automaticamente(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Sumamos los puntos de todas las máquinas vinculadas actualmente
        resultado = instance.maquinas_completadas.aggregate(total=Sum('puntos'))
        
        # Actualizamos el campo de puntos (si es None porque no hay máquinas, ponemos 0)
        instance.puntos_totales = resultado['total'] or 0
        instance.save()