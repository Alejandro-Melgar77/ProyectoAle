import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient I = ApiClient._();

  /// Cambia si tu API usa otro prefijo. Si ya pasas rutas con '/api/...'
  /// no pasa nada; el cliente detecta y NO lo duplica.
  static const String _apiPrefix = '/api';

  final Dio dio = Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        // Emulador Android -> 10.0.2.2; dispositivo físico usa tu IP o adb reverse
        defaultValue: 'http://10.0.2.2:8000',
      ),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 20),
    ),
  );

  final _storage = const FlutterSecureStorage();

  /// Llama esto una sola vez al iniciar la app (ya lo haces en `app.dart`)
  Future<void> init() async {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (opt, handler) async {
          // Bearer
          final access = await _storage.read(key: 'access_token');
          if (access != null && access.isNotEmpty) {
            opt.headers['Authorization'] = 'Bearer $access';
          }

          // Normaliza la ruta para asegurar el prefijo /api
          opt.path = _withApiPrefix(opt.path);

          handler.next(opt);
        },
        onError: (e, handler) async {
          // Si expira el access token, intenta refrescar y reintenta UNA vez
          if (e.response?.statusCode == 401) {
            final ok = await _refresh();
            if (ok) {
              final req = e.requestOptions;
              final access = await _storage.read(key: 'access_token');
              if (access != null) {
                req.headers['Authorization'] = 'Bearer $access';
              }

              // OJO: hay que clonar la request y volver a normalizar path
              final RequestOptions retry = RequestOptions(
                path: _withApiPrefix(req.path),
                method: req.method,
                data: req.data,
                queryParameters: req.queryParameters,
                headers: req.headers,
                baseUrl: req.baseUrl,
                sendTimeout: req.sendTimeout,
                receiveTimeout: req.receiveTimeout,
                extra: req.extra,
                contentType: req.contentType,
                responseType: req.responseType,
                followRedirects: req.followRedirects,
                listFormat: req.listFormat,
                maxRedirects: req.maxRedirects,
                receiveDataWhenStatusError: req.receiveDataWhenStatusError,
                requestEncoder: req.requestEncoder,
                responseDecoder: req.responseDecoder,
                validateStatus: req.validateStatus,
              );

              final resp = await dio.fetch(retry);
              return handler.resolve(resp);
            }
          }

          handler.next(e);
        },
      ),
    );
  }

  /// Guarda tokens (útil en login)
  Future<void> saveTokens(
      {required String access, required String refresh}) async {
    await _storage.write(key: 'access_token', value: access);
    await _storage.write(key: 'refresh_token', value: refresh);
  }

  /// Borra tokens (útil en logout)
  Future<void> clearTokens() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  // ------------------ WRAPPERS DE ALTO NIVEL ------------------

  Future<Response<dynamic>> get(
    String path, {
    Map<String, dynamic>? query,
  }) {
    return dio.get(_withApiPrefix(path), queryParameters: query);
  }

  Future<Response<dynamic>> post(
    String path,
    dynamic data, {
    Map<String, dynamic>? query,
  }) {
    return dio.post(_withApiPrefix(path), data: data, queryParameters: query);
  }

  Future<Response<dynamic>> patch(
    String path,
    dynamic data, {
    Map<String, dynamic>? query,
  }) {
    return dio.patch(_withApiPrefix(path), data: data, queryParameters: query);
  }

  Future<Response<dynamic>> delete(
    String path, {
    Map<String, dynamic>? query,
  }) {
    return dio.delete(_withApiPrefix(path), queryParameters: query);
  }

  // ------------------ REFRESH TOKEN ------------------

  Future<bool> _refresh() async {
    final refresh = await _storage.read(key: 'refresh_token');
    if (refresh == null || refresh.isEmpty) return false;

    try {
      // Ojo: aquí usamos path con prefijo /api
      final res = await dio.post(
        _withApiPrefix('/auth/refresh/'),
        data: {'refresh': refresh},
      );
      final newAccess = res.data['access'] as String?;
      if (newAccess == null || newAccess.isEmpty) return false;

      await _storage.write(key: 'access_token', value: newAccess);
      return true;
    } catch (_) {
      // Si no se puede refrescar, limpiamos y devolvemos false
      await _storage.deleteAll();
      return false;
    }
  }

  // ------------------ HELPERS ------------------

  /// Asegura que todos los paths lleven `/api` al frente,
  /// pero sin duplicar si ya viene con `/api`.
  String _withApiPrefix(String path) {
    // normaliza dobles barras, quita espacios
    final p = path.trim();

    if (p.startsWith('http://') || p.startsWith('https://')) {
      // Es URL absoluta; no tocamos
      return p;
    }
    if (p.startsWith('$_apiPrefix/')) {
      return p; // ya trae /api
    }
    if (p == _apiPrefix) {
      return p; // exactamente "/api"
    }
    if (p.startsWith('/')) {
      return '$_apiPrefix$p';
    }
    return '$_apiPrefix/$p';
  }
}
