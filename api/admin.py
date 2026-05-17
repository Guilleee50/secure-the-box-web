from django.contrib import admin
from .models import SOCProfile, Maquina, Flag
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
    readonly_fields = ('puntos_totales',)    

# Panel de FLAGS
@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display  = ('token_corto', 'maquina', 'creada_en', 'usada', 'usada_por', 'usada_en')
    list_filter   = ('usada', 'maquina')
    search_fields = ('token', 'usada_por__username')
    readonly_fields = ('token', 'maquina', 'creada_en', 'usada_por', 'usada_en')

    def token_corto(self, obj):
        """Muestra solo los primeros 40 caracteres del token en el listado."""
        return obj.token[:40] + '...'
    token_corto.short_description = 'Token'