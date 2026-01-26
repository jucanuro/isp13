from django.db import models
import os

class Convocatoria(models.Model):
    ESTADO_CHOICES = [
        ('REGISTRADO', 'Registrado'),
        ('PUBLICADO', 'Publicado'),
        ('EN_PROCESO', 'En Proceso'),
        ('FINALIZADO', 'Finalizado'),
    ]

    titulo = models.CharField(max_length=255, verbose_name="Título del Proceso")
    descripcion = models.TextField(verbose_name="Descripción General", blank=True,null=True)
    
    info_correo = models.EmailField(verbose_name="Correo para Consultas", blank=True, null=True)
    info_mesa_partes = models.CharField(max_length=500, verbose_name="Link Mesa de Partes / Dirección", blank=True, null=True)
    
    mensaje_evaluacion = models.TextField(
        verbose_name="Mensaje Informativo de Evaluación", 
        help_text="Texto que aparecerá durante el proceso de evaluación de expedientes.",
        blank=True
    )

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='REGISTRADO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Convocatoria"
        verbose_name_plural = "Convocatorias"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

class DocumentoConvocatoria(models.Model):
    FASE_CHOICES = [
        ('BASES', '1. Normatividad y Convocatoria'),
        ('EVALUACION', '2. Evaluación'),
        ('FINAL', '3. Resultados Finales'),
    ]

    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE, related_name='documentos')
    fase = models.CharField(max_length=50, choices=FASE_CHOICES, verbose_name="Etapa del Documento")
    nombre_documento = models.CharField(max_length=255, verbose_name="Etiqueta del Archivo")
    archivo = models.FileField(upload_to='convocatorias/%Y/%m/', verbose_name="Archivo PDF")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_fase_display()} - {self.nombre_documento}"

    @property
    def extension(self):
        return os.path.splitext(self.archivo.name)[1].lower()