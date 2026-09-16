from django.contrib.admin.widgets import AdminFileWidget


class RecorteImagenWidget(AdminFileWidget):
    """
    Input de archivo para el admin que abre un recorte fijo en 2:1
    (estilo editor de imagen de la librería de medios de WordPress)
    apenas se elige un archivo nuevo, antes de subirlo.
    """

    template_name = "admin/core/widgets/recorte_imagen.html"

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
