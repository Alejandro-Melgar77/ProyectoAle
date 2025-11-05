import 'package:dio/dio.dart';
import 'api_client.dart';
import 'models/solicitud.dart';
import 'models/plan.dart';

class SolicitudesRepository {
  final Dio _dio = ApiClient.I.dio;

  Future<Solicitud> crear({
    required int clienteId,
    required double monto,
    required int plazoMeses,
    required double tasaNominalAnual,
    required String moneda, // 'BOB' | 'USD'
  }) async {
    final resp = await _dio.post('/api/solicitudes/', data: {
      'cliente': clienteId,
      'monto': monto,
      'plazo_meses': plazoMeses,
      'tasa_nominal_anual': tasaNominalAnual,
      'moneda': moneda,
    });
    return Solicitud.fromJson(resp.data as Map<String, dynamic>);
  }

  /// Lista todas y filtra en cliente_id desde la app (si el backend no filtra).
  // lib/data/solicitudes_repository.dart
  Future<List<Solicitud>> listarDeCliente(int clienteId) async {
    final resp = await _dio.get(
      '/api/solicitudes/',
      queryParameters: {
        'cliente': clienteId,
        // si tu paginador lo soporta, puedes controlar el tamaño:
        'page_size': 100,
      },
    );

    final raw = resp.data;
    // Soportar ambas formas: lista directa o paginada {results: [...]}
    final List listJson = raw is List ? raw : (raw['results'] as List);

    final list = listJson
        .map((e) => Solicitud.fromJson(e as Map<String, dynamic>))
        .toList();

    // (Opcional) doble filtro por seguridad, por si el backend ignoró el query param
    return list.where((s) => s.cliente == clienteId).toList();
  }

  Future<PlanPago?> obtenerPlan(String solicitudId) async {
    try {
      final resp = await _dio.get('/api/solicitudes/$solicitudId/plan-pagos/');
      return PlanPago.fromJson(resp.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null; // aún no generado
      rethrow;
    }
  }
}
