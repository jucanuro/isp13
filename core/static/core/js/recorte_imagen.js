document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.recorte-imagen-widget').forEach(function (contenedor) {
        const input = contenedor.querySelector('input[type="file"]');
        const modal = contenedor.querySelector('.recorte-modal');
        const img = contenedor.querySelector('.recorte-imagen-preview');
        const btnAplicar = contenedor.querySelector('.recorte-aplicar');
        const btnCancelar = contenedor.querySelector('.recorte-cancelar');

        if (!input || !modal || !img || !btnAplicar || !btnCancelar) {
            return;
        }

        // Única fuente de verdad de la proporción: el atributo data-aspecto
        // del contenedor. El texto del botón y el recorte salen de aquí,
        // así no pueden desincronizarse entre sí.
        const partesAspecto = (contenedor.dataset.aspecto || '16/9')
            .split('/')
            .map(Number);
        const aspectRatio = partesAspecto[0] / partesAspecto[1];
        const etiquetaAspecto = partesAspecto[0] + ':' + partesAspecto[1];

        const ANCHO_SALIDA = 1600;
        const ALTO_SALIDA = Math.round(ANCHO_SALIDA / aspectRatio);

        btnAplicar.textContent = 'Aplicar recorte (' + etiquetaAspecto + ')';

        let cropper = null;
        let nombreArchivoOriginal = 'imagen.jpg';

        function cerrarModal() {
            modal.style.display = 'none';

            if (cropper) {
                cropper.destroy();
                cropper = null;
            }
        }

        input.addEventListener('change', function () {
            const file = input.files && input.files[0];

            if (!file) {
                return;
            }

            nombreArchivoOriginal = file.name;

            const reader = new FileReader();

            reader.onload = function (evento) {
                img.src = evento.target.result;
                modal.style.display = 'flex';

                if (cropper) {
                    cropper.destroy();
                }

                cropper = new Cropper(img, {
                    aspectRatio: aspectRatio,
                    viewMode: 1,
                    autoCropArea: 1,
                    responsive: true,
                    background: false,
                });
            };

            reader.readAsDataURL(file);
        });

        btnCancelar.addEventListener('click', function () {
            cerrarModal();
            input.value = '';
        });

        btnAplicar.addEventListener('click', function () {
            if (!cropper) {
                return;
            }

            cropper.getCroppedCanvas({
                width: ANCHO_SALIDA,
                height: ALTO_SALIDA,
                imageSmoothingQuality: 'high',
            }).toBlob(function (blob) {
                const nombreBase = nombreArchivoOriginal.replace(/\.[^.]+$/, '');
                const nombreRecortado = nombreBase + '-recortado.jpg';
                const archivoRecortado = new File([blob], nombreRecortado, {
                    type: 'image/jpeg',
                });

                const transferencia = new DataTransfer();
                transferencia.items.add(archivoRecortado);
                input.files = transferencia.files;

                cerrarModal();
            }, 'image/jpeg', 0.92);
        });
    });
});
