import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/notifications_repository.dart';
import '../auth/auth.dart';

class Noti {
  final String id;
  final String titulo;
  final String cuerpo;
  final String tipo; // p.ej. SOLICITUD, PLAN, PAGO
  final bool leida;
  final DateTime creada;
  Noti(this.id, this.titulo, this.cuerpo, this.tipo, this.leida, this.creada);

  factory Noti.fromJson(Map<String, dynamic> j) => Noti(
        j['id'].toString(),
        j['titulo'] ?? '',
        j['cuerpo'] ?? '',
        j['tipo'] ?? '',
        (j['leida'] ?? false) as bool,
        DateTime.tryParse(j['created_at'] ?? '') ?? DateTime.now(),
      );
}

class NotificationsState {
  final bool loading;
  final List<Noti> items;
  final String? error;
  const NotificationsState(
      {this.loading = false, this.items = const [], this.error});
  NotificationsState copyWith(
          {bool? loading, List<Noti>? items, String? error}) =>
      NotificationsState(
          loading: loading ?? this.loading,
          items: items ?? this.items,
          error: error);
}

class NotificationsController extends StateNotifier<NotificationsState> {
  NotificationsController(this._repo, this._ref)
      : super(const NotificationsState());
  final NotificationsRepository _repo;
  final Ref _ref;

  Future<void> load() async {
    final cid = _ref.read(authProvider).user?['cliente_id'] as int?;
    if (cid == null) {
      state = state.copyWith(error: 'Tu cuenta no es de tipo Cliente.');
      return;
    }
    state = state.copyWith(loading: true, error: null);
    try {
      final list = await _repo.listByCliente(cid);
      state = state.copyWith(
        loading: false,
        items: list.map(Noti.fromJson).toList(),
      );
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  Future<void> markRead(String id) async {
    await _repo.markRead(id);
    await load();
  }
}

final notificationsRepoProvider = Provider((_) => NotificationsRepository());
final notificationsProvider =
    StateNotifierProvider<NotificationsController, NotificationsState>((ref) {
  return NotificationsController(ref.read(notificationsRepoProvider), ref);
});
