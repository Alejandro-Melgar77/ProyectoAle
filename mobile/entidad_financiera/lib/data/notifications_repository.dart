import 'api_client.dart';

class NotificationsRepository {
  final _api = ApiClient.I;

  Future<List<Map<String, dynamic>>> listByCliente(int clienteId) async {
    final resp =
        await _api.get('/notificaciones/', query: {'cliente': '$clienteId'});
    return (resp.data as List).cast<Map<String, dynamic>>();
  }

  Future<void> markRead(String notiId) async {
    await _api.patch('/notificaciones/$notiId/', {'leida': true});
  }
}
