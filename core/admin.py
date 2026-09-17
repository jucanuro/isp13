from django import forms
from django.contrib import admin

from .models import (
    ComunicadoModal,
    ContenidoModal,
    DocumentoGestion,
    MenuItem,
    MenuPrincipal,
)
from .widgets import RecorteImagenWidget


class ComunicadoModalForm(forms.ModelForm):
    class Meta:
        model = ComunicadoModal
        fields = "__all__"
        widgets = {
            "imagen": RecorteImagenWidget,
        }


@admin.register(ComunicadoModal)
class ComunicadoModalAdmin(admin.ModelAdmin):
    form = ComunicadoModalForm
    list_display = ("titulo", "activo", "fecha_creacion")
    list_editable = ("activo",)
    list_filter = ("activo",)


@admin.register(DocumentoGestion)
class DocumentoGestionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "slug", "actualizado")


@admin.register(ContenidoModal)
class ContenidoModalAdmin(admin.ModelAdmin):
    list_display = ("slug", "titulo_1", "actualizado")
    fieldsets = (
        (None, {"fields": ("slug",)}),
        ("Primer bloque", {"fields": ("titulo_1", "texto_1")}),
        ("Segundo bloque (opcional)", {"fields": ("titulo_2", "texto_2")}),
        ("Imagen (opcional)", {"fields": ("imagen",)}),
    )


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = (
        "orden",
        "grupo",
        "titulo",
        "subtitulo",
        "icono",
        "tipo_destino",
        "modal_slug",
        "url",
        "destacado",
        "activo",
    )
    ordering = ("orden", "id")


@admin.register(MenuPrincipal)
class MenuPrincipalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "orden", "activo")
    list_editable = ("orden", "activo")
    inlines = [MenuItemInline]
