from datetime import date, timedelta

def validar_vigencia(fecha_emision, vigencia_dias: int | None) -> tuple[bool, str | None]:
    if not vigencia_dias or not fecha_emision:
        return True, None
    limite = fecha_emision + timedelta(days=vigencia_dias)
    if date.today() <= limite:
        return True, None
    return False, f'Documento vencido (vigencia {vigencia_dias} días; emisión {fecha_emision})'
