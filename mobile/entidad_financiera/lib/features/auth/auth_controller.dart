// lib/features/auth/auth_controller.dart
import 'package:flutter_riverpod/flutter_riverpod.dart' as rp;
import 'package:state_notifier/state_notifier.dart' as sn;

import '../../data/auth_repository.dart';
import 'auth_state.dart';

/// Notifier basado en state_notifier
class AuthController extends sn.StateNotifier<AuthState> {
  AuthController(this._repo) : super(const AuthState());

  final AuthRepository _repo;

  Future<void> loadSession() async {
    try {
      state = state.copyWith(loading: true);

      final hasTokens = await _repo.loadTokensIfAny();
      if (!hasTokens) {
        state = const AuthState(loading: false, authenticated: false);
        return;
      }

      final me = await _repo.me();
      state = AuthState(loading: false, authenticated: true, user: me);
    } catch (_) {
      state = const AuthState(loading: false, authenticated: false);
    }
  }

  // fragmento relevante del login() en tu AuthController
  Future<bool> login(String username, String password) async {
    try {
      print('[AUTH] Login iniciado...');
      state = state.copyWith(loading: true);

      await _repo.login(username: username, password: password);
      print('[AUTH] Login OK, token guardado.');

      final me = await _repo.me();
      print('[AUTH] me() OK: $me');

      state = AuthState(loading: false, authenticated: true, user: me);
      return true;
    } catch (e, st) {
      print('[AUTH] login error: $e\n$st');
      state = const AuthState(loading: false, authenticated: false);
      return false;
    }
  }

  // lib/features/auth/auth_controller.dart (solo el método register)
  Future<void> register({
    required String username,
    required String email,
    required String password,
    required String password2,
    String? firstName,
    String? lastName,
    required String tipoDocumento,
    required String numeroDocumento,
    required String telefono,
    String? direccion,
    String? fechaNacimiento,
    String? ocupacion,
    num? ingresosMensuales,
  }) async {
    await _repo.registerPublic(
      username: username,
      email: email,
      password: password,
      password2: password2,
      firstName: firstName,
      lastName: lastName,
      tipoDocumento: tipoDocumento,
      numeroDocumento: numeroDocumento,
      telefono: telefono,
      direccion: direccion,
      fechaNacimiento: fechaNacimiento,
      ocupacion: ocupacion,
      ingresosMensuales: ingresosMensuales,
    );
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthState(authenticated: false);
  }
}

/// Provider del repositorio
final authRepositoryProvider = rp.Provider<AuthRepository>((ref) {
  return AuthRepository();
});

/// Provider global del estado + notifier
final authProvider = rp.StateNotifierProvider<AuthController, AuthState>((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return AuthController(repo);
});
