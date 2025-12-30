from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    # CORRECCIÓN AQUÍ: de on_on_delete a on_delete
    autor = models.ForeignKey(User, on_delete=models.CASCADE) 
    publicado = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo