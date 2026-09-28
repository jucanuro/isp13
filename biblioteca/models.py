"""Biblioteca institucional: catálogo físico interno.

Regla de arquitectura: nada de este módulo se expone a ALICIA/RENATI ni al
endpoint /oai/. Las tesis NO se copian aquí: el catálogo las lee en vivo desde
investigacion.Tesis (ver views.py).
"""

import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


ANIO_MINIMO = 1500


def validar_anio_publicacion(valor):
    # Función (no MaxValueValidator) para que el tope siga al año en curso
    # sin generar una migración nueva cada enero.
    anio_actual = timezone.now().year
    if valor is not None and not ANIO_MINIMO <= valor <= anio_actual:
        raise ValidationError(
            f"El año debe estar entre {ANIO_MINIMO} y {anio_actual}."
        )


def normalizar_isbn(valor):
    """Quita guiones y espacios: '978-612-4-12345-6' → '9786124123456'."""
    return re.sub(r"[\s-]", "", valor or "").upper()


def validar_isbn(valor):
    isbn = normalizar_isbn(valor)
    if not isbn:
        return

    if re.fullmatch(r"\d{9}[\dX]", isbn):
        total = sum(
            (10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(isbn)
        )
        valido = total % 11 == 0
    elif re.fullmatch(r"\d{13}", isbn):
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(isbn))
        valido = total % 10 == 0
    else:
        raise ValidationError(
            "El ISBN debe tener 10 o 13 dígitos (se admiten guiones)."
        )

    if not valido:
        raise ValidationError(
            "El ISBN no es válido: el dígito de control no coincide."
        )


class Categoria(models.Model):
    nombre = models.CharField(max_length=120, unique=True, verbose_name="Nombre")
    slug = models.SlugField(
        max_length=140,
        unique=True,
        blank=True,
        help_text="Se genera a partir del nombre si se deja vacío.",
    )
    orden = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)[:140]
        super().save(*args, **kwargs)


class Libro(models.Model):
    TIPOS = [
        ("libro", "Libro"),
        ("revista", "Revista"),
        ("manual", "Manual"),
        ("referencia", "Obra de referencia"),
        ("otro", "Otro"),
    ]

    titulo = models.CharField(max_length=500, verbose_name="Título")
    # Texto libre a propósito: el modelo Autor de investigacion exige un DNI
    # único, y el autor de un libro publicado no tiene uno registrable.
    autores = models.CharField(
        max_length=500,
        verbose_name="Autores",
        help_text="Separe varios autores con punto y coma.",
    )
    tipo = models.CharField(
        max_length=20, choices=TIPOS, default="libro", verbose_name="Tipo"
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    editorial = models.CharField(max_length=255, blank=True, verbose_name="Editorial")
    anio_publicacion = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[validar_anio_publicacion],
        verbose_name="Año de publicación",
    )
    isbn = models.CharField(
        max_length=13,
        blank=True,
        validators=[validar_isbn],
        verbose_name="ISBN",
        help_text="ISBN-10 o ISBN-13. Se guarda sin guiones.",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="libros",
        verbose_name="Categoría",
    )
    portada = models.ImageField(
        upload_to="biblioteca/portadas/",
        blank=True,
        verbose_name="Portada",
    )
    ejemplares = models.PositiveSmallIntegerField(default=1, verbose_name="Ejemplares")
    ubicacion = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ubicación",
        help_text="Signatura topográfica o estante. Ej. «370.1 GAR» o «Estante B-3».",
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ["-fecha_registro"]
        constraints = [
            # Único solo si hay ISBN: varios libros sin ISBN no chocan entre sí.
            models.UniqueConstraint(
                fields=["isbn"],
                condition=~Q(isbn=""),
                name="biblioteca_libro_isbn_unico_si_no_vacio",
                violation_error_message="Ya existe un libro registrado con este ISBN.",
            ),
        ]

    def __str__(self):
        return self.titulo

    def clean_fields(self, exclude=None):
        # Antes de validar el max_length: "978-612-00-0001-4" ocupa 17 con guiones.
        self.isbn = normalizar_isbn(self.isbn)
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        # También aquí, para altas que no pasan por full_clean (seed, shell).
        self.isbn = normalizar_isbn(self.isbn)
        super().save(*args, **kwargs)
