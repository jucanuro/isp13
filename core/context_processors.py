from django.db.models import Prefetch

from .models import MenuItem, MenuPrincipal


def navbar(request):
    """
    Arma la estructura del navbar principal para las plantillas:
    cada menú con sus ítems agrupados por 'grupo' (columna del desplegable),
    preservando el orden de aparición.
    """
    menus = MenuPrincipal.objects.filter(activo=True).prefetch_related(
        Prefetch(
            "items",
            queryset=MenuItem.objects.filter(activo=True).order_by("orden", "id"),
        )
    )

    navbar_menus = []
    ya_hubo_desplegable = False

    for menu in menus:
        grupos = []
        indice_grupos = {}

        for item in menu.items.all():
            clave = item.grupo or ""

            if clave not in indice_grupos:
                indice_grupos[clave] = {"nombre": item.grupo, "items": []}
                grupos.append(indice_grupos[clave])

            indice_grupos[clave]["items"].append(item)

        alineacion = ""

        if menu.tipo == "menu":
            alineacion = "left" if not ya_hubo_desplegable else "right"
            ya_hubo_desplegable = True

        navbar_menus.append(
            {"menu": menu, "grupos": grupos, "alineacion": alineacion}
        )

    return {"navbar_menus": navbar_menus}
