import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/solicitudes_repository.dart';
import '../../data/models/solicitud.dart';
import '../../data/models/plan.dart';
import '../auth/auth.dart';

class SolicitudesState {
  final bool loading;
  final List<Solicitud> items;
  final String? error;

  const SolicitudesState(
      {this.loading = false, this.items = const [], this.error});

  SolicitudesState copyWith(
          {bool? loading, List<Solicitud>? items, String? error}) =>
      SolicitudesState(
        loading: loading ?? this.loading,
        items: items ?? this.items,
        error: error,
      );
}

class SolicitudesController extends StateNotifier<SolicitudesState> {
  SolicitudesController(this._repo, this._ref)
      : super(const SolicitudesState());

  final SolicitudesRepository _repo;
  final Ref _ref;

  Future<void> cargar() async {
    final me = _ref.read(authProvider).user;
    final clienteId = me?['cliente_id'] as int?;
    if (clienteId == null) {
      state =
          state.copyWith(error: 'Tu cuenta no está vinculada como Cliente.');
      return;
    }
    state = state.copyWith(loading: true, error: null);
    try {
      final list = await _repo.listarDeCliente(clienteId);
      state = state.copyWith(loading: false, items: list);
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  Future<Solicitud?> crear({
    required double monto,
    required int plazoMeses,
    required double tasaNominalAnual,
    required String moneda,
  }) async {
    final me = _ref.read(authProvider).user;
    final clienteId = me?['cliente_id'] as int?;
    if (clienteId == null) throw Exception('No se encontró cliente_id.');

    final s = await _repo.crear(
      clienteId: clienteId,
      monto: monto,
      plazoMeses: plazoMeses,
      tasaNominalAnual: tasaNominalAnual,
      moneda: moneda,
    );
    // refrescar lista
    await cargar();
    return s;
  }

  Future<PlanPago?> plan(String solicitudId) => _repo.obtenerPlan(solicitudId);
}

final solicitudesRepoProvider = Provider((_) => SolicitudesRepository());

final solicitudesProvider =
    StateNotifierProvider<SolicitudesController, SolicitudesState>((ref) {
  final repo = ref.watch(solicitudesRepoProvider);
  return SolicitudesController(repo, ref);
});
