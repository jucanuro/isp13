import hashlib
import uuid as uuid_lib

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


MAX_PDF_SIZE = 50 * 1024 * 1024
REPOSITORY_BASE_URL = "https://repositorio.13dejuliode1882sp.edu.pe"

pdf_extension_validator = FileExtensionValidator(
    allowed_extensions=["pdf"]
)


def validate_pdf_file(value):
    if not value:
        return

    if value.size > MAX_PDF_SIZE:
        raise ValidationError(
            "El archivo PDF no puede superar los 50 MB."
        )

    original_position = None

    try:
        if hasattr(value, "tell"):
            original_position = value.tell()

        if hasattr(value, "open"):
            value.open("rb")

        signature = value.read(5)

    except (OSError, ValueError, AttributeError) as error:
        raise ValidationError(
            "No fue posible validar el archivo PDF."
        ) from error

    finally:
        try:
            if original_position is not None:
                value.seek(original_position)
            else:
                value.seek(0)
        except (OSError, ValueError, AttributeError):
            pass

    if signature != b"%PDF-":
        raise ValidationError(
            "El archivo cargado no contiene una estructura PDF válida."
        )


class PalabraClave(models.Model):
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Palabra clave",
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Palabra clave"
        verbose_name_plural = "Palabras clave"
        ordering = ["nombre"]


class Autor(models.Model):
    TIPO_DOCUMENTO = [
        ("DNI", "Documento Nacional de Identidad"),
        ("CE", "Carné de Extranjería"),
        ("PAS", "Pasaporte"),
        ("OTRO", "Otro documento"),
    ]

    nombre_completo = models.CharField(
        max_length=255,
        verbose_name="Nombre completo (dc.creator)",
    )
    nombres = models.CharField(
        max_length=150,
        blank=True,
    )
    apellido_paterno = models.CharField(
        max_length=100,
        blank=True,
    )
    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
    )
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOCUMENTO,
        default="DNI",
    )
    dni = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de documento",
    )
    orcid = models.URLField(
        blank=True,
        null=True,
        help_text="Ejemplo: https://orcid.org/0000-0000-0000-0000",
    )

    def __str__(self):
        return self.nombre_completo

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autores"
        ordering = ["nombre_completo"]


class Asesor(models.Model):
    TIPO_DOCUMENTO = Autor.TIPO_DOCUMENTO

    nombre_completo = models.CharField(
        max_length=255,
        verbose_name="Nombre completo (dc.contributor.advisor)",
    )
    nombres = models.CharField(
        max_length=150,
        blank=True,
    )
    apellido_paterno = models.CharField(
        max_length=100,
        blank=True,
    )
    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
    )
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOCUMENTO,
        default="DNI",
    )
    dni = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Número de documento",
    )
    orcid = models.URLField(
        blank=True,
        null=True,
        help_text="Ejemplo: https://orcid.org/0000-0000-0000-0000",
    )

    def __str__(self):
        return self.nombre_completo

    class Meta:
        verbose_name = "Asesor"
        verbose_name_plural = "Asesores"
        ordering = ["nombre_completo"]


class Jurado(models.Model):
    nombre_completo = models.CharField(
        max_length=255,
        verbose_name="Nombre completo",
    )
    orcid = models.URLField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.nombre_completo

    class Meta:
        verbose_name = "Jurado"
        verbose_name_plural = "Jurados"
        ordering = ["nombre_completo"]


class Tesis(models.Model):
    TIPO_GRADO = [
        (
            "info:eu-repo/semantics/bachelorThesis",
            "Tesis de grado o título profesional",
        ),
        (
            "info:eu-repo/semantics/bachelorDiploma",
            "Trabajo de suficiencia profesional",
        ),
        (
            "info:eu-repo/semantics/masterThesis",
            "Tesis de segunda especialidad o maestría",
        ),
        (
            "info:eu-repo/semantics/doctoralThesis",
            "Tesis doctoral",
        ),
        (
            "info:eu-repo/semantics/article",
            "Artículo",
        ),
        (
            "info:eu-repo/semantics/researchReport",
            "Informe de investigación",
        ),
    ]

    IDIOMAS = [
        ("spa", "Español"),
        ("eng", "Inglés"),
        ("que", "Quechua"),
        ("por", "Portugués"),
    ]

    VERSIONES = [
        (
            "info:eu-repo/semantics/submittedVersion",
            "Versión presentada",
        ),
        (
            "info:eu-repo/semantics/acceptedVersion",
            "Versión aceptada",
        ),
        (
            "info:eu-repo/semantics/publishedVersion",
            "Versión publicada",
        ),
    ]

    ESTADOS = [
        ("pendiente", "Pendiente de validación"),
        ("validado", "Validado por Biblioteca"),
        ("publicado", "Publicado en el repositorio"),
        ("retirado", "Retirado del repositorio"),
    ]

    DERECHOS = [
        (
            "info:eu-repo/semantics/openAccess",
            "Acceso abierto",
        ),
        (
            "info:eu-repo/semantics/embargoedAccess",
            "Acceso embargado",
        ),
        (
            "info:eu-repo/semantics/restrictedAccess",
            "Acceso restringido",
        ),
        (
            "info:eu-repo/semantics/closedAccess",
            "Acceso cerrado",
        ),
    ]

    TIPOS_AUTORIZACION = [
        ("autor", "Autorización del autor"),
        ("cesion", "Cesión de derechos"),
        ("licencia", "Licencia de publicación"),
        ("institucional", "Autorización institucional"),
    ]

    uuid = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        editable=False,
        db_index=True,
    )

    titulo = models.CharField(
        max_length=500,
        verbose_name="Título de la investigación (dc.title)",
    )

    autores = models.ManyToManyField(
        Autor,
        verbose_name="Autores (dc.creator)",
    )

    asesores = models.ManyToManyField(
        Asesor,
        blank=True,
        verbose_name="Asesores (dc.contributor.advisor)",
    )

    jurados = models.ManyToManyField(
        Jurado,
        blank=True,
        verbose_name="Jurados",
    )

    resumen = models.TextField(
        verbose_name="Resumen (dc.description.abstract)",
    )

    palabras_clave = models.ManyToManyField(
        PalabraClave,
        blank=True,
        verbose_name="Palabras clave (dc.subject)",
    )

    tipo_tesis = models.CharField(
        max_length=100,
        choices=TIPO_GRADO,
        default="info:eu-repo/semantics/bachelorThesis",
        verbose_name="Tipo de documento (dc.type)",
    )

    grado_academico = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Grado o título obtenido",
    )

    programa_academico = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Programa académico",
    )

    disciplina_academica = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Disciplina académica",
    )

    ocde_codigo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Ejemplo: 5.03.01",
    )

    ocde_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre del área OCDE",
    )

    institucion_nombre = models.CharField(
        max_length=255,
        default=(
            'INSTITUTO DE EDUCACIÓN SUPERIOR PEDAGÓGICO '
            '"13 DE JULIO DE 1882"'
        ),
        verbose_name="Entidad responsable (dc.publisher)",
    )

    institucion_ruc = models.CharField(
        max_length=11,
        default="20202096582",
    )

    institucion_pais = models.CharField(
        max_length=2,
        default="PE",
    )

    institucion_otorgante = models.CharField(
        max_length=255,
        blank=True,
        default=(
            'INSTITUTO DE EDUCACIÓN SUPERIOR PEDAGÓGICO '
            '"13 DE JULIO DE 1882"'
        ),
    )

    idioma = models.CharField(
        max_length=10,
        choices=IDIOMAS,
        default="spa",
        verbose_name="Idioma",
    )

    pais_publicacion = models.CharField(
        max_length=2,
        default="PE",
        verbose_name="País de publicación",
    )

    version_publicacion = models.CharField(
        max_length=100,
        choices=VERSIONES,
        default="info:eu-repo/semantics/publishedVersion",
        verbose_name="Versión de la publicación",
    )

    archivo_pdf = models.FileField(
        upload_to="tesis_pdfs/",
        validators=[
            pdf_extension_validator,
            validate_pdf_file,
        ],
        verbose_name="Documento PDF de la tesis",
    )

    constancia_originalidad = models.FileField(
        upload_to="constancias/",
        validators=[
            pdf_extension_validator,
            validate_pdf_file,
        ],
        null=True,
        blank=True,
        verbose_name="Constancia de originalidad",
    )

    reporte_turnitin = models.FileField(
        upload_to="turnitin/",
        validators=[
            pdf_extension_validator,
            validate_pdf_file,
        ],
        null=True,
        blank=True,
        verbose_name="Reporte de Turnitin",
    )

    autorizacion_publicacion = models.FileField(
        upload_to="autorizaciones/",
        validators=[
            pdf_extension_validator,
            validate_pdf_file,
        ],
        null=True,
        blank=True,
        verbose_name="Autorización de publicación",
    )

    acepta_publicacion = models.BooleanField(
        default=False,
        verbose_name="Cuenta con autorización de publicación",
    )

    tipo_autorizacion = models.CharField(
        max_length=30,
        choices=TIPOS_AUTORIZACION,
        blank=True,
    )

    fecha_autorizacion = models.DateField(
        null=True,
        blank=True,
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    fecha_publicacion = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de sustentación o emisión del título",
    )

    fecha_disponibilidad = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de disponibilidad pública",
    )

    fecha_embargo_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización del embargo",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pendiente",
        db_index=True,
    )

    derechos_acceso = models.CharField(
        max_length=100,
        default="info:eu-repo/semantics/openAccess",
        choices=DERECHOS,
        verbose_name="Derechos de acceso (dc.rights)",
    )

    licencia_uri = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Licencia de publicación",
        help_text=(
            "Ejemplo: "
            "https://creativecommons.org/licenses/by/4.0/"
        ),
    )

    identificador_persistente = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        unique=True,
        editable=False,
    )

    formato_mime = models.CharField(
        max_length=100,
        default="application/pdf",
        editable=False,
    )

    tamano_archivo = models.BigIntegerField(
        default=0,
        editable=False,
    )

    numero_paginas = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    checksum_sha256 = models.CharField(
        max_length=64,
        blank=True,
        editable=False,
    )

    retirado = models.BooleanField(
        default=False,
        db_index=True,
    )

    fecha_retiro = models.DateTimeField(
        null=True,
        blank=True,
    )

    motivo_retiro = models.TextField(
        blank=True,
    )

    def __str__(self):
        if not self.pk:
            return self.titulo[:80] if self.titulo else "Investigación"

        autor_principal = self.autores.first()

        if autor_principal:
            return f"{autor_principal} - {self.titulo[:50]}"

        return f"S/A - {self.titulo[:50]}"

    @property
    def ocde_uri(self):
        if not self.ocde_codigo:
            return ""

        return (
            "https://purl.org/pe-repo/ocde/ford#"
            f"{self.ocde_codigo.strip()}"
        )

    def calcular_metadatos_archivo(self):
        if not self.archivo_pdf:
            return 0, ""

        try:
            file_size = self.archivo_pdf.size
        except (OSError, ValueError, AttributeError):
            file_size = 0

        checksum = hashlib.sha256()

        try:
            self.archivo_pdf.open("rb")

            for chunk in iter(
                lambda: self.archivo_pdf.read(1024 * 1024),
                b"",
            ):
                checksum.update(chunk)

            self.archivo_pdf.close()

        except (OSError, ValueError, AttributeError):
            return file_size, ""

        return file_size, checksum.hexdigest()

    def clean(self):
        errors = {}

        if (
            self.fecha_publicacion
            and self.fecha_disponibilidad
            and self.fecha_disponibilidad < self.fecha_publicacion
        ):
            errors["fecha_disponibilidad"] = (
                "La fecha de disponibilidad no puede ser anterior "
                "a la fecha de publicación."
            )

        if (
            self.fecha_embargo_fin
            and self.fecha_publicacion
            and self.fecha_embargo_fin < self.fecha_publicacion
        ):
            errors["fecha_embargo_fin"] = (
                "La fecha de fin del embargo no puede ser anterior "
                "a la fecha de publicación."
            )

        if (
            self.estado == "retirado"
            and not self.motivo_retiro
        ):
            errors["motivo_retiro"] = (
                "Debe registrar el motivo de retiro."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid_lib.uuid4()

        if not self.identificador_persistente:
            self.identificador_persistente = (
                f"{REPOSITORY_BASE_URL}/repositorio/tesis/"
                f"{self.uuid}/"
            )

        if self.estado == "retirado" and not self.fecha_retiro:
            self.fecha_retiro = timezone.now()

        if self.estado != "retirado":
            self.retirado = False
            self.fecha_retiro = None

        previous_file_name = None

        if self.pk:
            previous = (
                type(self)
                .objects.filter(pk=self.pk)
                .only("archivo_pdf")
                .first()
            )

            if previous and previous.archivo_pdf:
                previous_file_name = previous.archivo_pdf.name

        current_file_name = (
            self.archivo_pdf.name
            if self.archivo_pdf
            else None
        )

        file_changed = (
            previous_file_name != current_file_name
            or not self.checksum_sha256
            or not self.tamano_archivo
        )

        super().save(*args, **kwargs)

        if file_changed and self.archivo_pdf:
            file_size, checksum = (
                self.calcular_metadatos_archivo()
            )

            updates = {}

            if file_size != self.tamano_archivo:
                updates["tamano_archivo"] = file_size
                self.tamano_archivo = file_size

            if checksum and checksum != self.checksum_sha256:
                updates["checksum_sha256"] = checksum
                self.checksum_sha256 = checksum

            if updates:
                type(self).objects.filter(
                    pk=self.pk
                ).update(**updates)

    class Meta:
        verbose_name = "Investigación"
        verbose_name_plural = "Investigaciones"
        ordering = ["-fecha_registro"]
        indexes = [
            models.Index(
                fields=["estado", "fecha_publicacion"],
                name="tesis_estado_fecha_idx",
            ),
            models.Index(
                fields=["fecha_actualizacion"],
                name="tesis_actualiza_idx",
            ),
        ]