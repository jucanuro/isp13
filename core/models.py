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


class MenuPrincipal(models.Model):
    TIPO_CHOICES = [
        ("enlace", "Enlace directo"),
        ("menu", "Menú desplegable"),
    ]

    titulo = models.CharField(max_length=100, verbose_name="Título")
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default="menu",
        verbose_name="Tipo",
    )
    url = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="URL",
        help_text=(
            "Solo para 'Enlace directo'. Puede ser una ruta interna "
            "(ej. /repositorios/) o una URL externa completa."
        ),
    )
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Menú principal (navbar)"
        verbose_name_plural = "Menú principal (navbar)"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.titulo


class MenuItem(models.Model):
    TIPO_DESTINO_CHOICES = [
        ("modal", "Contenido interno (modal)"),
        ("url", "Enlace / URL"),
    ]

    menu = models.ForeignKey(
        MenuPrincipal,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Menú",
    )
    grupo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Grupo / columna",
        help_text=(
            "Título de la columna dentro del desplegable (opcional). "
            "Los ítems con el mismo texto de grupo quedan agrupados juntos."
        ),
    )
    titulo = models.CharField(max_length=150, verbose_name="Título")
    subtitulo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Subtítulo",
    )
    icono = models.CharField(
        max_length=50,
        default="file-alt",
        verbose_name="Ícono",
        help_text=(
            'Nombre del ícono de Font Awesome, sin el prefijo "fas fa-" '
            '(ej. "crosshairs", "landmark"). Ver iconos en fontawesome.com/icons.'
        ),
    )
    tipo_destino = models.CharField(
        max_length=10,
        choices=TIPO_DESTINO_CHOICES,
        default="modal",
        verbose_name="Tipo de destino",
    )
    modal_slug = models.SlugField(
        max_length=100,
        blank=True,
        verbose_name="Slug del modal",
        help_text="Coincide con el nombre de la plantilla en templates/modals/<slug>.html.",
    )
    url = models.CharField(max_length=300, blank=True, verbose_name="URL")
    destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado",
        help_text="Se muestra como botón grande de llamada a la acción, al final de su grupo.",
    )
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Ítem de menú"
        verbose_name_plural = "Ítems de menú"
        ordering = ["orden", "id"]

    def __str__(self):
        return f"{self.menu.titulo} → {self.titulo}"
