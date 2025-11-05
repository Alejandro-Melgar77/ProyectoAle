// lib/data/models/solicitud.dart
class Solicitud {
  final String id;
  final int cliente;
  final double monto;
  final int plazoMeses;
  final double tasaNominalAnual;
  final String moneda;
  final String estado;

  Solicitud({
    required this.id,
    required this.cliente,
    required this.monto,
    required this.plazoMeses,
    required this.tasaNominalAnual,
    required this.moneda,
    required this.estado,
  });

  // Helpers seguros para DRF (Decimal = string)
  static double _toDouble(dynamic v) {
    if (v == null) return 0;
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v) ?? 0;
    return 0;
  }

  static int _toInt(dynamic v) {
    if (v == null) return 0;
    if (v is int) return v;
    if (v is String) return int.tryParse(v) ?? 0;
    if (v is num) return v.toInt();
    return 0;
  }

  factory Solicitud.fromJson(Map<String, dynamic> json) {
    return Solicitud(
      id: json['id'].toString(),
      cliente: _toInt(json['cliente']),
      monto: _toDouble(json['monto']),
      plazoMeses: _toInt(json['plazo_meses']),
      tasaNominalAnual: _toDouble(json['tasa_nominal_anual']),
      moneda: (json['moneda'] ?? '').toString(),
      estado: (json['estado'] ?? '').toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'cliente': cliente,
        'monto': monto,
        'plazo_meses': plazoMeses,
        'tasa_nominal_anual': tasaNominalAnual,
        'moneda': moneda,
        'estado': estado,
      };
}
