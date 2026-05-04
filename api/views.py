from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import PerfilForm
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.response import Response
from rest_framework import status
from api.models import SOCProfile, Maquina

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Loguea al usuario automáticamente tras registrarse
            return redirect('home')
    else:
        form = UserCreationForm()
    
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