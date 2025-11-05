// lib/data/auth_repository.dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../data/api_client.dart';

class AuthRepository {
  final Dio _dio = ApiClient.I.dio;
  final _storage = const FlutterSecureStorage();

  static const _kAccess = 'access_token';
  static const _kRefresh = 'refresh_token';

  // ========== AUTH BASICO ==========

  Future<void> login({
    required String username,
    required String password,
  }) async {
    final resp = await _dio.post('/api/auth/login/', data: {
      'username': username,
      'password': password,
    });

    // Log útil
    // ignore: avoid_print
    print('[API] login resp: ${resp.data}');

    final data = resp.data as Map<String, dynamic>;
    final access =
        (data['access'] ?? data['access_token'] ?? data['token']) as String;
    final refresh = (data['refresh'] ?? data['refresh_token'] ?? '') as String?;

    await _storage.write(key: _kAccess, value: access);
    if (refresh != null && refresh.isNotEmpty) {
      await _storage.write(key: _kRefresh, value: refresh);
    }
    _dio.options.headers['Authorization'] = 'Bearer $access';
  }

  Future<void> refresh() async {
    final refresh = await _storage.read(key: _kRefresh);
    if (refresh == null) return;
    final resp = await _dio.post(
      '/api/auth/refresh/',
      data: {'refresh': refresh},
    );
    final access = resp.data['access'] as String;
    await _storage.write(key: _kAccess, value: access);
    _dio.options.headers['Authorization'] = 'Bearer $access';
  }

  Future<void> logout() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
    _dio.options.headers.remove('Authorization');
  }

  Future<bool> loadTokensIfAny() async {
    final access = await _storage.read(key: _kAccess);
    if (access == null) return false;
    _dio.options.headers['Authorization'] = 'Bearer $access';
    return true;
  }

  // ========== PERFIL / ME ==========

  /// Devuelve SIEMPRE un Map para que tu controlador no reviente
  /// aunque /api/users/ sea una lista.
  // lib/data/auth_repository.dart
  // Devuelve SIEMPRE un Map con el usuario autenticado
  Future<Map<String, dynamic>?> me() async {
    final resp = await _dio.get('/api/users/me/');
    // ignore: avoid_print
    print('[API] me() → status:${resp.statusCode} data:${resp.data}');
    final data = resp.data;
    if (data is Map<String, dynamic>) return data; // incluye cliente_id
    return null; // sin fallback a listas
  }

  // ========== REGISTRO PUBLICO (User + Cliente con rol=Cliente) ==========

  /// Endpoint público: POST /api/auth/register/
  /// Crea User + UserProfile(rol=Cliente) + Cliente.
  Future<void> registerPublic({
    // User
    required String username,
    required String email,
    required String password,
    required String password2,
    String? firstName,
    String? lastName,

    // Cliente
    required String tipoDocumento, // 'CI' | 'PAS' | 'NIT'
    required String numeroDocumento,
    required String telefono,
    String? direccion,
    String? fechaNacimiento, // 'YYYY-MM-DD'
    String? ocupacion,
    num? ingresosMensuales,
  }) async {
    final payload = {
      // User
      'username': username,
      'email': email,
      'password': password,
      'password2': password2,
      'first_name': firstName ?? '',
      'last_name': lastName ?? '',
      // Cliente
      'tipo_documento': tipoDocumento,
      'numero_documento': numeroDocumento,
      'telefono': telefono,
      if (direccion != null && direccion.isNotEmpty) 'direccion': direccion,
      if (fechaNacimiento != null && fechaNacimiento.isNotEmpty)
        'fecha_nacimiento': fechaNacimiento,
      if (ocupacion != null && ocupacion.isNotEmpty) 'ocupacion': ocupacion,
      if (ingresosMensuales != null) 'ingresos_mensuales': ingresosMensuales,
    };

    try {
      final resp = await _dio.post('/api/auth/register/', data: payload);
      if (resp.statusCode != 201) {
        throw DioException(
          requestOptions: resp.requestOptions,
          response: resp,
          message: 'Registro falló (${resp.statusCode})',
        );
      }
    } on DioException catch (e) {
      // Intenta surfear mensajes detallados del serializer
      final data = e.response?.data;
      if (data is Map<String, dynamic>) {
        throw Exception(data.toString());
      }
      rethrow;
    }
  }

  /// DEPRECATED: si en tu UI antigua llamas a register(), redirígelo aquí
  @Deprecated('Usa registerPublic(...) con todos los campos requeridos.')
  Future<void> register({
    required String username,
    required String email,
    required String password,
  }) async {
    // Provee defaults mínimos para no romper, pero lo ideal es
    // llamar a registerPublic desde la nueva UI.
    await registerPublic(
      username: username,
      email: email,
      password: password,
      password2: password, // misma pass repetida
      firstName: '',
      lastName: '',
      tipoDocumento: 'CI',
      numeroDocumento: 'AUTO-MOBILE',
      telefono: '-',
    );
  }
}
