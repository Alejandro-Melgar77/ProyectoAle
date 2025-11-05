// lib/core/router.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart' as rp;
import 'package:go_router/go_router.dart';

import '../features/auth/auth.dart'; // exporta authProvider y AuthState
import '../features/auth/onboarding_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/register_screen.dart';
import '../features/home/home_screen.dart';
import '../features/solicitudes/solicitud_new_screen.dart';
import '../features/solicitudes/solicitudes_list_screen.dart';
import '../features/solicitudes/solicitud_detail_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/notifications/notifications_screen.dart';

class AppRouter {
  /// Acepta WidgetRef (desde un ConsumerWidget/ConsumerState)
  static GoRouter create(rp.WidgetRef ref) {
    return GoRouter(
      initialLocation: '/onboarding',

      // Se vuelve a evaluar el redirect cuando cambia el authProvider
      refreshListenable: GoRouterRefresh(ref),

      redirect: (context, state) {
        final auth = ref.read(authProvider);
        final path = state.fullPath ?? state.uri.toString();
        final inAuth = path == '/login' || path == '/register';

        // No autenticado y fuera de login/register/onboarding -> a login
        if (!auth.authenticated &&
            path != '/login' &&
            path != '/register' &&
            path != '/onboarding') {
          return '/login';
        }

        // Autenticado y dentro de login/register -> a home
        if (auth.authenticated && inAuth) return '/home';

        return null;
      },

      // ⚠️ ¡Sin const! GoRoute no es const porque usa builder (una función).
      routes: [
        GoRoute(
          path: '/onboarding',
          builder: (_, __) => const OnboardingScreen(),
        ),
        GoRoute(
          path: '/login',
          builder: (_, __) => const LoginScreen(),
        ),
        GoRoute(
          path: '/register',
          builder: (_, __) => const RegisterScreen(),
        ),
        GoRoute(
          path: '/home',
          builder: (_, __) => const HomeScreen(),
        ),
        GoRoute(
          path: '/solicitudes',
          builder: (_, __) => const SolicitudesListScreen(),
        ),
        GoRoute(
          path: '/solicitudes/new',
          builder: (_, __) => const SolicitudNewScreen(),
        ),
        GoRoute(
          path: '/solicitudes/:id',
          builder: (ctx, st) =>
              SolicitudDetailScreen(id: st.pathParameters['id']!),
        ),
        GoRoute(path: '/perfil', builder: (_, __) => const ProfileScreen()),
        GoRoute(
            path: '/notificaciones',
            builder: (_, __) => const NotificationsScreen()),
      ],
    );
  }
}

/// Notificador que despierta a GoRouter cuando cambia el provider de auth.
/// Usamos listenManual para obtener una suscripción y cerrarla en dispose.
class GoRouterRefresh extends ChangeNotifier {
  GoRouterRefresh(this.ref) {
    _sub = ref.listenManual<AuthState>(
      authProvider,
      (prev, next) => notifyListeners(),
      fireImmediately: false, // no dispares al crear
    );
  }

  final rp.WidgetRef ref;
  late final rp.ProviderSubscription<AuthState> _sub;

  @override
  void dispose() {
    _sub.close();
    super.dispose();
  }
}
