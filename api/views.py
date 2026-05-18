from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
import json
import hmac
import hashlib
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import PerfilForm, RegistroConCaptchaForm
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.response import Response
from rest_framework import status
from api.models import SOCProfile, Maquina, Flag

def register_view(request):
    if request.method == 'POST':
        # 1. Usamos el formulario que incluye el campo CAPTCHA
        form = RegistroConCaptchaForm(request.POST) 
        
        # 2. Django comprueba automáticamente el CAPTCHA aquí
        if form.is_valid():
            user = form.save()
            
            # 3. Solución al conflicto con Axes: especificamos el backend de autenticación
            login(request, user, backend='django.contrib.auth.backends.ModelBackend') 
            
            return redirect('home')
    else:
        # Formulario vacío para peticiones GET
        form = RegistroConCaptchaForm()
    
    return render(request, 'register.html', {'form': form})

def home_view(request):
    # Obtenemos los 5 perfiles con más puntos (orden descendente: -puntos_totales)
    # select_related('user') es un truco de optimización para que la DB vaya más rápido
    top_hackers = SOCProfile.objects.select_related('user').order_by('-puntos_totales')[:5]
    
    context = {
        'top_hackers': top_hackers
    }
    return render(request, 'index.html', context) 

def docs_view(request):
    return render(request, 'docs.html')

# Vista de solo lectura (puede ser pública o privada)
def normativa_view(request):
    return render(request, 'normativa.html')

# Función para guardar la aceptación
@login_required
def aceptar_normativa(request):
    if request.method == 'POST':
        request.user.profile.normativa_aceptada = True
        request.user.profile.save()
        return redirect('panel') # O el nombre que tenga vuestra URL del panel
    return redirect('home')

@login_required # Obliga a estar logueado para ver esta página
def panel_view(request):
    # 1. Gestionar el formulario de cambio de datos
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('panel') # Recarga la página tras guardar
    else:
        # Si acaba de entrar, le mostramos el formulario con sus datos actuales
        form = PerfilForm(instance=request.user)

    # 2. Máquinas hardcodeadas (Datos de prueba)
    maquinas_completadas = [
        {'nombre': 'SQLi Master', 'fecha': '18 Abr 2026', 'dificultad': 'Fácil', 'puntos': 50},
        {'nombre': 'Docker Escape', 'fecha': '19 Abr 2026', 'dificultad': 'Media', 'puntos': 150},
        {'nombre': 'Ransomware Reversing', 'fecha': '20 Abr 2026', 'dificultad': 'Difícil', 'puntos': 300},
    ]

    context = {
        'form': form,
        'maquinas': maquinas_completadas,
        'puntos_totales': sum(m['puntos'] for m in maquinas_completadas) # Suma los puntos automáticamente
    }
    return render(request, 'panel.html', context)

@extend_schema(
    summary="Validar resolución de máquina",
    description="Recibe la API Key del usuario y el nombre de la máquina para sumar puntos.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'api_key': {'type': 'string', 'example': 'tu_api_key_aqui'},
                'maquina': {'type': 'string', 'example': 'Docker_Hardening_01'},
            },
            'required': ['api_key', 'maquina']
        }
    },
    responses={200: dict, 400: dict, 401: dict, 404: dict}
)
@api_view(['POST']) # Sustituye a @csrf_exempt y @require_POST
def validar_maquina(request):
    try:
        # 1. Leer los datos enviados por el script de la máquina usando DRF
        api_key = request.data.get('api_key')
        maquina_nombre = request.data.get('maquina')

        # Validar que nos envían todo lo necesario
        if not api_key or not maquina_nombre:
            return Response({'status': 'error', 'message': 'Faltan parámetros: api_key o maquina'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Buscar al agente por su API Key
        try:
            perfil = SOCProfile.objects.get(api_key=api_key)
        except SOCProfile.DoesNotExist:
            return Response({'status': 'error', 'message': 'API Key inválida o Agente no encontrado'}, status=status.HTTP_401_UNAUTHORIZED)

        # 3. Buscar la máquina en la base de datos
        try:
            maquina = Maquina.objects.get(nombre=maquina_nombre)
        except Maquina.DoesNotExist:
            return Response({'status': 'error', 'message': 'Máquina no reconocida por el sistema'}, status=status.HTTP_404_NOT_FOUND)

        # 4. Comprobar si el usuario ya ha completado esta máquina antes
        if perfil.maquinas_completadas.filter(id=maquina.id).exists():
            return Response({'status': 'error', 'message': 'Máquina ya completada anteriormente'}, status=status.HTTP_400_BAD_REQUEST)

        # 5. ¡Éxito! Añadir la máquina a su lista
        # (La señal en models.py sumará los puntos automáticamente)
        perfil.maquinas_completadas.add(maquina)
        perfil.refresh_from_db() # Refrescamos para obtener el nuevo total de puntos

        # Responder al script de la máquina con éxito
        return Response({
            'status': 'success',
            'message': '¡Reto superado! Puntos añadidos a tu perfil.',
            'puntos_ganados': maquina.puntos,
            'puntos_totales': perfil.puntos_totales
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'status': 'error', 'message': f'Error interno del servidor: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener datos del agente",
    request={'application/json': {'type': 'object', 'properties': {'api_key': {'type': 'string'}}}},
    responses={200: dict}
)
@api_view(['POST'])
def get_user_data(request):
    try:
        # 1. Leer los datos enviados por la app cliente
        api_key = request.data.get('api_key')

        # Validar que nos envían la key
        if not api_key:
            return JsonResponse({'status': 'error', 'message': 'Falta el parámetro: api_key'}, status=400)

        # 2. Buscar al agente por su API Key
        try:
            perfil = SOCProfile.objects.get(api_key=api_key)
        except SOCProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'API Key inválida o Agente no encontrado'}, status=401)

        # 3. Preparar los datos a devolver
        # values_list('nombre', flat=True) saca solo los nombres de las máquinas en una lista limpia
        maquinas_hechas = list(perfil.maquinas_completadas.values_list('nombre', flat=True))

        # 4. Devolver la información estructurada en JSON
        return JsonResponse({
            'status': 'success',
            'data': {
                'username': perfil.user.username,
                'puntos_totales': perfil.puntos_totales,
                'maquinas_completadas': maquinas_hechas,
                # Si tienes el campo de normativa en el modelo, lo puedes pasar también:
                # 'normativa_aceptada': perfil.normativa_aceptada 
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno del servidor: {str(e)}'}, status=500)
    

# ===========================================================
# --- SISTEMA DE FLAGS ---
# ===========================================================

def _verificar_hmac_flag(token: str) -> bool:
    """
    Comprueba que la firma HMAC del token es válida.
    Formato del token: STB-<maquina>-<timestamp_unix>-<hmac_hex>
    """
    try:
        partes = token.split('-', 3)          # máximo 4 partes
        if len(partes) != 4 or partes[0] != 'STB':
            return False
        _, maquina_slug, ts, firma_recibida = partes
        mensaje = f"{maquina_slug}-{ts}".encode()
        firma_esperada = hmac.new(
            settings.FLAG_SECRET.encode(),
            mensaje,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(firma_esperada, firma_recibida)
    except Exception:
        return False


@extend_schema(
    summary="Registrar FLAG generada por el script de validación",
    description=(
        "El script de check llama a este endpoint para depositar una FLAG válida "
        "en la base de datos. No suma puntos: solo guarda la FLAG para que el "
        "usuario la canjee desde la web."
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'flag':    {'type': 'string', 'example': 'STB-ssh_inseguro-1716000000-abcdef...'},
                'maquina': {'type': 'string', 'example': 'ssh_inseguro'},
            },
            'required': ['flag', 'maquina']
        }
    },
    responses={201: dict, 400: dict, 404: dict, 409: dict}
)
@api_view(['POST'])
def registrar_flag(request):
    """
    Llamado por el script de check tras validar la máquina.
    Guarda la FLAG en BD para que el usuario la canjee desde la web.
    No requiere autenticación de usuario (solo HMAC válido).
    """
    token       = request.data.get('flag', '').strip()
    maquina_slug = request.data.get('maquina', '').strip()

    if not token or not maquina_slug:
        return Response(
            {'status': 'error', 'message': 'Faltan parámetros: flag o maquina'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1. Verificar firma HMAC
    if not _verificar_hmac_flag(token):
        return Response(
            {'status': 'error', 'message': 'FLAG inválida: firma incorrecta'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 2. Extraer timestamp del token y calcular caducidad
    try:
        ts_unix = int(token.split('-')[2])
        creada_en = timezone.datetime.fromtimestamp(ts_unix, tz=timezone.utc)
    except (ValueError, IndexError):
        return Response(
            {'status': 'error', 'message': 'FLAG inválida: timestamp malformado'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if (timezone.now() - creada_en).total_seconds() > Flag.FLAG_TTL_MINUTOS * 60:
        return Response(
            {'status': 'error', 'message': 'FLAG caducada'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Buscar la máquina
    try:
        maquina = Maquina.objects.get(nombre=maquina_slug)
    except Maquina.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Máquina no reconocida'},
            status=status.HTTP_404_NOT_FOUND
        )

    # 4. Evitar duplicados
    if Flag.objects.filter(token=token).exists():
        return Response(
            {'status': 'error', 'message': 'FLAG ya registrada'},
            status=status.HTTP_409_CONFLICT
        )

    # 5. Guardar la FLAG
    try:
        Flag.objects.create(token=token, maquina=maquina, creada_en=creada_en)
    except Exception as e:
        return Response(
            {'status': 'error', 'message': f'Error al guardar la FLAG: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {'status': 'success', 'message': 'FLAG registrada. El usuario ya puede canjearla en la web.'},
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="Canjear FLAG por puntos",
    description="El usuario introduce la FLAG en la web. Si es válida, no ha caducado y no ha sido usada, suma los puntos a su perfil.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'flag': {'type': 'string', 'example': 'STB-ssh_inseguro-1716000000-abcdef...'},
            },
            'required': ['flag']
        }
    },
    responses={200: dict, 400: dict, 401: dict}
)
@api_view(['POST'])
def canjear_flag(request):
    """
    Llamado desde el panel web cuando el usuario introduce su FLAG.
    Requiere sesión activa (login_required a nivel de vista).
    """
    if not request.user.is_authenticated:
        return Response(
            {'status': 'error', 'message': 'Debes iniciar sesión para canjear una FLAG'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token = request.data.get('flag', '').strip()
    if not token:
        return Response(
            {'status': 'error', 'message': 'Falta el parámetro: flag'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1. Verificar firma HMAC
    if not _verificar_hmac_flag(token):
        return Response(
            {'status': 'error', 'message': 'FLAG inválida'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 2. Verificar caducidad
    try:
        ts_unix = int(token.split('-')[2])
        creada_en = timezone.datetime.fromtimestamp(ts_unix, tz=timezone.utc)
    except (ValueError, IndexError):
        return Response(
            {'status': 'error', 'message': 'FLAG malformada'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if (timezone.now() - creada_en).total_seconds() > Flag.FLAG_TTL_MINUTOS * 60:
        return Response(
            {'status': 'error', 'message': f'FLAG caducada (límite: {Flag.FLAG_TTL_MINUTOS} min)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Buscar la FLAG en BD
    try:
        flag_obj = Flag.objects.select_related('maquina').get(token=token)
    except Flag.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'FLAG no encontrada. ¿La ha generado el script de validación?'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 4. Comprobar que no ha sido ya usada
    if flag_obj.usada:
        return Response(
            {'status': 'error', 'message': 'Esta FLAG ya ha sido canjeada'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 5. Comprobar que el usuario no ha completado ya esta máquina
    perfil = request.user.profile
    maquina = flag_obj.maquina

    if perfil.maquinas_completadas.filter(id=maquina.id).exists():
        return Response(
            {'status': 'error', 'message': 'Ya tienes esta máquina completada'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 6. ¡Todo OK! Marcar FLAG como usada y sumar puntos
    flag_obj.usada    = True
    flag_obj.usada_por = request.user
    flag_obj.usada_en  = timezone.now()
    flag_obj.save()

    perfil.maquinas_completadas.add(maquina)   # La señal en models.py recalcula puntos
    perfil.refresh_from_db()

    return Response({
        'status':        'success',
        'message':       f'¡FLAG válida! Has completado "{maquina.nombre}".',
        'puntos_ganados': maquina.puntos,
        'puntos_totales': perfil.puntos_totales,
    }, status=status.HTTP_200_OK)

