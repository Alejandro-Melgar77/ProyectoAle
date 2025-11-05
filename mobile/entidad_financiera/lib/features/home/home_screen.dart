// lib/features/home/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme.dart';
import '../auth/auth_controller.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Crédito'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Hola, ${user?['first_name'] ?? user?['username'] ?? ''}',
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 14),

          // Accesos rápidos
          Row(
            children: [
              _QuickAction(
                icon: Icons.add_circle_outline,
                label: 'Nueva solicitud',
                onTap: () => context.go('/solicitudes/new'),
              ),
              const SizedBox(width: 12),
              _QuickAction(
                icon: Icons.description_outlined,
                label: 'Mis solicitudes',
                onTap: () => context.go('/solicitudes'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _QuickAction(
                icon: Icons.person_outline,
                label: 'Mi perfil',
                onTap: () => context.go('/perfil'), // <- aquí estaba el fallo
              ),
              const SizedBox(width: 12),
              _QuickAction(
                icon: Icons.notifications_outlined,
                label: 'Notificaciones',
                onTap: () => context.go('/notificaciones'),
              ),
            ],
          ),

          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: const [
                BoxShadow(
                    color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))
              ],
            ),
            child: const Text(
              'Puedes crear una solicitud y hacer seguimiento del estado. '
              'Cuando sea APROBADA, verás tu plan de pagos.',
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.icon, required this.label, this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          height: 90,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            boxShadow: const [
              BoxShadow(
                  color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))
            ],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon),
              const SizedBox(height: 6),
              Text(label, style: TextStyle(color: AppColors.muted)),
            ],
          ),
        ),
      ),
    );
  }
}
