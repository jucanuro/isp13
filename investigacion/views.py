from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.core.paginator import Paginator
from .models import Tesis, Autor, Asesor
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from lxml import etree
from django.db.models import Q

@login_required
def registrar_tesis(request):
    tesis = None
    id_hidden = request.POST.get('tesis_id_hidden')
    if id_hidden:
        tesis = Tesis.objects.filter(id=id_hidden).first()

    if request.method == 'POST':
        es_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true'
        titulo = request.POST.get('titulo', '').strip()

        if es_ajax:
            if not titulo:
                return JsonResponse({'status': 'error', 'message': 'Título vacío'}, status=400)
            
            if tesis:
                tesis.titulo = titulo
                tesis.save()
            else:
                tesis = Tesis.objects.create(titulo=titulo, estado='pendiente')
            return JsonResponse({'status': 'success', 'id': tesis.id})

        if not tesis:
            messages.error(request, "Error: Inicie el registro con un título para activar el sistema.")
            return redirect('investigacion:registrar_tesis')

        try:
            tesis.titulo = titulo or tesis.titulo
            tesis.resumen = request.POST.get('resumen', '').strip()
            tesis.tipo_tesis = request.POST.get('tipo_tesis')
            tesis.ocde_codigo = request.POST.get('ocde_codigo', '').strip()
            tesis.ocde_nombre = request.POST.get('ocde_nombre', '').strip() or f"Área OCDE {tesis.ocde_codigo}"
            tesis.derechos_acceso = request.POST.get('derechos_acceso')
            
            fecha = request.POST.get('fecha_publicacion')
            tesis.fecha_publicacion = fecha if (fecha and fecha.strip()) else None

            if 'archivo_pdf' in request.FILES: tesis.archivo_pdf = request.FILES['archivo_pdf']
            if 'constancia_originalidad' in request.FILES: tesis.constancia_originalidad = request.FILES['constancia_originalidad']
            if 'reporte_turnitin' in request.FILES: tesis.reporte_turnitin = request.FILES['reporte_turnitin']
            
            tesis.save()
            messages.success(request, "Registro completado con éxito.")
            return redirect('investigacion:lista_tesis')

        except Exception as e:
            messages.error(request, f"Error al registrar: {e}")
            
    return render(request, 'investigacion/registro.html', {
        'tesis': tesis,
        'tipos_grado': Tesis.TIPO_GRADO,
        'editando': False
    })

@login_required
def editar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis.objects.prefetch_related('autores', 'asesores'), id=tesis_id)
    
    if request.method == 'POST':
        try:
            # 1. Metadatos básicos
            tesis.titulo = request.POST.get('titulo')
            tesis.resumen = request.POST.get('resumen')
            tesis.tipo_tesis = request.POST.get('tipo_tesis')
            tesis.ocde_codigo = request.POST.get('ocde_codigo')
            tesis.ocde_nombre = request.POST.get('ocde_nombre') or f"Área OCDE {tesis.ocde_codigo}"
            tesis.derechos_acceso = request.POST.get('derechos_acceso')
            
            # 2. Fecha (Formato ISO para evitar errores de base de datos)
            fecha = request.POST.get('fecha_publicacion')
            tesis.fecha_publicacion = fecha if (fecha and fecha.strip()) else None

            # 3. Archivos (Solo se actualizan si se cargan nuevos)
            if 'archivo_pdf' in request.FILES:
                tesis.archivo_pdf = request.FILES['archivo_pdf']
            if 'constancia_originalidad' in request.FILES:
                tesis.constancia_originalidad = request.FILES['constancia_originalidad']
            if 'reporte_turnitin' in request.FILES:
                tesis.reporte_turnitin = request.FILES['reporte_turnitin']

            # 4. Estado: Si no está publicado, vuelve a pendiente para revisión
            if tesis.estado != 'publicado':
                tesis.estado = 'pendiente'
            
            tesis.save()
            messages.success(request, f"Tesis '{tesis.titulo[:50]}' actualizada.")
            return redirect('investigacion:lista_tesis')

        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")
        
    return render(request, 'investigacion/registro.html', {
        'tesis': tesis, 
        'editando': True, 
        'tipos_grado': Tesis.TIPO_GRADO,
        'autores_actuales': tesis.autores.all(),
        'asesores_actuales': tesis.asesores.all()
    })

@login_required
def lista_tesis(request):
    query = request.GET.get('q')
    estado_filtro = request.GET.get('estado')
    
    tesis_queryset = Tesis.objects.all().prefetch_related('autores', 'asesores').order_by('-fecha_registro')

    if query:
        tesis_queryset = tesis_queryset.filter(
            models.Q(titulo__icontains=query) | 
            models.Q(autores__nombre_completo__icontains=query) |
            models.Q(autores__dni__icontains=query)
        ).distinct() 

    if estado_filtro and estado_filtro != 'todos':
        tesis_queryset = tesis_queryset.filter(estado=estado_filtro)

    paginator = Paginator(tesis_queryset, 5) 
    page_number = request.GET.get('page')
    tesis_paginadas = paginator.get_page(page_number)

    return render(request, 'investigacion/lista.html', {
        'tesis_locales': tesis_paginadas, 
        'estado_actual': estado_filtro or 'todos',
        'query_actual': query or ''
    })


def repositorio_publico(request):
    query = request.GET.get('q')
    tesis_queryset = Tesis.objects.filter(estado='publicado').prefetch_related('autores', 'asesores').order_by('-fecha_registro')

    if query:
        tesis_queryset = Tesis.objects.filter(estado='publicado').prefetch_related('autores')

    paginator = Paginator(tesis_queryset, 9)
    page_number = request.GET.get('page')
    tesis_paginadas = paginator.get_page(page_number)

    return render(request, 'investigacion/repositorio_web.html', {
        'tesis_locales': tesis_paginadas,
        'query': query or '',
        'mostrar_boton_ver_mas': False, 
        'template_base': 'base.html',
    })

@login_required
def validar_tesis(request, tesis_id):
    # 1. Obtenemos la tesis
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    if request.method == 'POST':
        errores = []

        if not tesis.archivo_pdf: 
            errores.append("Falta el archivo PDF.")
        
        if not tesis.autores.exists():
            errores.append("Debe tener al menos un autor.")

        if not tesis.ocde_codigo:
            errores.append("Falta el código OCDE.")

        if errores:
            for error in errores:
                messages.error(request, f"ID #({tesis_id}): {error}")
            return redirect('investigacion:lista_tesis')

        try:
            tesis.estado = 'validado' 
            tesis.save()
            messages.success(request, f"¡Tesis #{tesis_id} validada correctamente!")
        except Exception as e:
            messages.error(request, f"Error al guardar en base de datos: {e}")
            
    return redirect('investigacion:lista_tesis')

@login_required
def enviar_alicia(request, tesis_id):
    tesis = get_object_or_404(Tesis.objects.prefetch_related('autores', 'asesores'), id=tesis_id)
    
    if tesis.estado == 'pendiente':
        messages.warning(request, f"La tesis '{tesis.titulo[:30]}' primero debe ser validada por un revisor.")
        return redirect('investigacion:lista_tesis')
    
    if tesis.estado == 'publicado':
        messages.info(request, "Esta tesis ya se encuentra publicada.")
        return redirect('investigacion:lista_tesis')

    faltantes = []

    if not tesis.titulo:
        faltantes.append("Título (dc:title)")
    if not tesis.resumen:
        faltantes.append("Resumen (dc:description)")
    if not tesis.tipo_tesis:
        faltantes.append("Tipo de Tesis (dc:type)")
    if not tesis.ocde_codigo:
        faltantes.append("Código OCDE (dc:subject)")
    
    if not tesis.archivo_pdf:
        faltantes.append("Archivo PDF de la Tesis")
    if not tesis.constancia_originalidad:
        faltantes.append("Constancia de Originalidad")
    if not tesis.reporte_turnitin:
        faltantes.append("Reporte Turnitin")

    autores = tesis.autores.all()
    if not autores.exists():
        faltantes.append("Al menos un Autor (dc:creator)")
    else:
        for autor in autores:
            if not autor.dni:
                faltantes.append(f"DNI del autor {autor.nombre_completo}")

    if faltantes:
        messages.error(request, f"No se puede publicar. Faltan requisitos de la Guía ALICIA: {', '.join(faltantes)}")
        return redirect('investigacion:lista_tesis')

    try:
        tesis.estado = 'publicado' 
        tesis.save()
        
        messages.success(request, (
            f"¡Publicación Exitosa! La tesis '{tesis.titulo[:50]}...' con sus {autores.count()} "
            f"autor(es) ya está disponible para el recolector nacional de CONCYTEC."
        ))
    except Exception as e:
        messages.error(request, f"Error técnico al guardar: {e}")

    return redirect('investigacion:lista_tesis')

def oai_repository(request, tesis_id):
    tesis = get_object_or_404(Tesis.objects.prefetch_related('autores', 'asesores'), id=tesis_id, estado='publicado')
    
    NS_MAP = {
        'oai_dc': "http://www.openarchives.org/OAI/2.0/oai_dc/",
        'dc': "http://purl.org/dc/elements/1.1/",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }

    schema_location = "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    
    root = etree.Element(
        "{%s}dc" % NS_MAP['oai_dc'], 
        nsmap=NS_MAP,
        attrib={"{%s}schemaLocation" % NS_MAP['xsi']: schema_location}
    )
    
    clean_tipo = tesis.tipo_tesis.split('_')[0]
    
    # 1. Título
    etree.SubElement(root, "{%s}title" % NS_MAP['dc']).text = tesis.titulo
    
    # 2. AUTORES (Múltiples dc:creator e identifiers)
    for autor in tesis.autores.all():
        etree.SubElement(root, "{%s}creator" % NS_MAP['dc']).text = autor.nombre_completo
        # ALICIA exige el DNI como identifier
        etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = f"DNI:{autor.dni}"
        if autor.orcid:
            etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = autor.orcid

    # 3. ASESORES (Múltiples dc:contributor)
    for asesor in tesis.asesores.all():
        etree.SubElement(root, "{%s}contributor" % NS_MAP['dc']).text = asesor.nombre_completo

    # 4. Metadatos Descriptivos
    etree.SubElement(root, "{%s}description" % NS_MAP['dc']).text = tesis.resumen
    etree.SubElement(root, "{%s}publisher" % NS_MAP['dc']).text = tesis.institucion_nombre
    etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = f"RUC:{tesis.institucion_ruc}"
    
    if tesis.fecha_publicacion:
        etree.SubElement(root, "{%s}date" % NS_MAP['dc']).text = tesis.fecha_publicacion.strftime('%Y-%m-%d')
    
    # 5. Clasificación Técnica (Guía ALICIA 2.0)
    etree.SubElement(root, "{%s}type" % NS_MAP['dc']).text = clean_tipo
    etree.SubElement(root, "{%s}subject" % NS_MAP['dc']).text = f"OCDE:{tesis.ocde_codigo}"
    etree.SubElement(root, "{%s}subject" % NS_MAP['dc']).text = tesis.ocde_nombre
    etree.SubElement(root, "{%s}rights" % NS_MAP['dc']).text = tesis.derechos_acceso
    etree.SubElement(root, "{%s}language" % NS_MAP['dc']).text = "spa"
    etree.SubElement(root, "{%s}publisher" % NS_MAP['dc']).text = tesis.institucion_pais
    
    # 6. Enlace al archivo PDF principal
    if tesis.archivo_pdf:
        full_url = request.build_absolute_uri(tesis.archivo_pdf.url)
        etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = full_url

    xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return HttpResponse(xml_output, content_type="application/xml")

@login_required
def eliminar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    titulo_eliminado = tesis.titulo[:50]

    if tesis.estado == 'publicado':
        messages.error(request, f"No se puede eliminar la tesis '{titulo_eliminado}' porque ya está publicada en el repositorio nacional.")
        return redirect('investigacion:lista_tesis')

    try:
        tesis.delete()
        
        messages.warning(request, f"La investigación '{titulo_eliminado}...' ha sido eliminada del registro local.")
    except Exception as e:
        messages.error(request, f"Error técnico al intentar eliminar: {e}")

    return redirect('investigacion:lista_tesis')

@login_required
def agregar_autor_ajax(request, tesis_id):
    if request.method == 'POST':
        tesis = get_object_or_404(Tesis, id=tesis_id)
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        try:
            autor, _ = Autor.objects.get_or_create(dni=dni, defaults={'nombre_completo': nombre})
            tesis.autores.add(autor)
            return JsonResponse({'status': 'success', 'id': autor.id, 'nombre': autor.nombre_completo, 'dni': autor.dni})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def agregar_asesor_ajax(request, tesis_id):
    if request.method == 'POST':
        tesis = get_object_or_404(Tesis, id=tesis_id)
        nombre = request.POST.get('nombre')
        try:
            asesor, _ = Asesor.objects.get_or_create(nombre_completo=nombre)
            tesis.asesores.add(asesor)
            return JsonResponse({'status': 'success', 'id': asesor.id, 'nombre': asesor.nombre_completo})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def eliminar_relacion_ajax(request, tesis_id):
    if request.method == 'POST':
        tesis = get_object_or_404(Tesis, id=tesis_id)
        tipo = request.POST.get('tipo')
        p_id = request.POST.get('persona_id')
        try:
            if tipo == 'autor':
                p = get_object_or_404(Autor, id=p_id)
                tesis.autores.remove(p)
            else:
                p = get_object_or_404(Asesor, id=p_id)
                tesis.asesores.remove(p)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)