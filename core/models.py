from django.db import models


class ComunicadoModal(models.Model):
    titulo = models.CharField(
        max_length=200,
        default="Comunicado Oficial",
        verbose_name="Título",
    )
    subtitulo = models.CharField(
        max_length=200,
        blank=True,
        default='IESPP "13 de Julio de 1882"',
        verbose_name="Subtítulo",
    )
    imagen = models.ImageField(
        upload_to="comunicados/",
        verbose_name="Imagen",
        help_text="Se muestra en el modal que aparece al entrar a la página de inicio.",
    )
    texto_pie = models.CharField(
        max_length=100,
        blank=True,
        default="Información 2026",
        verbose_name="Texto del pie",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Solo se muestra en el inicio si está activo. Si hay varios activos, se usa el más reciente.",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comunicado del modal de inicio"
        verbose_name_plural = "Comunicados del modal de inicio"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.titulo
