from apps.accounts.models import User
from apps.customers.models import Cliente
from apps.loyalty.models import ProgramaFidelizacion
from apps.loyalty.services import (
    ErrorFidelizacion,
    VisitaMuyPronto,
    canjear_premio,
    registrar_visita,
)

USERNAME_ENCARGADO = "Lucas"   # el usuario con negocio, sin staff
UID = "04A1B2C3D4E5F6"                # el UID de tu chip de prueba

cliente = Cliente.objects.first()
encargado = User.objects.get(username=USERNAME_ENCARGADO)
local_id = cliente.negocio.locales.first().pk
programa = ProgramaFidelizacion.objects.get(negocio=cliente.negocio, activo=True)
minutos_original = programa.minutos_entre_visitas

try:
    print("--- 1. El usuario de soporte no puede canjear")
    soporte = User.objects.filter(is_superuser=True).first()
    try:
        canjear_premio(cliente_id=cliente.pk, local_id=local_id, usuario=soporte)
        print("FALLO: el soporte pudo canjear")
    except ErrorFidelizacion as e:
        print("OK, rechazado:", type(e).__name__, "-", e)

    print("--- 2. Chip desconocido")
    try:
        registrar_visita(tag_uid="UID-QUE-NO-EXISTE", cliente_id=cliente.pk)
        print("FALLO: aceptó un chip inexistente")
    except ErrorFidelizacion as e:
        print("OK, rechazado:", type(e).__name__, "-", e)

    print("--- 3. Tiempo mínimo entre visitas")
    programa.minutos_entre_visitas = 60
    programa.save()
    try:
        registrar_visita(tag_uid=UID, cliente_id=cliente.pk)
        registrar_visita(tag_uid=UID, cliente_id=cliente.pk)
        print("FALLO: la segunda visita no fue rechazada")
    except VisitaMuyPronto as e:
        print("OK, rechazada. Faltan", e.segundos_restantes, "segundos")

    print("--- 4. Completar la meta y canjear")
    programa.minutos_entre_visitas = 0
    programa.save()
    cliente.refresh_from_db()
    faltan = max(programa.visitas_requeridas - cliente.contador_visitas, 0)

    if faltan > 0:
        try:
            canjear_premio(cliente_id=cliente.pk, local_id=local_id, usuario=encargado)
            print("FALLO: canjeó sin tener las visitas")
        except ErrorFidelizacion as e:
            print("OK, canje anticipado rechazado:", e)

    for _ in range(faltan):
        registrar_visita(tag_uid=UID, cliente_id=cliente.pk)

    cliente.refresh_from_db()
    print("Contador:", cliente.contador_visitas, "de", programa.visitas_requeridas)

    canje = canjear_premio(cliente_id=cliente.pk, local_id=local_id, usuario=encargado)
    cliente.refresh_from_db()
    print("Canje creado, id:", canje.pk, "- contador tras canje:", cliente.contador_visitas)

finally:
    # Deja el programa como estaba, pase lo que pase
    programa.minutos_entre_visitas = minutos_original
    programa.save()
    print("Programa restaurado a", minutos_original, "minutos entre visitas")