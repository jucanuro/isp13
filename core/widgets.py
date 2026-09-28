from django.contrib.admin.widgets import AdminFileWidget


class RecorteImagenWidget(AdminFileWidget):
    """
    Input de archivo para el admin que abre un recorte fijo en la proporción
    indicada (2:1 por defecto, estilo editor de imagen de la librería de
    medios de WordPress) apenas se elige un archivo nuevo, antes de subirlo.
    """

    template_name = "admin/core/widgets/recorte_imagen.html"

    # La salida del recorte siempre mide 1600 px de ancho (ver recorte_imagen.js).
    ANCHO_SALIDA = 1600

    def __init__(self, attrs=None, aspecto="2/1"):
        super().__init__(attrs)
        self.aspecto = aspecto

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        ancho, alto = (int(parte) for parte in self.aspecto.split("/"))
        context["widget"].update(
            {
                "aspecto": self.aspecto,
                "etiqueta_aspecto": f"{ancho}:{alto}",
                "ancho_salida": self.ANCHO_SALIDA,
                "alto_salida": round(self.ANCHO_SALIDA * alto / ancho),
            }
        )
        return context

    class Media:
        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.js",
            "core/js/recorte_imagen.js",
        )
