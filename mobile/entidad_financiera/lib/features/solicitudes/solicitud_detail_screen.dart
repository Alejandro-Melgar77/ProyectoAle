// lib/features/solicitudes/solicitud_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'solicitudes_controller.dart';
import '../../data/models/plan.dart';

class SolicitudDetailScreen extends ConsumerStatefulWidget {
  const SolicitudDetailScreen({super.key, required this.id});
  final String id;

  @override
  ConsumerState<SolicitudDetailScreen> createState() =>
      _SolicitudDetailScreenState();
}

class _SolicitudDetailScreenState extends ConsumerState<SolicitudDetailScreen> {
  PlanPago? plan;
  String? error;
  bool loading = false;

  Future<void> _loadPlan() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final p = await ref.read(solicitudesProvider.notifier).plan(widget.id);
      if (!mounted) return;
      setState(() {
        plan = p;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = e.toString();
      });
    } finally {
      if (!mounted) return;
      setState(() {
        loading = false;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    _loadPlan();
  }

  @override
  Widget build(BuildContext context) {
    final st = ref.watch(solicitudesProvider);

    // Buscar la solicitud de forma segura (evitar crash si la lista está vacía)
    final solicitud = _findSolicitudById(st.items, widget.id);

    if (solicitud == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Detalle de solicitud')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text(
              'No se encontró la solicitud.\n'
              'Vuelve a la lista y refresca si acabas de crearla.',
              textAlign: TextAlign.center,
            ),
          ),
        ),
      );
    }

    final chipColor = _statusColor(solicitud.estado);

    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de solicitud')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            elevation: 1,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: CircleAvatar(
                child: Text(
                  solicitud.moneda.isNotEmpty ? solicitud.moneda[0] : '?',
                ),
              ),
              title: Text(
                '${solicitud.moneda} ${solicitud.monto.toStringAsFixed(2)}',
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
              subtitle: Text(
                'TNA ${solicitud.tasaNominalAnual}% • ${solicitud.plazoMeses} meses',
              ),
              trailing: Chip(
                label: Text(
                  solicitud.estado,
                  style: TextStyle(color: chipColor),
                ),
                backgroundColor: chipColor.withOpacity(0.12),
                side: BorderSide(color: chipColor.withOpacity(0.4)),
              ),
            ),
          ),
          const SizedBox(height: 12),
          if (loading) const LinearProgressIndicator(),
          if (error != null) ...[
            const SizedBox(height: 8),
            Text(error!, style: const TextStyle(color: Colors.red)),
          ],
          if (!loading && error == null && plan == null) ...[
            const SizedBox(height: 8),
            const Text(
              'Aún no hay plan generado.\n'
              'Cuando la solicitud sea APROBADA y el oficial genere el plan, aparecerá aquí.',
            ),
          ],
          if (plan != null) ...[
            const SizedBox(height: 12),
            _PlanTable(plan: plan!),
          ],
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loadPlan,
        icon: const Icon(Icons.refresh),
        label: const Text('Actualizar plan'),
      ),
    );
  }

  /// Busca una solicitud por id sin lanzar excepción.
  dynamic _findSolicitudById(List items, String id) {
    for (final e in items) {
      if (e.id == id) return e;
    }
    return null;
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

class _PlanTable extends StatelessWidget {
  const _PlanTable({required this.plan});
  final PlanPago plan;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Método: ${plan.metodo}   Moneda: ${plan.moneda}\n'
          'Primera cuota: ${plan.primeraCuotaFecha}',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columns: const [
              DataColumn(label: Text('#')),
              DataColumn(label: Text('Vencimiento')),
              DataColumn(label: Text('Capital')),
              DataColumn(label: Text('Interés')),
              DataColumn(label: Text('Cuota')),
              DataColumn(label: Text('Saldo')),
            ],
            rows: [
              for (final c in plan.cuotas)
                DataRow(
                  cells: [
                    DataCell(Text(c.nroCuota.toString())),
                    DataCell(Text(c.fechaVencimiento)),
                    DataCell(Text(c.capital.toStringAsFixed(2))),
                    DataCell(Text(c.interes.toStringAsFixed(2))),
                    DataCell(Text(c.cuota.toStringAsFixed(2))),
                    DataCell(Text(c.saldo.toStringAsFixed(2))),
                  ],
                ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Totales — Capital: ${plan.totalCapital.toStringAsFixed(2)}'
          '  • Interés: ${plan.totalInteres.toStringAsFixed(2)}'
          '  • Cuotas: ${plan.totalCuotas.toStringAsFixed(2)}',
        ),
      ],
    );
  }
}
