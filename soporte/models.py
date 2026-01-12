from django.db import models

class SolicitudIdentidad(models.Model):
    TIPO_TRAMITE = [
        ('RECUPERAR_CLAVE', 'Recuperar Clave'),
        ('CREAR_USUARIO', 'Crear Usuario'),
        ('NUEVO_CORREO', 'Nuevo Correo Office 365'),
    ]

    ESTADO_SOLICITUD = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESADO', 'Procesado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_TRAMITE, default='RECUPERAR_CLAVE')
    dni = models.CharField(max_length=12, verbose_name="DNI del Alumno")
    email_contacto = models.EmailField(verbose_name="Email de Contacto")
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADO_SOLICITUD, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True, help_text="Notas del administrador")

    class Meta:
        verbose_name = "Solicitud de Identidad"
        verbose_name_plural = "Solicitudes de Identidad"

    def __str__(self):
        return f"{self.tipo} - {self.nombre_completo} ({self.dni})"