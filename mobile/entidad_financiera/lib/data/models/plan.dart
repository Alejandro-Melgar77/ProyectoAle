// lib/data/models/plan.dart
class PlanPago {
  final String id;
  final String solicitudId;
  final String metodo;
  final String moneda;
  final String primeraCuotaFecha;
  final double totalCapital;
  final double totalInteres;
  final double totalCuotas;
  final double redondeoAjusteTotal;
  final List<PlanCuota> cuotas;

  PlanPago({
    required this.id,
    required this.solicitudId,
    required this.metodo,
    required this.moneda,
    required this.primeraCuotaFecha,
    required this.totalCapital,
    required this.totalInteres,
    required this.totalCuotas,
    required this.redondeoAjusteTotal,
    required this.cuotas,
  });

  static double _d(dynamic v) {
    if (v == null) return 0;
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0;
    return 0;
  }

  factory PlanPago.fromJson(Map<String, dynamic> j) => PlanPago(
        id: j['id'].toString(),
        solicitudId: j['solicitud_id'].toString(),
        metodo: (j['metodo'] ?? '').toString(),
        moneda: (j['moneda'] ?? '').toString(),
        primeraCuotaFecha: (j['primera_cuota_fecha'] ?? '').toString(),
        totalCapital: _d(j['total_capital']),
        totalInteres: _d(j['total_interes']),
        totalCuotas: _d(j['total_cuotas']),
        redondeoAjusteTotal: _d(j['redondeo_ajuste_total']),
        cuotas: (j['cuotas'] as List<dynamic>? ?? [])
            .map((e) => PlanCuota.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class PlanCuota {
  final int nroCuota;
  final String fechaVencimiento;
  final double capital;
  final double interes;
  final double cuota;
  final double saldo;
  final double ajusteRedondeo;

  PlanCuota({
    required this.nroCuota,
    required this.fechaVencimiento,
    required this.capital,
    required this.interes,
    required this.cuota,
    required this.saldo,
    required this.ajusteRedondeo,
  });

  static double _d(dynamic v) {
    if (v == null) return 0;
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0;
    return 0;
  }

  static int _i(dynamic v) {
    if (v == null) return 0;
    if (v is int) return v;
    if (v is String) return int.tryParse(v) ?? 0;
    if (v is num) return v.toInt();
    return 0;
  }

  factory PlanCuota.fromJson(Map<String, dynamic> j) => PlanCuota(
        nroCuota: _i(j['nro_cuota']),
        fechaVencimiento: (j['fecha_vencimiento'] ?? '').toString(),
        capital: _d(j['capital']),
        interes: _d(j['interes']),
        cuota: _d(j['cuota']),
        saldo: _d(j['saldo']),
        ajusteRedondeo: _d(j['ajuste_redondeo']),
      );
}
