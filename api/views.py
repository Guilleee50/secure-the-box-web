from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import PerfilForm

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