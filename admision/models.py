from django.db import models
from django.utils import timezone


class TipoExamenAdmision(models.Model):
    nombre = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Nombre'
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Tipo de examen de admisión'
        verbose_name_plural = 'Tipos de examen de admisión'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class ResultadoAdmision(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('oculto', 'Oculto'),
    ]

    titulo = models.CharField(
        max_length=255,
        verbose_name='Título'
    )

    tipo_examen = models.ForeignKey(
        TipoExamenAdmision,
        on_delete=models.PROTECT,
        related_name='resultados',
        verbose_name='Tipo de examen'
    )

    fecha_examen = models.DateField(
        verbose_name='Fecha de examen'
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción'
    )

    archivo = models.FileField(
        upload_to='admision/resultados/',
        verbose_name='Archivo de resultados'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        verbose_name='Estado'
    )

    es_destacado = models.BooleanField(
        default=False,
        verbose_name='Destacado'
    )

    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )

    fecha_publicacion = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de publicación'
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Resultado de admisión'
        verbose_name_plural = 'Resultados de admisión'
        ordering = ['orden', '-fecha_examen', '-fecha_publicacion']

    def __str__(self):
        return f'{self.titulo} - {self.tipo_examen.nombre}'