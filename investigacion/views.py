from django.shortcuts import render, redirect, get_object_or_404
from .models import Tesis
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from lxml import etree

@login_required
def registrar_tesis(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        autor = request.POST.get('autor', '').strip()
        autor_dni = request.POST.get('autor_dni', '').strip()
        autor_orcid = request.POST.get('autor_orcid', '').strip()
        asesor = request.POST.get('asesor', '').strip()
        resumen = request.POST.get('resumen', '').strip()
        
        tipo_tesis = request.POST.get('tipo_tesis')
        ocde_codigo = request.POST.get('ocde_codigo', '').strip()
        ocde_nombre = request.POST.get('ocde_nombre', '').strip()
        fecha_pub = request.POST.get('fecha_publicacion')
        derechos = request.POST.get('derechos_acceso', 'info:eu-repo/semantics/openAccess')
        
        archivo = request.FILES.get('archivo_pdf')

        if not ocde_nombre and ocde_codigo:
            ocde_nombre = f"Área OCDE {ocde_codigo}"
        elif not ocde_nombre:
            ocde_nombre = "Por definir"

        errores = []
        if not titulo: errores.append("El título es obligatorio.")
        if not autor: errores.append("El nombre del autor es obligatorio.")
        if not autor_dni or len(autor_dni) < 8: errores.append("DNI del autor no válido para RENATI.")
        if not archivo: errores.append("Debe subir el archivo PDF de la tesis.")

        if not errores:
            try:
                nueva_tesis = Tesis(
                    titulo=titulo,
                    autor=autor,
                    autor_dni=autor_dni,
                    autor_orcid=autor_orcid if autor_orcid else None,
                    asesor=asesor,
                    resumen=resumen,
                    tipo_tesis=tipo_tesis,
                    ocde_codigo=ocde_codigo,
                    ocde_nombre=ocde_nombre, 
                    fecha_publicacion=fecha_pub if fecha_pub and fecha_pub != '' else None,
                    archivo_pdf=archivo,
                    derechos_acceso=derechos,
                    estado='pendiente'
                )
                nueva_tesis.save()
                
                messages.success(request, f"¡Éxito! '{titulo[:60]}...' registrado. Se requiere validación técnica para ALICIA.")
                return redirect('investigacion:lista_tesis')
                
            except Exception as e:
                messages.error(request, f"Error de base de datos: {e}")
        else:
            for error in errores:
                messages.error(request, error)
            
    return render(request, 'investigacion/registro.html', {
        'tipos_grado': Tesis.TIPO_GRADO
    })

@login_required
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

@login_required
def validar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    errores = []
    if not tesis.archivo_pdf:
        errores.append("Error: No se puede validar sin el archivo PDF original.")
    if not tesis.autor_dni:
        errores.append("Error: El DNI es obligatorio para el reporte RENATI.")
    if not tesis.ocde_codigo:
        errores.append("Error: Debe asignar un código OCDE válido.")
    if len(tesis.resumen) < 50:
        errores.append("Error: El resumen es muy corto para los estándares de CONCYTEC.")
    
    if errores:
        for error in errores:
            messages.error(request, error)
        return redirect('investigacion:lista_tesis')

    tesis.estado = 'validado'
    tesis.save()
    messages.success(request, f"¡Éxito! La tesis '{tesis.titulo[:30]}' ha sido validada.")
    return redirect('investigacion:lista_tesis')

@login_required
def enviar_alicia(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    if tesis.estado == 'pendiente':
        messages.warning(request, f"La tesis '{tesis.titulo[:30]}' primero debe ser validada por un revisor.")
        return redirect('investigacion:lista_tesis')
    
    if tesis.estado == 'publicado':
        messages.info(request, "Esta tesis ya se encuentra publicada.")
        return redirect('investigacion:lista_tesis')

    campos_obligatorios = {
        'Título (dc:title)': tesis.titulo,
        'Autor (dc:creator)': tesis.autor,
        'Resumen (dc:description)': tesis.resumen,
        'Tipo de Tesis (dc:type)': tesis.tipo_tesis,
        'Código OCDE (dc:subject)': tesis.ocde_codigo,
        'DNI del Autor': tesis.autor_dni,
    }
    
    faltantes = [k for k, v in campos_obligatorios.items() if not v]

    if not tesis.archivo_pdf:
        faltantes.append("Archivo PDF de la Tesis")

    if faltantes:
        messages.error(request, f"No se puede publicar. Faltan requisitos de la Guía ALICIA: {', '.join(faltantes)}")
        return redirect('investigacion:lista_tesis')

    try:
        tesis.estado = 'publicado' 
        tesis.save()
        messages.success(request, "¡Publicación Exitosa! La tesis ya está disponible para el recolector nacional de CONCYTEC.")
    except Exception as e:
        messages.error(request, f"Error técnico al guardar: {e}")

    return redirect('investigacion:lista_tesis')

def oai_repository(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id, estado='publicado')
    
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
    
    etree.SubElement(root, "{%s}title" % NS_MAP['dc']).text = tesis.titulo
    etree.SubElement(root, "{%s}creator" % NS_MAP['dc']).text = tesis.autor
    etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = f"DNI:{tesis.autor_dni}"
    
    if tesis.autor_orcid:
        etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = tesis.autor_orcid

    etree.SubElement(root, "{%s}contributor" % NS_MAP['dc']).text = tesis.asesor
    etree.SubElement(root, "{%s}description" % NS_MAP['dc']).text = tesis.resumen
    etree.SubElement(root, "{%s}publisher" % NS_MAP['dc']).text = tesis.institucion_nombre
    etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = f"RUC:{tesis.institucion_ruc}"
    
    if tesis.fecha_publicacion:
        etree.SubElement(root, "{%s}date" % NS_MAP['dc']).text = tesis.fecha_publicacion.strftime('%Y-%m-%d')
    
    etree.SubElement(root, "{%s}type" % NS_MAP['dc']).text = clean_tipo
    etree.SubElement(root, "{%s}subject" % NS_MAP['dc']).text = f"OCDE:{tesis.ocde_codigo}"
    etree.SubElement(root, "{%s}subject" % NS_MAP['dc']).text = tesis.ocde_nombre
    etree.SubElement(root, "{%s}rights" % NS_MAP['dc']).text = tesis.derechos_acceso
    etree.SubElement(root, "{%s}language" % NS_MAP['dc']).text = "spa"
    etree.SubElement(root, "{%s}publisher" % NS_MAP['dc']).text = tesis.institucion_pais
    
    if tesis.archivo_pdf:
        full_url = request.build_absolute_uri(tesis.archivo_pdf.url)
        etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = full_url

    xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return HttpResponse(xml_output, content_type="application/xml")

@login_required
def editar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    if request.method == 'POST':
        tesis.titulo = request.POST.get('titulo')
        tesis.autor = request.POST.get('autor')
        tesis.autor_dni = request.POST.get('autor_dni')
        tesis.asesor = request.POST.get('asesor')
        tesis.resumen = request.POST.get('resumen')
        tesis.tipo_tesis = request.POST.get('tipo_tesis')
        tesis.ocde_codigo = request.POST.get('ocde_codigo')
        
        if request.FILES.get('archivo_pdf'):
            tesis.archivo_pdf = request.FILES.get('archivo_pdf')
            
        tesis.save()
        messages.success(request, "¡Cambios guardados exitosamente!")
        return redirect('investigacion:lista_tesis')
        
    return render(request, 'investigacion/registro.html', {
        'tesis': tesis, 
        'editando': True, 
        'tipos_grado': Tesis.TIPO_GRADO
    })

@login_required
def eliminar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    tesis.delete()
    messages.warning(request, "La tesis ha sido eliminada del registro local.")
    return redirect('investigacion:lista_tesis')