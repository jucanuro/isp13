import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from lxml import etree

from .models import Asesor, Autor, PalabraClave, Tesis
from .oai import build_oai_dc


M2M_FIELDS = [
    "autores",
    "asesores",
    "jurados",
    "palabras_clave",
]


def _es_ajax(request):
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.POST.get("ajax") == "true"
    )


def _texto(request, field_name):
    return request.POST.get(field_name, "").strip()


def _obtener_fecha(request, field_name):
    if field_name not in request.POST:
        return None, False

    value = _texto(request, field_name)

    if not value:
        return None, True

    parsed_value = parse_date(value)

    if parsed_value is None:
        raise ValidationError(
            {
                field_name: (
                    "La fecha ingresada no tiene un formato válido."
                )
            }
        )

    return parsed_value, True


def _obtener_entero(request, field_name):
    if field_name not in request.POST:
        return None, False

    value = _texto(request, field_name)

    if not value:
        return None, True

    try:
        parsed_value = int(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(
            {
                field_name: (
                    "Debe ingresar un número entero válido."
                )
            }
        ) from error

    if parsed_value < 0:
        raise ValidationError(
            {
                field_name: (
                    "El valor no puede ser negativo."
                )
            }
        )

    return parsed_value, True


def _formatear_error_validacion(error):
    if hasattr(error, "message_dict"):
        errores = []

        for field_name, field_errors in error.message_dict.items():
            for field_error in field_errors:
                errores.append(
                    f"{field_name}: {field_error}"
                )

        return " | ".join(errores)

    if hasattr(error, "messages"):
        return " | ".join(error.messages)

    return str(error)


def _actualizar_campos_tesis(tesis, request):
    text_fields = [
        "titulo",
        "resumen",
        "tipo_tesis",
        "ocde_codigo",
        "ocde_nombre",
        "derechos_acceso",
        "idioma",
        "pais_publicacion",
        "version_publicacion",
        "grado_academico",
        "programa_academico",
        "disciplina_academica",
        "licencia_uri",
        "tipo_autorizacion",
    ]

    for field_name in text_fields:
        if field_name in request.POST:
            setattr(
                tesis,
                field_name,
                _texto(request, field_name),
            )

    if (
        not tesis.ocde_nombre
        and tesis.ocde_codigo
    ):
        tesis.ocde_nombre = (
            f"Área OCDE {tesis.ocde_codigo}"
        )

    date_fields = [
        "fecha_publicacion",
        "fecha_disponibilidad",
        "fecha_embargo_fin",
        "fecha_autorizacion",
    ]

    for field_name in date_fields:
        parsed_value, was_sent = _obtener_fecha(
            request,
            field_name,
        )

        if was_sent:
            setattr(
                tesis,
                field_name,
                parsed_value,
            )

    numero_paginas, was_sent = _obtener_entero(
        request,
        "numero_paginas",
    )

    if was_sent:
        tesis.numero_paginas = numero_paginas

    authorization_fields_sent = any(
        field_name in request.POST
        for field_name in [
            "acepta_publicacion",
            "tipo_autorizacion",
            "fecha_autorizacion",
        ]
    )

    if authorization_fields_sent:
        tesis.acepta_publicacion = (
            request.POST.get("acepta_publicacion")
            in {"1", "true", "on", "yes", "si", "sí"}
        )

    file_fields = [
        "archivo_pdf",
        "constancia_originalidad",
        "reporte_turnitin",
        "autorizacion_publicacion",
    ]

    for field_name in file_fields:
        uploaded_file = request.FILES.get(field_name)

        if uploaded_file:
            setattr(
                tesis,
                field_name,
                uploaded_file,
            )


def _sincronizar_palabras_clave(tesis, request):
    if "palabras_clave" not in request.POST:
        return

    raw_keywords = _texto(
        request,
        "palabras_clave",
    )

    keyword_names = [
        keyword.strip()
        for keyword in re.split(
            r"[,;\n]+",
            raw_keywords,
        )
        if keyword.strip()
    ]

    keyword_objects = []
    normalized_names = set()

    for keyword_name in keyword_names:
        normalized_name = keyword_name.casefold()

        if normalized_name in normalized_names:
            continue

        keyword = PalabraClave.objects.filter(
            nombre__iexact=keyword_name
        ).first()

        if keyword is None:
            keyword = PalabraClave.objects.create(
                nombre=keyword_name
            )

        keyword_objects.append(keyword)
        normalized_names.add(normalized_name)

    tesis.palabras_clave.set(keyword_objects)


def _contexto_formulario(tesis, editando):
    return {
        "tesis": tesis,
        "editando": editando,
        "tipos_grado": Tesis.TIPO_GRADO,
        "idiomas": Tesis.IDIOMAS,
        "versiones_publicacion": Tesis.VERSIONES,
        "derechos_acceso": Tesis.DERECHOS,
        "tipos_autorizacion": Tesis.TIPOS_AUTORIZACION,
        "autores_actuales": (
            tesis.autores.all()
            if tesis and tesis.pk
            else []
        ),
        "asesores_actuales": (
            tesis.asesores.all()
            if tesis and tesis.pk
            else []
        ),
        "jurados_actuales": (
            tesis.jurados.all()
            if tesis and tesis.pk
            else []
        ),
        "palabras_clave_actuales": (
            tesis.palabras_clave.all()
            if tesis and tesis.pk
            else []
        ),
    }


def _faltantes_validacion(tesis):
    faltantes = []

    if not tesis.titulo.strip():
        faltantes.append("Título")

    if not tesis.resumen.strip():
        faltantes.append("Resumen")

    if not tesis.tipo_tesis:
        faltantes.append("Tipo de documento")

    if not tesis.fecha_publicacion:
        faltantes.append("Fecha de publicación o sustentación")

    if not tesis.ocde_codigo:
        faltantes.append("Código OCDE")

    if not tesis.ocde_nombre:
        faltantes.append("Nombre del área OCDE")

    if not tesis.archivo_pdf:
        faltantes.append("Archivo PDF de la tesis")

    if not tesis.constancia_originalidad:
        faltantes.append("Constancia de originalidad")

    if not tesis.reporte_turnitin:
        faltantes.append("Reporte Turnitin")

    if not tesis.autores.exists():
        faltantes.append("Al menos un autor")

    if not tesis.asesores.exists():
        faltantes.append("Al menos un asesor")

    return faltantes


def _faltantes_publicacion(tesis):
    faltantes = _faltantes_validacion(tesis)

    if not tesis.institucion_nombre:
        faltantes.append("Institución responsable")

    if not tesis.institucion_pais:
        faltantes.append("País de la institución")

    if not tesis.idioma:
        faltantes.append("Idioma")

    if not tesis.pais_publicacion:
        faltantes.append("País de publicación")

    if not tesis.version_publicacion:
        faltantes.append("Versión de la publicación")

    if not tesis.derechos_acceso:
        faltantes.append("Nivel de acceso")

    if (
        tesis.derechos_acceso
        == "info:eu-repo/semantics/openAccess"
        and not tesis.licencia_uri
    ):
        faltantes.append(
            "Licencia de publicación para acceso abierto"
        )

    if not tesis.grado_academico:
        faltantes.append("Grado o título obtenido")

    if not tesis.programa_academico:
        faltantes.append("Programa académico")

    if not tesis.palabras_clave.exists():
        faltantes.append("Palabras clave")

    if not tesis.acepta_publicacion:
        faltantes.append(
            "Confirmación de autorización de publicación"
        )

    if not tesis.autorizacion_publicacion:
        faltantes.append(
            "Documento de autorización de publicación"
        )

    return list(dict.fromkeys(faltantes))


@login_required
def registrar_tesis(request):
    tesis = None

    tesis_id = (
        request.POST.get("tesis_id_hidden")
        or request.GET.get("tesis_id")
    )

    if tesis_id:
        tesis = Tesis.objects.filter(
            pk=tesis_id
        ).first()

    if request.method == "POST":
        titulo = _texto(request, "titulo")

        if _es_ajax(request):
            if not titulo:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Debe ingresar el título.",
                    },
                    status=400,
                )

            try:
                with transaction.atomic():
                    if tesis:
                        tesis.titulo = titulo
                        tesis.save(
                            update_fields=[
                                "titulo",
                                "fecha_actualizacion",
                            ]
                        )
                    else:
                        tesis = Tesis.objects.create(
                            titulo=titulo,
                            estado="pendiente",
                        )

                return JsonResponse(
                    {
                        "status": "success",
                        "id": tesis.pk,
                        "uuid": str(tesis.uuid),
                    }
                )

            except Exception as error:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": str(error),
                    },
                    status=500,
                )

        if tesis is None:
            messages.error(
                request,
                (
                    "Primero debe ingresar el título para "
                    "iniciar el registro."
                ),
            )
            return redirect(
                "investigacion:registrar_tesis"
            )

        try:
            with transaction.atomic():
                _actualizar_campos_tesis(
                    tesis,
                    request,
                )

                tesis.estado = "pendiente"

                tesis.full_clean(
                    exclude=M2M_FIELDS
                )
                tesis.save()

                _sincronizar_palabras_clave(
                    tesis,
                    request,
                )

            messages.success(
                request,
                "La investigación fue registrada correctamente.",
            )
            return redirect(
                "investigacion:lista_tesis"
            )

        except ValidationError as error:
            messages.error(
                request,
                _formatear_error_validacion(error),
            )

        except Exception as error:
            messages.error(
                request,
                f"Error al registrar: {error}",
            )

    return render(
        request,
        "investigacion/registro.html",
        _contexto_formulario(
            tesis,
            editando=False,
        ),
    )


@login_required
def editar_tesis(request, tesis_id):
    tesis = get_object_or_404(
        Tesis.objects.prefetch_related(
            "autores",
            "asesores",
            "jurados",
            "palabras_clave",
        ),
        pk=tesis_id,
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                estado_anterior = tesis.estado

                _actualizar_campos_tesis(
                    tesis,
                    request,
                )

                if estado_anterior in {
                    "pendiente",
                    "validado",
                }:
                    tesis.estado = "pendiente"

                tesis.full_clean(
                    exclude=M2M_FIELDS
                )
                tesis.save()

                _sincronizar_palabras_clave(
                    tesis,
                    request,
                )

            messages.success(
                request,
                (
                    f"La tesis '{tesis.titulo[:60]}' "
                    "fue actualizada correctamente."
                ),
            )
            return redirect(
                "investigacion:lista_tesis"
            )

        except ValidationError as error:
            messages.error(
                request,
                _formatear_error_validacion(error),
            )

        except Exception as error:
            messages.error(
                request,
                f"Error al actualizar: {error}",
            )

    return render(
        request,
        "investigacion/registro.html",
        _contexto_formulario(
            tesis,
            editando=True,
        ),
    )


@login_required
def lista_tesis(request):
    query = request.GET.get("q", "").strip()
    estado_filtro = request.GET.get(
        "estado",
        "",
    ).strip()

    tesis_queryset = (
        Tesis.objects
        .prefetch_related(
            "autores",
            "asesores",
            "palabras_clave",
        )
        .order_by("-fecha_registro")
    )

    if query:
        tesis_queryset = tesis_queryset.filter(
            Q(titulo__icontains=query)
            | Q(resumen__icontains=query)
            | Q(autores__nombre_completo__icontains=query)
            | Q(autores__dni__icontains=query)
            | Q(asesores__nombre_completo__icontains=query)
            | Q(programa_academico__icontains=query)
            | Q(grado_academico__icontains=query)
            | Q(palabras_clave__nombre__icontains=query)
        ).distinct()

    valid_states = {
        state_value
        for state_value, _ in Tesis.ESTADOS
    }

    if estado_filtro in valid_states:
        tesis_queryset = tesis_queryset.filter(
            estado=estado_filtro
        )

    paginator = Paginator(
        tesis_queryset,
        5,
    )

    tesis_paginadas = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "investigacion/lista.html",
        {
            "tesis_locales": tesis_paginadas,
            "estado_actual": (
                estado_filtro or "todos"
            ),
            "query_actual": query,
        },
    )


def repositorio_publico(request):
    query = request.GET.get("q", "").strip()

    tesis_queryset = (
        Tesis.objects
        .filter(
            estado="publicado",
            retirado=False,
        )
        .prefetch_related(
            "autores",
            "asesores",
            "palabras_clave",
        )
        .order_by(
            "-fecha_publicacion",
            "-fecha_registro",
        )
    )

    if query:
        tesis_queryset = tesis_queryset.filter(
            Q(titulo__icontains=query)
            | Q(resumen__icontains=query)
            | Q(autores__nombre_completo__icontains=query)
            | Q(asesores__nombre_completo__icontains=query)
            | Q(programa_academico__icontains=query)
            | Q(grado_academico__icontains=query)
            | Q(ocde_nombre__icontains=query)
            | Q(palabras_clave__nombre__icontains=query)
        ).distinct()

    paginator = Paginator(
        tesis_queryset,
        9,
    )

    tesis_paginadas = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "investigacion/repositorio_web.html",
        {
            "tesis_locales": tesis_paginadas,
            "query": query,
            "mostrar_boton_ver_mas": False,
            "template_base": "base.html",
        },
    )


def detalle_tesis(request, tesis_uuid):
    tesis = get_object_or_404(
        Tesis.objects.prefetch_related(
            "autores",
            "asesores",
            "jurados",
            "palabras_clave",
        ),
        uuid=tesis_uuid,
        estado="publicado",
        retirado=False,
    )

    return render(
        request,
        "investigacion/detalle_tesis.html",
        {
            "tesis": tesis,
            "template_base": "base.html",
        },
    )


@login_required
@require_POST
def validar_tesis(request, tesis_id):
    tesis = get_object_or_404(
        Tesis.objects.prefetch_related(
            "autores",
            "asesores",
        ),
        pk=tesis_id,
    )

    if tesis.estado == "publicado":
        messages.info(
            request,
            "La investigación ya está publicada.",
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    if tesis.estado == "retirado":
        messages.error(
            request,
            "Una investigación retirada no puede validarse.",
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    faltantes = _faltantes_validacion(tesis)

    if faltantes:
        messages.error(
            request,
            (
                "No se puede validar. Faltan: "
                + ", ".join(faltantes)
                + "."
            ),
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    try:
        tesis.full_clean(
            exclude=M2M_FIELDS
        )
        tesis.estado = "validado"
        tesis.save()

        messages.success(
            request,
            (
                f"La investigación #{tesis.pk} "
                "fue validada correctamente."
            ),
        )

    except ValidationError as error:
        messages.error(
            request,
            _formatear_error_validacion(error),
        )

    except Exception as error:
        messages.error(
            request,
            f"Error al validar: {error}",
        )

    return redirect(
        "investigacion:lista_tesis"
    )


@login_required
@require_POST
def enviar_alicia(request, tesis_id):
    tesis = get_object_or_404(
        Tesis.objects.prefetch_related(
            "autores",
            "asesores",
            "palabras_clave",
        ),
        pk=tesis_id,
    )

    if tesis.estado == "pendiente":
        messages.warning(
            request,
            (
                "La investigación primero debe "
                "ser validada por Biblioteca."
            ),
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    if tesis.estado == "publicado":
        messages.info(
            request,
            "La investigación ya está publicada.",
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    if tesis.estado == "retirado":
        messages.error(
            request,
            "Una investigación retirada no puede publicarse.",
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    faltantes = _faltantes_publicacion(tesis)

    if faltantes:
        messages.error(
            request,
            (
                "No se puede publicar. Faltan: "
                + ", ".join(faltantes)
                + "."
            ),
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    try:
        with transaction.atomic():
            if not tesis.fecha_disponibilidad:
                tesis.fecha_disponibilidad = (
                    timezone.localdate()
                )

            tesis.full_clean(
                exclude=M2M_FIELDS
            )
            tesis.estado = "publicado"
            tesis.retirado = False
            tesis.save()

        messages.success(
            request,
            (
                f"La investigación '{tesis.titulo[:60]}' "
                "fue publicada en el repositorio y quedó "
                "disponible en el endpoint institucional "
                "para su cosecha."
            ),
        )

    except ValidationError as error:
        messages.error(
            request,
            _formatear_error_validacion(error),
        )

    except Exception as error:
        messages.error(
            request,
            f"Error técnico al publicar: {error}",
        )

    return redirect(
        "investigacion:lista_tesis"
    )


def oai_repository(request, tesis_id):
    tesis = get_object_or_404(
        Tesis.objects.prefetch_related(
            "autores",
            "asesores",
            "palabras_clave",
        ),
        pk=tesis_id,
        estado="publicado",
        retirado=False,
    )

    root = build_oai_dc(
        tesis,
        request,
    )

    xml_output = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )

    return HttpResponse(
        xml_output,
        content_type="application/xml; charset=utf-8",
    )


@login_required
@require_POST
def eliminar_tesis(request, tesis_id):
    tesis = get_object_or_404(
        Tesis,
        pk=tesis_id,
    )

    if tesis.estado in {
        "publicado",
        "retirado",
    }:
        messages.error(
            request,
            (
                "No se puede eliminar una investigación "
                "publicada o retirada. Debe conservarse "
                "su trazabilidad institucional."
            ),
        )
        return redirect(
            "investigacion:lista_tesis"
        )

    titulo_eliminado = tesis.titulo[:60]

    try:
        tesis.delete()

        messages.warning(
            request,
            (
                f"La investigación '{titulo_eliminado}' "
                "fue eliminada del registro local."
            ),
        )

    except Exception as error:
        messages.error(
            request,
            f"Error al eliminar: {error}",
        )

    return redirect(
        "investigacion:lista_tesis"
    )


@login_required
@require_POST
def agregar_autor_ajax(request, tesis_id):
    tesis = get_object_or_404(
        Tesis,
        pk=tesis_id,
    )

    nombre = _texto(request, "nombre")
    dni = _texto(request, "dni")
    orcid = _texto(request, "orcid")

    if not nombre:
        return JsonResponse(
            {
                "status": "error",
                "message": "Debe ingresar el nombre del autor.",
            },
            status=400,
        )

    if not dni:
        return JsonResponse(
            {
                "status": "error",
                "message": (
                    "Debe ingresar el documento del autor."
                ),
            },
            status=400,
        )

    try:
        with transaction.atomic():
            autor = Autor.objects.filter(
                dni=dni
            ).first()

            if autor is None:
                autor = Autor(
                    nombre_completo=nombre,
                    dni=dni,
                    orcid=orcid or None,
                )
            else:
                autor.nombre_completo = nombre

                if orcid:
                    autor.orcid = orcid

            autor.full_clean()
            autor.save()
            tesis.autores.add(autor)

        return JsonResponse(
            {
                "status": "success",
                "id": autor.pk,
                "nombre": autor.nombre_completo,
                "dni": autor.dni,
                "orcid": autor.orcid or "",
            }
        )

    except ValidationError as error:
        return JsonResponse(
            {
                "status": "error",
                "message": _formatear_error_validacion(
                    error
                ),
            },
            status=400,
        )

    except IntegrityError:
        return JsonResponse(
            {
                "status": "error",
                "message": (
                    "Ya existe un autor con ese documento."
                ),
            },
            status=409,
        )

    except Exception as error:
        return JsonResponse(
            {
                "status": "error",
                "message": str(error),
            },
            status=500,
        )


@login_required
@require_POST
def agregar_asesor_ajax(request, tesis_id):
    tesis = get_object_or_404(
        Tesis,
        pk=tesis_id,
    )

    nombre = _texto(request, "nombre")
    dni = _texto(request, "dni")
    orcid = _texto(request, "orcid")

    if not nombre:
        return JsonResponse(
            {
                "status": "error",
                "message": "Debe ingresar el nombre del asesor.",
            },
            status=400,
        )

    try:
        with transaction.atomic():
            asesor = None

            if dni:
                asesor = Asesor.objects.filter(
                    dni=dni
                ).first()

            if asesor is None:
                asesor = Asesor.objects.filter(
                    nombre_completo__iexact=nombre
                ).first()

            if asesor is None:
                asesor = Asesor(
                    nombre_completo=nombre,
                    dni=dni or None,
                    orcid=orcid or None,
                )
            else:
                asesor.nombre_completo = nombre

                if dni:
                    asesor.dni = dni

                if orcid:
                    asesor.orcid = orcid

            asesor.full_clean()
            asesor.save()
            tesis.asesores.add(asesor)

        return JsonResponse(
            {
                "status": "success",
                "id": asesor.pk,
                "nombre": asesor.nombre_completo,
                "dni": asesor.dni or "",
                "orcid": asesor.orcid or "",
            }
        )

    except ValidationError as error:
        return JsonResponse(
            {
                "status": "error",
                "message": _formatear_error_validacion(
                    error
                ),
            },
            status=400,
        )

    except IntegrityError:
        return JsonResponse(
            {
                "status": "error",
                "message": (
                    "Ya existe un asesor con ese documento."
                ),
            },
            status=409,
        )

    except Exception as error:
        return JsonResponse(
            {
                "status": "error",
                "message": str(error),
            },
            status=500,
        )


@login_required
@require_POST
def eliminar_relacion_ajax(request, tesis_id):
    tesis = get_object_or_404(
        Tesis,
        pk=tesis_id,
    )

    relation_type = _texto(
        request,
        "tipo",
    )

    person_id = _texto(
        request,
        "persona_id",
    )

    if relation_type not in {
        "autor",
        "asesor",
    }:
        return JsonResponse(
            {
                "status": "error",
                "message": "Tipo de relación no válido.",
            },
            status=400,
        )

    if not person_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "No se recibió el identificador.",
            },
            status=400,
        )

    try:
        if relation_type == "autor":
            person = get_object_or_404(
                Autor,
                pk=person_id,
            )
            tesis.autores.remove(person)

        else:
            person = get_object_or_404(
                Asesor,
                pk=person_id,
            )
            tesis.asesores.remove(person)

        return JsonResponse(
            {
                "status": "success",
            }
        )

    except Exception as error:
        return JsonResponse(
            {
                "status": "error",
                "message": str(error),
            },
            status=500,
        )