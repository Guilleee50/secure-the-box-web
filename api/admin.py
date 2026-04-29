from django.contrib import admin
from .models import SOCProfile, Maquina
# Register your models here.

# Configuración avanzada para el panel de Máquinas
@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puntos')
    search_fields = ('nombre',)

# Configuración avanzada para el panel de Perfiles SOC
@admin.register(SOCProfile)
class SOCProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'puntos_totales', 'normativa_aceptada', 'api_key')
    search_fields = ('user__username', 'api_key')
    list_filter = ('normativa_aceptada',)
