from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse # Importante para el modal
from django.contrib.auth.decorators import login_required
from .models import SolicitudIdentidad

def solicitar_asistencia(request):
    if request.method == 'POST':
        # Capturamos los datos (asegúrate que los 'name' en el HTML coincidan)
        tipo = request.POST.get('tipo') 
        dni = request.POST.get('dni')
        email = request.POST.get('email')
        nombre = request.POST.get('nombre')

        if dni and email and nombre:
            SolicitudIdentidad.objects.create(
                tipo=tipo,
                dni=dni,
                email_contacto=email,
                nombre_completo=nombre
            )
            
            # SI LA PETICIÓN ES AJAX (Desde el Modal)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'message': 'Solicitud registrada con éxito.'})
            
            # SI ES PETICIÓN NORMAL
            messages.success(request, "Tu solicitud ha sido recibida. Procesaremos tu caso en breve.")
            return redirect('soporte:solicitud_exitosa')
        
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Faltan campos.'}, status=400)
            messages.error(request, "Por favor, completa todos los campos obligatorios.")

    return render(request, 'soporte/asistencia.html')

@login_required
def lista_solicitudes(request):
    # Esta es la vista para que TÚ gestiones los mensajes recibidos
    solicitudes = SolicitudIdentidad.objects.all().order_by('-fecha_solicitud')
    return render(request, 'soporte/lista_solicitudes.html', {'solicitudes': solicitudes})