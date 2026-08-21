import uuid
from django.db import models


class TipoFuente(models.TextChoices):
    TESIS_INTERNA = "tesis_interna", "Tesis Interna (ISP13)"
    OAI_PMH = "oai_pmh", "Repositorio Externo (OAI-PMH)"
    WEB = "web", "Búsqueda Web"


class EstadoAnalisis(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    PROCESANDO = "procesando", "En Procesamiento"
    COMPLETADO = "completado", "Completado"
    ERROR = "error", "Error"


class NivelRiesgo(models.TextChoices):
    BAJO = "bajo", "Bajo (< 15%)"
    MODERADO = "moderado", "Moderado (15% - 29%)"
    ALTO = "alto", "Alto (>= 30%)"


class DocumentFingerprint(models.Model):
    """
    Índice invertido de huellas digitales de documentos (Winnowing algorithm).
    Permite búsquedas WHERE hash IN (...) para shortlist rápido.
    """
    hash_value = models.BigIntegerField(
        db_index=True,
        help_text="Hash BLAKE2b de 64 bits del shingle"
    )
    tipo_fuente = models.CharField(
        max_length=20,
        choices=TipoFuente.choices,
        db_index=True
    )
    id_fuente = models.CharField(
        max_length=100,
        db_index=True,
        help_text="ID primario de la tesis interna o URI de la fuente externa"
    )
    posicion_shingle = models.IntegerField(
        help_text="Posición del shingle dentro del texto original"
    )

    class Meta:
        verbose_name = "Huella Digital de Documento"
        verbose_name_plural = "Huellas Digitales de Documentos"
        indexes = [
            models.Index(fields=["hash_value", "tipo_fuente"]),
            models.Index(fields=["tipo_fuente", "id_fuente"]),
        ]


class AnalisisOriginalidad(models.Model):
    """
    Registro principal de cada ejecución de análisis sobre una tesis o documento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identificación genérica del documento analizado
    id_fuente = models.CharField(
        max_length=100,
        db_index=True,
        help_text="ID de la Tesis o documento analizado"
    )
    titulo_documento = models.CharField(max_length=500, blank=True, default="")
    texto_extraido = models.TextField(blank=True, default="")
    total_palabras = models.IntegerField(default=0)
    
    # Resultados de Similitud
    porcentaje_similitud = models.FloatField(default=0.0)
    nivel_similitud = models.CharField(
        max_length=10,
        choices=NivelRiesgo.choices,
        default=NivelRiesgo.BAJO
    )
    
    # Resultados de IA
    score_ia = models.FloatField(default=0.0)
    nivel_ia = models.CharField(
        max_length=10,
        choices=NivelRiesgo.choices,
        default=NivelRiesgo.BAJO
    )
    perplejidad_promedio = models.FloatField(null=True, blank=True)
    burstiness_score = models.FloatField(null=True, blank=True)
    
    # Configuración aplicada
    excluir_citas = models.BooleanField(default=True)
    min_palabras_coincidencia = models.IntegerField(default=15)
    
    # Control de Estado
    estado = models.CharField(
        max_length=20,
        choices=EstadoAnalisis.choices,
        default=EstadoAnalisis.PENDIENTE
    )
    mensaje_error = models.TextField(blank=True, default="")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Análisis de Originalidad"
        verbose_name_plural = "Análisis de Originalidad"
        ordering = ["-fecha_creacion"]


class CoincidenciaSimilitud(models.Model):
    """
    Fragmentos coincidentes detectados en un análisis contra una fuente candidata.
    """
    analisis = models.ForeignKey(
        AnalisisOriginalidad,
        on_delete=models.CASCADE,
        related_name="coincidencias"
    )
    tipo_fuente_coincidente = models.CharField(
        max_length=20,
        choices=TipoFuente.choices
    )
    id_fuente_coincidente = models.CharField(max_length=255)
    titulo_fuente = models.CharField(max_length=500, blank=True, default="")
    url_fuente = models.URLField(max_length=1000, blank=True, default="")
    
    # Posiciones en el texto analizado para resaltado
    inicio_texto = models.IntegerField()
    fin_texto = models.IntegerField()
    texto_coincidente = models.TextField()
    
    porcentaje_coincidencia_especifica = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "Coincidencia de Similitud"
        verbose_name_plural = "Coincidencias de Similitud"
        ordering = ["inicio_texto"]


class ExclusionConfig(models.Model):
    """
    Configuración global de reglas de exclusión para los análisis.
    """
    excluir_citas_textuales = models.BooleanField(
        default=True,
        help_text="Excluir texto entre comillas dobles o latinas"
    )
    min_palabras_coincidencia = models.IntegerField(
        default=15,
        help_text="Ignorar bloques coincidentes de menos de N palabras"
    )
    excluir_bibliografia = models.BooleanField(
        default=False,
        help_text="Intentar detectar y omitir la sección de Referencias/Bibliografía"
    )

    class Meta:
        verbose_name = "Configuración de Exclusión"
        verbose_name_plural = "Configuraciones de Exclusión"