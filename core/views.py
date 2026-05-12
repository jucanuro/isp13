from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import requests
from sickle import Sickle
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import etree
import urllib3
import io
from investigacion.models import Tesis 
from django.contrib.auth.decorators import login_required

def home(request):
    tesis_locales = Tesis.objects.filter(estado='publicado').prefetch_related('autores').order_by('-fecha_registro')[:6]
    
    return render(request, 'index.html', {
        'tesis_locales': tesis_locales, 
        'mostrar_boton_ver_mas': True,
        'template_padre': 'investigacion/vacio.html'
    })

@login_required
def dashboard_view(request):
    total_tesis = Tesis.objects.count()
    tesis_pendientes = Tesis.objects.filter(estado='pendiente').count() 
    
    context = {
        'total_tesis': total_tesis,
        'tesis_pendientes': tesis_pendientes,
        'template_padre': 'investigacion/vacio.html' 
    }
    return render(request, 'dashboard.html', context)


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenido de nuevo, {u}")
            return redirect('dashboard')
        else:
            messages.error(request, "Credenciales incorrectas. Inténtalo de nuevo.")
            
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')

def modal_content(request, modal_id):
    """
    Carga dinámicamente archivos HTML desde la carpeta templates/modals/
    """
    template_name = f'modals/{modal_id}.html'
    return render(request, template_name)

def portal_transparencia(request):
    return render(request, 'portal.html')