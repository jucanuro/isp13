from django.db import models

class Tesis(models.Model):
    titulo = models.CharField(max_length=500)
    autor = models.CharField(max_length=255)
    asesor = models.CharField(max_length=255)
    resumen = models.TextField()
    archivo_pdf = models.FileField(upload_to='tesis_pdfs/')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('validado', 'Validado'),
        ('enviado', 'Enviado a ALICIA'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return self.titulo