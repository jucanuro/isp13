from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


class DocumentoGestion(models.Model):
    slug = models.SlugField(
        unique=True,
        verbose_name="Identificador",
        help_text=(
            "Debe coincidir exactamente con el ítem de menú que abre este "
            "documento (ej. 'doc_reglamento', 'doc_pci', 'doc_mapro')."
        ),
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    subtitulo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Subtítulo",
        help_text="Ej. 'Vigencia 2023 - 2028'.",
    )
    archivo = models.FileField(
        upload_to="documentos/",
        validators=[FileExtensionValidator(["pdf"])],
        verbose_name="Archivo PDF",
    )
    actualizado = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        verbose_name = "Documento de gestión (PDF)"
        verbose_name_plural = "Documentos de gestión (PDF)"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo


class ContenidoModal(models.Model):
    slug = models.SlugField(
        unique=True,
        verbose_name="Identificador",
        help_text="Debe coincidir exactamente con el modal (ej. 'mision', 'historia', 'organigrama', 'personal').",
    )
    titulo_1 = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Título del primer bloque",
        help_text="Ej. para 'Misión y Visión', este sería el bloque de Misión.",
    )
    texto_1 = models.TextField(
        blank=True,
        verbose_name="Texto del primer bloque",
        help_text="Admite HTML básico (<strong>, <em>, <p>, <br>). Se muestra tal cual, sin escapar.",
    )
    titulo_2 = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Título del segundo bloque (opcional)",
    )
    texto_2 = models.TextField(
        blank=True,
        verbose_name="Texto del segundo bloque (opcional)",
    )
    imagen = models.ImageField(
        upload_to="modales/",
        blank=True,
        null=True,
        verbose_name="Imagen (opcional)",
    )
    actualizado = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        verbose_name = "Contenido de modal (texto/imagen)"
        verbose_name_plural = "Contenidos de modales (texto/imagen)"
        ordering = ["slug"]

    def __str__(self):
        return self.slug

    def clean(self):
        if not (self.texto_1 or self.texto_2 or self.imagen):
            raise ValidationError(
                "Debe completar al menos el texto del primer bloque o "
                "una imagen — un registro vacío no tiene efecto."
            )


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

    def clean(self):
        if self.tipo == "enlace" and not self.url:
            raise ValidationError(
                {"url": "Un 'Enlace directo' necesita una URL."}
            )


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

    def clean(self):
        if self.tipo_destino == "modal" and not self.modal_slug:
            raise ValidationError(
                {"modal_slug": "Un destino 'Contenido interno (modal)' necesita el slug del modal."}
            )

        if self.tipo_destino == "url" and not self.url:
            raise ValidationError(
                {"url": "Un destino 'Enlace / URL' necesita una URL."}
            )
