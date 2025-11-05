import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../auth/auth.dart';
import 'solicitudes_controller.dart';
import 'package:go_router/go_router.dart';

class SolicitudNewScreen extends ConsumerStatefulWidget {
  const SolicitudNewScreen({super.key});
  @override
  ConsumerState<SolicitudNewScreen> createState() => _SolicitudNewScreenState();
}

class _SolicitudNewScreenState extends ConsumerState<SolicitudNewScreen> {
  final _montoCtrl = TextEditingController();
  final _plazoCtrl = TextEditingController(text: '12');
  final _tasaCtrl = TextEditingController(text: '18');
  String moneda = 'BOB';
  String? error;

  @override
  void dispose() {
    _montoCtrl.dispose();
    _plazoCtrl.dispose();
    _tasaCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final me = ref.read(authProvider).user;
    if (me?['cliente_id'] == null) {
      setState(() => error = 'Tu cuenta no es de tipo Cliente.');
      return;
    }

    final monto = double.tryParse(_montoCtrl.text.replaceAll(',', '.')) ?? -1;
    final plazo = int.tryParse(_plazoCtrl.text) ?? -1;
    final tasa = double.tryParse(_tasaCtrl.text.replaceAll(',', '.')) ?? -1;

    if (monto <= 0) {
      setState(() => error = 'Monto inválido');
      return;
    }
    if (plazo < 1) {
      setState(() => error = 'Plazo inválido');
      return;
    }
    if (tasa <= 0) {
      setState(() => error = 'Tasa inválida');
      return;
    }

    setState(() => error = null);

    try {
      final created = await ref.read(solicitudesProvider.notifier).crear(
            monto: monto,
            plazoMeses: plazo,
            tasaNominalAnual: tasa,
            moneda: moneda,
          );
      if (!mounted) return;
      context.go('/solicitudes/${created!.id}');
    } catch (e) {
      setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = ref.watch(authProvider).user;
    return Scaffold(
      appBar: AppBar(title: const Text('Nueva solicitud')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (me?['cliente_id'] == null)
            const Text('Tu cuenta no está vinculada como Cliente.',
                style: TextStyle(color: Colors.red)),
          TextField(
            controller: _montoCtrl,
            decoration: const InputDecoration(
                labelText: 'Monto solicitado',
                prefixIcon: Icon(Icons.attach_money)),
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: TextField(
                controller: _plazoCtrl,
                decoration: const InputDecoration(
                    labelText: 'Plazo (meses)',
                    prefixIcon: Icon(Icons.calendar_month)),
                keyboardType: TextInputType.number,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _tasaCtrl,
                decoration: const InputDecoration(
                    labelText: 'Tasa nominal anual (%)',
                    prefixIcon: Icon(Icons.percent)),
                keyboardType: TextInputType.number,
              ),
            ),
          ]),
          const SizedBox(height: 12),
          InputDecorator(
            decoration: const InputDecoration(
                labelText: 'Moneda', border: OutlineInputBorder()),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: moneda,
                items: const [
                  DropdownMenuItem(value: 'BOB', child: Text('BOB')),
                  DropdownMenuItem(value: 'USD', child: Text('USD')),
                ],
                onChanged: (v) => setState(() => moneda = v ?? 'BOB'),
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (error != null)
            Text(error!, style: const TextStyle(color: Colors.red)),
          const SizedBox(height: 12),
          FilledButton(
              onPressed: _submit, child: const Text('Enviar solicitud')),
        ],
      ),
    );
  }
}
