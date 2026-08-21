from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DocumentFingerprint,
    AnalisisOriginalidad,
    CoincidenciaSimilitud,
    ExclusionConfig,
)


@admin.register(DocumentFingerprint)
class DocumentFingerprintAdmin(admin.ModelAdmin):
    list_display = ("hash_value", "tipo_fuente", "id_fuente", "posicion_shingle")
    list_filter = ("tipo_fuente",)
    search_fields = ("id_fuente", "hash_value")
    readonly_fields = ("hash_value", "tipo_fuente", "id_fuente", "posicion_shingle")

    def has_add_permission(self, request):
        # Las huellas se generan programáticamente vía algoritmo Winnowing
        return False


class CoincidenciaSimilitudInline(admin.TabularInline):
    model = CoincidenciaSimilitud
    extra = 0
    readonly_fields = (
        "tipo_fuente_coincidente",
        "id_fuente_coincidente",
        "titulo_fuente",
        "url_fuente",
        "inicio_texto",
        "fin_texto",
        "porcentaje_coincidencia_especifica",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AnalisisOriginalidad)
class AnalisisOriginalidadAdmin(admin.ModelAdmin):
    list_display = (
        "id_fuente",
        "titulo_documento",
        "similitud_badge",
        "ia_badge",
        "total_palabras",
        "estado",
        "fecha_creacion",
    )
    list_filter = ("estado", "nivel_similitud", "nivel_ia", "fecha_creacion")
    search_fields = ("id_fuente", "titulo_documento")
    readonly_fields = (
        "id",
        "id_fuente",
        "titulo_documento",
        "texto_extraido",
        "total_palabras",
        "porcentaje_similitud",
        "nivel_similitud",
        "score_ia",
        "nivel_ia",
        "perplejidad_promedio",
        "burstiness_score",
        "fecha_creacion",
        "fecha_finalizacion",
    )
    inlines = [CoincidenciaSimilitudInline]

    @admin.display(description="Similitud (%)")
    def similitud_badge(self, obj):
        color = "#10B981"  # Verde (Bajo)
        if obj.nivel_similitud == "moderado":
            color = "#F59E0B"  # Ámbar
        elif obj.nivel_similitud == "alto":
            color = "#EF4444"  # Rojo

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.porcentaje_similitud,
        )

    @admin.display(description="Prob. IA (%)")
    def ia_badge(self, obj):
        color = "#10B981"  # Verde (Bajo)
        if obj.nivel_ia == "moderado":
            color = "#F59E0B"  # Ámbar
        elif obj.nivel_ia == "alto":
            color = "#EF4444"  # Rojo

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.score_ia,
        )


@admin.register(ExclusionConfig)
class ExclusionConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "excluir_citas_textuales",
        "min_palabras_coincidencia",
        "excluir_bibliografia",
    )

    def has_add_permission(self, request):
        # Limitar a un único registro de configuración global
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)