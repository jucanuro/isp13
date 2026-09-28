from django.contrib import admin

from .forms import LibroForm
from .models import Categoria, Libro


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "orden", "activo")
    list_editable = ("orden", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    form = LibroForm  # acepta el ISBN con guiones, igual que el formulario público
    list_display = (
        "titulo",
        "autores",
        "tipo",
        "categoria",
        "anio_publicacion",
        "isbn",
        "ejemplares",
        "ubicacion",
        "activo",
    )
    list_display_links = ("titulo",)
    list_editable = ("activo",)
    list_filter = ("tipo", "categoria", "activo")
    search_fields = ("titulo", "autores", "isbn")
    list_select_related = ("categoria",)
    readonly_fields = ("fecha_registro", "fecha_actualizacion")
    fieldsets = (
        (None, {"fields": ("titulo", "autores", "tipo", "categoria", "descripcion")}),
        ("Publicación", {"fields": ("editorial", "anio_publicacion", "isbn", "portada")}),
        ("Ejemplares físicos", {"fields": ("ejemplares", "ubicacion", "activo")}),
        ("Registro", {"fields": ("fecha_registro", "fecha_actualizacion")}),
    )
