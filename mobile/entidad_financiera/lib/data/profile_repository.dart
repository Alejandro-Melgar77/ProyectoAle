import 'api_client.dart';

class ProfileRepository {
  final _api = ApiClient.I;

  /// GET /users/me/
  Future<Map<String, dynamic>> me() async {
    final resp = await _api.get('/users/me/');
    return resp.data as Map<String, dynamic>;
  }

  /// GET /clientes/:id/
  Future<Map<String, dynamic>> getCliente(int id) async {
    final resp = await _api.get('/clientes/$id/');
    return resp.data as Map<String, dynamic>;
  }

  /// PATCH /clientes/:id/
  Future<Map<String, dynamic>> updateCliente({
    required int clienteId,
    required Map<String, dynamic> data,
  }) async {
    final resp = await _api.patch('/clientes/$clienteId/', data);
    return resp.data as Map<String, dynamic>;
  }
}
