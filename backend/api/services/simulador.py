# api/services/simulador.py
from inspect import signature
from .plan_pago import generar_plan as _generar_plan


def simular_plan(monto, plazo_meses, tna, primera_cuota_fecha=None):
    """
    Simula un plan de pagos SIN persistir en BD, adaptando los nombres
    de parámetros que espera la función real generar_plan.
    """
    sig = signature(_generar_plan)
    params = sig.parameters

    kwargs = {}

    # ---- capital (alias)
    if 'capital' in params:
        kwargs['capital'] = monto
    elif 'monto' in params:
        kwargs['monto'] = monto
    elif 'principal' in params:
        kwargs['principal'] = monto

    # ---- plazo
    if 'plazo_meses' in params:
        kwargs['plazo_meses'] = plazo_meses
    elif 'plazo' in params:
        kwargs['plazo'] = plazo_meses
    elif 'meses' in params:
        kwargs['meses'] = plazo_meses

    # ---- tasa nominal anual
    if 'tna' in params:
        kwargs['tna'] = tna
    elif 'tasa_nominal_anual' in params:
        kwargs['tasa_nominal_anual'] = tna
    elif 'tasa' in params:
        kwargs['tasa'] = tna

    # ---- primera fecha (opcional)
    if 'primera_cuota_fecha' in params:
        kwargs['primera_cuota_fecha'] = primera_cuota_fecha

    # ---- NO PERSISTIR en simulación
    if 'persistir' in params:
        kwargs['persistir'] = False

    # ---- Si la firma exige solicitud/usuario, pasa None (simulación)
    if 'solicitud' in params:
        kwargs['solicitud'] = None
    if 'usuario' in params:
        kwargs['usuario'] = None

    # Llamada final
    plan, cuotas = _generar_plan(**kwargs)
    return plan, cuotas
