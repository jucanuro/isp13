from django.db import models
from django.db import models

class Tesis(models.Model):
    # --- METADATOS PRINCIPALES (Obligatorios Guía ALICIA) ---
    titulo = models.CharField(max_length=500, verbose_name="Título de la Investigación (dc.title)")
    autor = models.CharField(max_length=255, verbose_name="Autor (dc.creator)")
    autor_dni = models.CharField(max_length=15, help_text="Requerido para RENATI / SUNEDU")
    autor_orcid = models.URLField(blank=True, null=True, help_text="Opcional: ID de investigador")
    
    asesor = models.CharField(max_length=255, verbose_name="Asesor (dc.contributor.advisor)")
    resumen = models.TextField(verbose_name="Resumen (dc.description.abstract)")
    

    TIPO_GRADO = [
        ('info:eu-repo/semantics/bachelorThesis', 'Tesis de Grado de Bachiller'),
        ('info:eu-repo/semantics/bachelorThesis_TITULO', 'Tesis para Título Profesional'),
        ('info:eu-repo/semantics/bachelorDiploma', 'Trabajo de Suficiencia Profesional (Bachiller)'),
        ('info:eu-repo/semantics/masterThesis', 'Tesis de Segunda Especialidad Profesional'),
        ('info:eu-repo/semantics/article', 'Informe de Práctica Pre-Profesional'),
    ]
    tipo_tesis = models.CharField(
        max_length=100, 
        choices=TIPO_GRADO, 
        default='info:eu-repo/semantics/bachelorThesis',
        verbose_name="Tipo de Documento (dc.type)"
    )
    
    # --- TAXONOMÍA OCDE (Seguridad de Nulos para evitar IntegrityError) ---
    ocde_codigo = models.CharField(max_length=20, blank=True, null=True, help_text="Ej: 5.03.01")
    ocde_nombre = models.CharField(max_length=200, blank=True, null=True, help_text="Nombre del área OCDE")

    # --- DATOS OFICIALES DEL INSTITUTO (Fijos para Interoperabilidad) ---
    institucion_nombre = models.CharField(
        max_length=255, 
        default='INSTITUTO DE EDUCACIÓN SUPERIOR PEDAGÓGICO "13 DE JULIO DE 1882"',
        verbose_name="Entidad (dc.publisher)"
    )
    institucion_ruc = models.CharField(max_length=11, default='20202096582')
    institucion_pais = models.CharField(max_length=2, default='PE')
    
    # --- GESTIÓN DE ARCHIVOS Y FECHAS ---
    archivo_pdf = models.FileField(upload_to='tesis_pdfs/', verbose_name="Documento PDF")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_publicacion = models.DateField(null=True, blank=True, help_text="Fecha de sustentación o emisión del título")
    
    # --- ESTADOS DE FLUJO ---
    ESTADOS = [
        ('pendiente', 'Pendiente de Validación'),
        ('validado', 'Validado por Biblioteca'),
        ('publicado', 'Publicado en Repositorio OAI'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    # --- DERECHOS DE ACCESO (Obligatorio ALICIA) ---
    derechos_acceso = models.CharField(
        max_length=100, 
        default='info:eu-repo/semantics/openAccess',
        choices=[
            ('info:eu-repo/semantics/openAccess', 'Acceso Abierto'),
            ('info:eu-repo/semantics/closedAccess', 'Acceso Cerrado'),
            ('info:eu-repo/semantics/restrictedAccess', 'Acceso Restringido'),
        ],
        verbose_name="Derechos (dc.rights)"
    )

    def __str__(self):
        return f"{self.autor} - {self.titulo[:50]}"

    class Meta:
        verbose_name = "Investigación"
        verbose_name_plural = "Investigaciones"
        ordering = ['-fecha_registro']