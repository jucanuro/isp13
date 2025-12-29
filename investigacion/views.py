from django.shortcuts import render, redirect, get_object_or_404
from .models import Tesis
from django.contrib import messages

def registrar_tesis(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor = request.POST.get('autor')
        asesor = request.POST.get('asesor')
        resumen = request.POST.get('resumen')
        archivo = request.FILES.get('archivo_pdf') 
        if titulo and autor and archivo:
            nueva_tesis = Tesis(
                titulo=titulo,
                autor=autor,
                asesor=asesor,
                resumen=resumen,
                archivo_pdf=archivo
            )
            nueva_tesis.save()
            messages.success(request, "¡Tesis registrada con éxito! Esperando validación.")
            return redirect('investigacion:lista_tesis') 
            
    return render(request, 'investigacion/registro.html')

def lista_tesis(request):
    estado_filtro = request.GET.get('estado')
    
    if estado_filtro and estado_filtro != 'todos':
        tesis_locales = Tesis.objects.filter(estado=estado_filtro).order_by('-fecha_registro')
    else:
        tesis_locales = Tesis.objects.all().order_by('-fecha_registro')

    return render(request, 'investigacion/lista.html', {
        'tesis_locales': tesis_locales,
        'estado_actual': estado_filtro or 'todos'
    })

def validar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    errores = []
    if not tesis.archivo_pdf:
        errores.append("Error: No se puede validar sin el archivo PDF original.")
    if len(tesis.resumen) < 10:
        errores.append("Error: El resumen es demasiado breve para los estándares ALICIA.")
    
    if errores:
        for error in errores:
            messages.error(request, error)
        return redirect('investigacion:lista_tesis')

    tesis.estado = 'validado'
    tesis.save()
    messages.success(request, f"¡Éxito! La tesis '{tesis.titulo[:30]}' ha sido validada correctamente.")
    return redirect('investigacion:lista_tesis')


def enviar_alicia(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    messages.info(request, f"Sincronizando '{tesis.titulo[:20]}' con el repositorio nacional...")
    return redirect('investigacion:lista_tesis')


def editar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    if request.method == 'POST':
        tesis.titulo = request.POST.get('titulo')
        tesis.autor = request.POST.get('autor')
        tesis.asesor = request.POST.get('asesor')
        tesis.resumen = request.POST.get('resumen')
        
        nuevo_archivo = request.FILES.get('archivo_pdf')
        if nuevo_archivo:
            tesis.archivo_pdf = nuevo_archivo
            
        tesis.save()
        messages.success(request, "¡Cambios guardados correctamente!")
        return redirect('investigacion:lista_tesis')
    
    return render(request, 'investigacion/registro.html', {
        'tesis': tesis, 
        'editando': True
    })
    
def eliminar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    tesis.delete()
    messages.warning(request, "La tesis ha sido eliminada del sistema.")
    return redirect('investigacion:lista_tesis')