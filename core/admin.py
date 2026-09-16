from django import forms
from django.contrib import admin

from .models import ComunicadoModal
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
