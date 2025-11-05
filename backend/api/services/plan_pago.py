# api/services/plan_pago.py
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Optional, Tuple, List, Dict, Any
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from django.db import transaction

from ..models import PlanPago, PlanCuota, SolicitudCredito

# Precisión alta para cálculos financieros
getcontext().prec = 28
Q2 = Decimal("0.01")


def q2(x) -> Decimal:
    """Redondeo a 2 decimales con HALF_UP."""
    return Decimal(x).quantize(Q2, rounding=ROUND_HALF_UP)


def _calcular_cronograma_frances(
    capital: Decimal,
    plazo_meses: int,
    tna: Decimal,
    primera_cuota_fecha,
    moneda: str = "BOB",
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Calcula el plan (método francés) sin tocar BD.
    Retorna (plan_dto, cuotas_dto).
    """
    P = q2(capital)
    n = int(plazo_meses)
    # tasa mensual
    r = Decimal(tna) / Decimal("1200")

    # PMT:
    if r == 0:
        pmt = q2(P / n)
    else:
        pmt = q2(P * r / (Decimal(1) - (Decimal(1) + r) ** (-n)))

    # Primera fecha de vencimiento
    if primera_cuota_fecha:
        base_date = primera_cuota_fecha
    else:
        base_date = now().date() + relativedelta(months=+1)

    fecha = base_date

    cuotas: List[Dict[str, Any]] = []
    saldo = P
    tot_cap = Decimal("0.00")
    tot_int = Decimal("0.00")
    ajuste_total = Decimal("0.00")

    for k in range(1, n + 1):
        interes = q2(saldo * r) if r != 0 else Decimal("0.00")
        capital_k = q2(pmt - interes) if r != 0 else q2(P / n)
        cuota_k = pmt if r != 0 else q2(capital_k + interes)

        # Ajuste de la última cuota para cerrar el saldo en 0.00
        if k == n:
            capital_k = q2(saldo)
            cuota_k = q2(capital_k + interes)
            # Ajuste informativo de redondeos
            ajuste_total = q2((P + tot_int + interes) - (pmt * (n - 1) + cuota_k))

        saldo = q2(saldo - capital_k)

        cuotas.append({
            "nro_cuota": k,
            "fecha_vencimiento": fecha,
            "capital": capital_k,
            "interes": interes,
            "cuota": cuota_k,
            "saldo": saldo,
            "ajuste_redondeo": Decimal("0.00") if k < n else ajuste_total,
        })

        fecha = fecha + relativedelta(months=+1)
        tot_cap += capital_k
        tot_int += interes

    plan_dto = {
        "metodo": "frances",
        "moneda": moneda,
        "primera_cuota_fecha": cuotas[0]["fecha_vencimiento"] if cuotas else base_date,
        "total_capital": q2(tot_cap),
        "total_interes": q2(tot_int),
        "total_cuotas": q2(tot_cap + tot_int),
        "redondeo_ajuste_total": q2(ajuste_total),
        "cuota" : pmt,
    }
    return plan_dto, cuotas


def generar_plan(
    solicitud: Optional[SolicitudCredito] = None,
    usuario=None,
    *,
    # modo directo (simulador o usos avanzados)
    capital: Optional[Decimal] = None,
    plazo_meses: Optional[int] = None,
    tna: Optional[Decimal] = None,
    moneda: Optional[str] = None,
    primera_cuota_fecha=None,
    # control
    persistir: bool = True,
    overwrite: bool = False,
) -> Any:
    """
    Genera un plan de pagos.

    Modo 1 (por solicitud, persistiendo en BD - DEFAULT):
        generar_plan(solicitud=<obj>, usuario=<user>, persistir=True, overwrite=False)
        -> crea PlanPago/PlanCuota en BD y retorna `plan` (PlanPago)

    Modo 2 (simulación / sin persistir):
        generar_plan(capital=..., plazo_meses=..., tna=..., moneda='BOB', persistir=False, primera_cuota_fecha=...)
        -> NO toca BD y retorna (plan_dto, cuotas_dto)

    Notas:
      - Si persistir=True y ya existe plan y overwrite=False -> ValueError
      - Si persistir=False ignora solicitud/usuario y sólo calcula DTOs
    """

    # --- Resolver parámetros de entrada (desde solicitud o directos)
    if solicitud is not None:
        # Validaciones del flujo normal
        if solicitud.estado != 'APROBADA':
            raise ValueError("La solicitud no está APROBADA.")

        if persistir:
            if overwrite and hasattr(solicitud, "plan"):
                solicitud.plan.delete()
            elif not overwrite and hasattr(solicitud, "plan"):
                raise ValueError("El plan ya existe. Use overwrite=True para regenerar.")
            if usuario is None:
                raise ValueError("Para persistir el plan se requiere 'usuario'.")

        # Datos base desde la solicitud
        P = Decimal(solicitud.monto)
        n = int(solicitud.plazo_meses)
        tasa = Decimal(solicitud.tasa_nominal_anual)
        mon = solicitud.moneda
        # Por defecto, 1 mes después de la aprobación (o hoy si no hay fecha)
        base_date = (solicitud.fecha_aprobacion.date() if solicitud.fecha_aprobacion else now().date()) + relativedelta(months=+1)
        if primera_cuota_fecha:
            base_date = primera_cuota_fecha

    else:
        # Modo directo (simulador u otros)
        if capital is None or plazo_meses is None or tna is None:
            raise ValueError("Para el modo directo se requieren: capital, plazo_meses y tna.")
        P = Decimal(capital)
        n = int(plazo_meses)
        tasa = Decimal(tna)
        mon = moneda or "BOB"
        base_date = primera_cuota_fecha or (now().date() + relativedelta(months=+1))

    # --- Cálculo puro (sin BD)
    plan_dto, cuotas_dto = _calcular_cronograma_frances(
        capital=P,
        plazo_meses=n,
        tna=tasa,
        primera_cuota_fecha=base_date,
        moneda=mon,
    )

    # --- Si NO persistimos, devolvemos DTOs y salimos
    if not persistir:
        return plan_dto, cuotas_dto

    # --- Persistencia en BD (flujo normal)
    with transaction.atomic():
        plan = PlanPago.objects.create(
            solicitud=solicitud,
            metodo=plan_dto["metodo"],
            moneda=plan_dto["moneda"],
            primera_cuota_fecha=plan_dto["primera_cuota_fecha"],
            total_capital=plan_dto["total_capital"],
            total_interes=plan_dto["total_interes"],
            total_cuotas=plan_dto["total_cuotas"],
            redondeo_ajuste_total=plan_dto["redondeo_ajuste_total"],
            generado_por=usuario
        )
        for c in cuotas_dto:
            PlanCuota.objects.create(
                plan=plan,
                nro_cuota=c["nro_cuota"],
                fecha_vencimiento=c["fecha_vencimiento"],
                capital=c["capital"],
                interes=c["interes"],
                cuota=c["cuota"],
                saldo=c["saldo"],
                ajuste_redondeo=c["ajuste_redondeo"],
            )

    # Compatibilidad con el uso previo (retornar plan creado)
    return plan
