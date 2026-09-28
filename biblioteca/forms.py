from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.models import Q

from .models import Categoria, Libro


MAX_PORTADA_BYTES = 5 * 1024 * 1024

CLASES_INPUT = (
    "block w-full min-w-0 rounded-lg border border-crema-300 bg-white px-4 py-3 "
    "text-sm text-slate-800 placeholder:text-slate-400 transition "
    "focus:outline-none focus:border-blue-900 focus:ring-2 focus:ring-blue-900/10"
)


class LibroForm(forms.ModelForm):
    # El modelo guarda el ISBN sin guiones (13 máx.); aquí se acepta escrito con
    # guiones (17 máx.). Libro.clean_fields lo normaliza antes de validarlo.
    isbn = forms.CharField(
        max_length=17,
        required=False,
        label="ISBN",
        help_text="ISBN-10 o ISBN-13, con o sin guiones.",
    )

    class Meta:
        model = Libro
        fields = [
            "titulo",
            "autores",
            "tipo",
            "categoria",
            "descripcion",
            "editorial",
            "anio_publicacion",
            "isbn",
            "portada",
            "ejemplares",
            "ubicacion",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Categorías activas, más la actual del libro aunque se haya desactivado.
        self.fields["categoria"].queryset = Categoria.objects.filter(
            Q(activo=True) | Q(pk=self.instance.categoria_id)
        )
        self.fields["categoria"].empty_label = "Sin categoría"

        self.fields["descripcion"].widget.attrs["rows"] = 4
        self.fields["autores"].widget.attrs["placeholder"] = "Ej. María Salazar; Jorge Quispe"
        self.fields["isbn"].widget.attrs["placeholder"] = "978-612-00-0001-4"
        self.fields["anio_publicacion"].widget.attrs["placeholder"] = "Ej. 2019"
        self.fields["ubicacion"].widget.attrs["placeholder"] = "Ej. 371.3 SAL"
        for nombre, campo in self.fields.items():
            if nombre != "portada":
                campo.widget.attrs["class"] = CLASES_INPUT
                campo.widget.attrs["aria-describedby"] = f"error-{nombre}"

    def clean_portada(self):
        portada = self.cleaned_data.get("portada")
        if portada and getattr(portada, "size", 0) > MAX_PORTADA_BYTES:
            raise forms.ValidationError("La portada no puede superar los 5 MB.")
        return portada

    def _post_clean(self):
        super()._post_clean()
        # El índice único es condicional, así que Django reporta el choque como
        # error general del formulario. Se reasigna al campo para mostrarlo junto
        # al ISBN, no en un aviso suelto.
        mensaje = Libro._meta.constraints[0].violation_error_message
        generales = self._errors.get(NON_FIELD_ERRORS) if self._errors else None
        if not generales:
            return
        restantes = [e for e in generales.as_data() if mensaje not in e.messages]
        if len(restantes) == len(generales):
            return
        if restantes:
            self._errors[NON_FIELD_ERRORS] = self.error_class(restantes, error_class="nonfield")
        else:
            del self._errors[NON_FIELD_ERRORS]
        self.add_error("isbn", mensaje)
