// lib/features/solicitudes/solicitudes_list_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../auth/auth.dart';
import 'solicitudes_controller.dart';

class SolicitudesListScreen extends ConsumerStatefulWidget {
  const SolicitudesListScreen({super.key});

  @override
  ConsumerState<SolicitudesListScreen> createState() =>
      _SolicitudesListScreenState();
}

class _SolicitudesListScreenState extends ConsumerState<SolicitudesListScreen> {
  @override
  void initState() {
    super.initState();
    // Cargar solicitudes al entrar
    Future.microtask(() => ref.read(solicitudesProvider.notifier).cargar());
  }

  Future<void> _onRefresh() async {
    await ref.read(solicitudesProvider.notifier).cargar();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final state = ref.watch(solicitudesProvider);

    final clienteId = auth.user?['cliente_id'] as int?;
    final noCliente = clienteId == null;

    return Scaffold(
      appBar: AppBar(title: const Text('Mis solicitudes')),
      floatingActionButton: noCliente
          ? null
          : FloatingActionButton.extended(
              onPressed: () => context.push('/solicitudes/new'),
              icon: const Icon(Icons.add),
              label: const Text('Nueva'),
            ),
      body: RefreshIndicator(
        onRefresh: _onRefresh,
        child: Builder(
          builder: (_) {
            if (noCliente) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    'Tu cuenta no está vinculada como Cliente.\nNo puedes crear solicitudes.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.red),
                  ),
                ),
              );
            }

            if (state.loading) {
              return const Center(child: CircularProgressIndicator());
            }

            if (state.error != null) {
              return ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  Text(state.error!, style: const TextStyle(color: Colors.red)),
                  const SizedBox(height: 8),
                  FilledButton(
                    onPressed: _onRefresh,
                    child: const Text('Reintentar'),
                  ),
                ],
              );
            }

            if (state.items.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(20),
                children: const [
                  SizedBox(height: 12),
                  Text('Aún no tienes solicitudes.'),
                ],
              );
            }

            return ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: state.items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, i) {
                final s = state.items[i];

                final subtitle =
                    'Plazo: ${s.plazoMeses} meses • Tasa: ${s.tasaNominalAnual}% • ${s.moneda}';
                final chipColor = _statusColor(s.estado);

                return Card(
                  elevation: 1,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text(s.moneda.isNotEmpty ? s.moneda[0] : '?'),
                    ),
                    title: Text(
                      'Monto: ${s.monto.toStringAsFixed(2)} ${s.moneda}',
                    ),
                    subtitle: Text(subtitle),
                    trailing: Chip(
                      label: Text(
                        s.estado,
                        style: TextStyle(color: chipColor),
                      ),
                      backgroundColor: chipColor.withOpacity(0.12),
                      side: BorderSide(color: chipColor.withOpacity(0.4)),
                    ),
                    onTap: () => context.push('/solicitudes/${s.id}'),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }

  Color _statusColor(String estado) {
    switch (estado.toUpperCase()) {
      case 'APROBADA':
        return Colors.green;
      case 'RECHAZADA':
        return Colors.red;
      case 'EVALUADA':
        return Colors.orange;
      default:
        return Colors.blueGrey;
    }
  }
}
