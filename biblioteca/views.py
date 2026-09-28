"""Vistas de la biblioteca institucional.

El catálogo une Libro (propio) y Tesis publicadas (de investigacion), leídas en
vivo: si una tesis se despublica, deja de aparecer aquí sin hacer nada más.
No hay copia, ni señales, ni sincronización entre ambos modelos. Tampoco hay
nada que vaya hacia /oai/: el flujo es Tesis → catálogo, nunca al revés.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from investigacion.models import Tesis

from .forms import LibroForm
from .models import Categoria, Libro


POR_PAGINA = 12
BIBLIOTECA_VIRTUAL_URL = (
    "https://13dejuliode1882spedupe.sharepoint.com/sites/BibliotecaVirtual"
)

# Filtro "tipo": todos, solo libros, solo tesis, o un tipo concreto de libro.
TIPOS_FILTRO = [("", "Todos"), ("libros", "Libros"), ("tesis", "Tesis")] + Libro.TIPOS
TIPOS_LIBRO = {clave for clave, _ in Libro.TIPOS}


def _tesis_publicadas():
    # Mismo criterio que investigacion.views.detalle_tesis, para que cada
    # tarjeta de tesis del catálogo abra una ficha que exista.
    return Tesis.objects.filter(estado="publicado", retirado=False)


def _querysets_filtrados(tipo, categoria, query):
    """Devuelve (libros, tesis); cualquiera puede ser None si el filtro lo excluye."""
    libros = Libro.objects.filter(activo=True)
    tesis = _tesis_publicadas()

    if tipo == "libros":
        tesis = None
    elif tipo == "tesis":
        libros = None
    elif tipo in TIPOS_LIBRO:
        libros = libros.filter(tipo=tipo)
        tesis = None

    if categoria:
        # Las tesis no tienen categoría: filtrar por una deja solo libros.
        tesis = None
        if libros is not None:
            libros = libros.filter(categoria__slug=categoria)

    if query:
        if libros is not None:
            libros = libros.filter(Q(titulo__icontains=query) | Q(autores__icontains=query))
        if tesis is not None:
            tesis = tesis.filter(
                Q(titulo__icontains=query) | Q(autores__nombre_completo__icontains=query)
            ).distinct()

    return libros, tesis


def _claves_ordenadas(libros, tesis):
    """Une ambos orígenes como claves livianas y las ordena (más reciente primero).

    Solo se traen tres columnas por fila (fecha, origen, pk), no los objetos:
    ordenar y contar la unión cuesta una lista de tuplas en memoria. Los objetos
    completos se cargan después, solo para la página visible.
    """
    claves = []
    if libros is not None:
        claves += [(f, "libro", pk) for f, pk in libros.values_list("fecha_registro", "pk")]
    if tesis is not None:
        claves += [(f, "tesis", pk) for f, pk in tesis.values_list("fecha_registro", "pk")]
    claves.sort(reverse=True)
    return claves


def _normalizar_libro(libro):
    return {
        "titulo": libro.titulo,
        "autores": libro.autores,
        "tipo_label": libro.get_tipo_display(),
        "anio": libro.anio_publicacion,
        "descripcion": libro.descripcion,
        "imagen": libro.portada.url if libro.portada else None,
        "inicial": libro.titulo[:1].upper(),
        "url_detalle": reverse("biblioteca:detalle_libro", args=[libro.pk]),
        "url_pdf": None,
        "origen": "libro",
    }


def _normalizar_tesis(tesis):
    return {
        "titulo": tesis.titulo,
        # .all() usa el prefetch; no dispara una query por tesis.
        "autores": "; ".join(a.nombre_completo for a in tesis.autores.all()),
        "tipo_label": "Tesis",
        "anio": tesis.fecha_publicacion.year if tesis.fecha_publicacion else None,
        "descripcion": tesis.resumen,
        "imagen": None,
        "inicial": "",
        "url_detalle": reverse("investigacion:detalle_tesis", args=[tesis.uuid]),
        "url_pdf": tesis.archivo_pdf.url if tesis.archivo_pdf else None,
        "origen": "tesis",
    }


def _cargar_pagina(claves_pagina):
    ids_libros = [pk for _, origen, pk in claves_pagina if origen == "libro"]
    ids_tesis = [pk for _, origen, pk in claves_pagina if origen == "tesis"]

    libros = Libro.objects.in_bulk(ids_libros)
    tesis = (
        _tesis_publicadas()
        .filter(pk__in=ids_tesis)
        .prefetch_related("autores")
        .in_bulk()
    )

    items = []
    for _, origen, pk in claves_pagina:
        # Una tesis despublicada entre las dos consultas simplemente se omite.
        if origen == "libro" and pk in libros:
            items.append(_normalizar_libro(libros[pk]))
        elif origen == "tesis" and pk in tesis:
            items.append(_normalizar_tesis(tesis[pk]))
    return items


def catalogo(request):
    tipo = request.GET.get("tipo", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    query = request.GET.get("q", "").strip()

    if tipo not in dict(TIPOS_FILTRO):
        tipo = ""

    libros, tesis = _querysets_filtrados(tipo, categoria, query)

    paginator = Paginator(_claves_ordenadas(libros, tesis), POR_PAGINA)
    pagina = paginator.get_page(request.GET.get("page"))
    items = _cargar_pagina(pagina.object_list)

    # Mismo rango recortado con "…" que repositorio_web.html.
    page_range = paginator.get_elided_page_range(
        pagina.number,
        on_each_side=2,
        on_ends=1,
    )

    return render(
        request,
        "biblioteca/catalogo.html",
        {
            "items": items,
            "pagina": pagina,
            "page_range": page_range,
            "paginator_ellipsis": str(Paginator.ELLIPSIS),
            "tipos_filtro": TIPOS_FILTRO,
            "categorias": Categoria.objects.filter(activo=True),
            "tipo": tipo,
            "categoria": categoria,
            "query": query,
            "hay_filtros": bool(tipo or categoria or query),
            "biblioteca_virtual_url": BIBLIOTECA_VIRTUAL_URL,
        },
    )


def detalle_libro(request, pk):
    libro = get_object_or_404(
        Libro.objects.select_related("categoria"), pk=pk, activo=True
    )
    return render(request, "biblioteca/detalle_libro.html", {"libro": libro})


def staff_requerido(vista):
    """Tras @login_required: un usuario logueado sin is_staff recibe 403, no
    una redirección al login (que lo devolvería aquí en bucle)."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return vista(request, *args, **kwargs)

    return envoltura


@login_required
@staff_requerido
@require_http_methods(["GET", "POST"])
def registrar_libro(request):
    if request.method == "POST":
        form = LibroForm(request.POST, request.FILES)
        if form.is_valid():
            libro = form.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"«{libro.titulo}» quedó registrado en el catálogo.",
                    "redirect": reverse("biblioteca:detalle_libro", args=[libro.pk]),
                }
            )
        # Errores por campo: el cliente pinta cada uno junto a su input.
        return JsonResponse(
            {
                "status": "error",
                "message": "Revise los campos marcados.",
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )

    return render(request, "biblioteca/registrar_libro.html", {"form": LibroForm()})
