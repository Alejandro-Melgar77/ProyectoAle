import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/profile_repository.dart';
import '../auth/auth.dart';

/// ==== STATE ===============================================================
class ProfileState {
  final bool loading;
  final String? error;

  /// Usuario de /users/me/
  final Map<String, dynamic>? user;

  /// Cliente de /clientes/:id/
  final Map<String, dynamic>? cliente;

  const ProfileState({
    this.loading = false,
    this.error,
    this.user,
    this.cliente,
  });

  ProfileState copyWith({
    bool? loading,
    String? error,
    Map<String, dynamic>? user,
    Map<String, dynamic>? cliente,
  }) {
    return ProfileState(
      loading: loading ?? this.loading,
      error: error,
      user: user ?? this.user,
      cliente: cliente ?? this.cliente,
    );
  }
}

/// ==== CONTROLLER ==========================================================
class ProfileController extends StateNotifier<ProfileState> {
  ProfileController(this._repo, this._ref) : super(const ProfileState());

  final ProfileRepository _repo;
  final Ref _ref;

  Future<void> load() async {
    state = state.copyWith(loading: true, error: null);
    try {
      final me = await _repo.me(); // /users/me/
      Map<String, dynamic>? cliente;
      final cid = me['cliente_id'] as int?;
      if (cid != null) {
        cliente = await _repo.getCliente(cid); // /clientes/:id/
      }
      state = state.copyWith(loading: false, user: me, cliente: cliente);
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  Future<void> saveCliente(Map<String, dynamic> data) async {
    // preferimos el id del estado (si ya se cargó el cliente)
    final cidFromState = state.cliente?['id'] as int?;
    final cidFromAuth = _ref.read(authProvider).user?['cliente_id'] as int?;
    final clienteId = cidFromState ?? cidFromAuth;
    if (clienteId == null) {
      throw Exception('No se encontró cliente_id.');
    }

    state = state.copyWith(loading: true, error: null);
    try {
      await _repo.updateCliente(clienteId: clienteId, data: data);
      await load(); // refrescar todo
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
      rethrow;
    }
  }
}

/// ==== PROVIDERS ===========================================================
final profileRepoProvider = Provider((_) => ProfileRepository());

final profileProvider =
    StateNotifierProvider<ProfileController, ProfileState>((ref) {
  return ProfileController(ref.read(profileRepoProvider), ref);
});
