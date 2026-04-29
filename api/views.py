from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import PerfilForm
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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

@api_view(['POST'])
def validar_maquina_api(request):
    api_key = request.data.get('api_key')
    nombre_maquina = request.data.get('maquina')

    try:
        # 1. Buscar al usuario por su API Key
        perfil = SOCProfile.objects.get(api_key=api_key)
        
        # 2. Buscar la máquina en la base de datos
        maquina = Maquina.objects.get(nombre=nombre_maquina)

        # 3. Evitar que sume puntos dos veces por la misma máquina
        if maquina in perfil.maquinas_completadas.all():
            return Response({"error": "Máquina ya completada anteriormente"}, status=400)

        # 4. Sumar puntos y registrar
        perfil.maquinas_completadas.add(maquina)
        perfil.puntos_totales += maquina.puntos
        perfil.save()

        return Response({"status": "Puntos sumados", "total": perfil.puntos_totales})

    except SOCProfile.DoesNotExist:
        return Response({"error": "API Key inválida"}, status=403)
    except Maquina.DoesNotExist:
        return Response({"error": "Máquina no encontrada"}, status=404)