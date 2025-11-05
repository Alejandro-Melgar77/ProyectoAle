// lib/features/auth/register_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/widgets/app_button.dart';
import '../../core/widgets/app_text_field.dart';
import '../../utils/validators.dart';
import 'auth_controller.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final usernameCtrl = TextEditingController();
  final emailCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  final pass2Ctrl = TextEditingController();

  final firstCtrl = TextEditingController();
  final lastCtrl = TextEditingController();
  final nroDocCtrl = TextEditingController();
  final telCtrl = TextEditingController();
  final dirCtrl = TextEditingController();
  final ocupCtrl = TextEditingController();
  final ingresosCtrl = TextEditingController();
  final fechaNacCtrl = TextEditingController(); // YYYY-MM-DD

  String tipoDoc = 'CI';
  String? error;
  bool _hide = true;

  @override
  void dispose() {
    usernameCtrl.dispose();
    emailCtrl.dispose();
    passCtrl.dispose();
    pass2Ctrl.dispose();
    firstCtrl.dispose();
    lastCtrl.dispose();
    nroDocCtrl.dispose();
    telCtrl.dispose();
    dirCtrl.dispose();
    ocupCtrl.dispose();
    ingresosCtrl.dispose();
    fechaNacCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = usernameCtrl.text.trim();
    final email = emailCtrl.text.trim();
    final pass = passCtrl.text;
    final pass2 = pass2Ctrl.text;
    final numeroDoc = nroDocCtrl.text.trim();
    final telefono = telCtrl.text.trim();

    if (!Validators.isUsername(username)) {
      setState(() => error = 'Usuario inválido');
      return;
    }
    if (!Validators.isEmail(email)) {
      setState(() => error = 'Email inválido');
      return;
    }
    if (pass.length < 6) {
      setState(() => error = 'Contraseña muy corta (mín. 6)');
      return;
    }
    if (pass != pass2) {
      setState(() => error = 'Las contraseñas no coinciden');
      return;
    }
    if (numeroDoc.isEmpty) {
      setState(() => error = 'Ingrese número de documento');
      return;
    }
    if (telefono.isEmpty) {
      setState(() => error = 'Ingrese teléfono');
      return;
    }

    setState(() => error = null);

    try {
      await ref.read(authProvider.notifier).register(
            username: username,
            email: email,
            password: pass,
            password2: pass2,
            firstName:
                firstCtrl.text.trim().isEmpty ? null : firstCtrl.text.trim(),
            lastName:
                lastCtrl.text.trim().isEmpty ? null : lastCtrl.text.trim(),
            tipoDocumento: tipoDoc, // requerido
            numeroDocumento: numeroDoc, // requerido
            telefono: telefono, // requerido
            direccion: dirCtrl.text.trim().isEmpty ? null : dirCtrl.text.trim(),
            fechaNacimiento: fechaNacCtrl.text.trim().isEmpty
                ? null
                : fechaNacCtrl.text.trim(), // YYYY-MM-DD
            ocupacion:
                ocupCtrl.text.trim().isEmpty ? null : ocupCtrl.text.trim(),
            ingresosMensuales: ingresosCtrl.text.trim().isEmpty
                ? null
                : num.tryParse(ingresosCtrl.text.trim()),
          );

      if (!mounted) return;
      // Tras registrarse, lo mando a login
      context.go('/login');
    } catch (e) {
      setState(() => error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar:
          AppBar(leading: BackButton(onPressed: () => context.go('/login'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('Crear cuenta',
                      style:
                          TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 18),

                  // ——— Cuenta
                  AppTextField(
                      hint: 'Usuario',
                      controller: usernameCtrl,
                      prefixIcon: Icons.person_outline),
                  const SizedBox(height: 12),
                  AppTextField(
                      hint: 'Correo electrónico',
                      controller: emailCtrl,
                      prefixIcon: Icons.email_outlined,
                      keyboardType: TextInputType.emailAddress),
                  const SizedBox(height: 12),

                  Row(children: [
                    Expanded(
                        child: AppTextField(
                            hint: 'Contraseña',
                            controller: passCtrl,
                            obscure: _hide,
                            prefixIcon: Icons.lock_outline)),
                    const SizedBox(width: 12),
                    Expanded(
                        child: AppTextField(
                            hint: 'Repite contraseña',
                            controller: pass2Ctrl,
                            obscure: _hide,
                            prefixIcon: Icons.lock_outline)),
                    IconButton(
                      icon:
                          Icon(_hide ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setState(() => _hide = !_hide),
                    )
                  ]),
                  const SizedBox(height: 16),

                  // ——— Datos personales (opcionales)
                  Row(children: [
                    Expanded(
                        child: AppTextField(
                            hint: 'Nombres (opcional)',
                            controller: firstCtrl,
                            prefixIcon: Icons.badge_outlined)),
                    const SizedBox(width: 12),
                    Expanded(
                        child: AppTextField(
                            hint: 'Apellidos (opcional)',
                            controller: lastCtrl,
                            prefixIcon: Icons.badge_outlined)),
                  ]),
                  const SizedBox(height: 12),

                  // ——— Cliente (requeridos)
                  Row(children: [
                    Expanded(
                      child: InputDecorator(
                        decoration: const InputDecoration(
                            prefixIcon: Icon(Icons.credit_card),
                            border: OutlineInputBorder(),
                            labelText: 'Tipo doc.'),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: tipoDoc,
                            items: const [
                              DropdownMenuItem(value: 'CI', child: Text('CI')),
                              DropdownMenuItem(
                                  value: 'PAS', child: Text('PAS')),
                              DropdownMenuItem(
                                  value: 'NIT', child: Text('NIT')),
                            ],
                            onChanged: (v) =>
                                setState(() => tipoDoc = v ?? 'CI'),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                        child: AppTextField(
                            hint: 'Nro documento',
                            controller: nroDocCtrl,
                            prefixIcon: Icons.numbers)),
                  ]),
                  const SizedBox(height: 12),

                  Row(children: [
                    Expanded(
                        child: AppTextField(
                            hint: 'Teléfono',
                            controller: telCtrl,
                            prefixIcon: Icons.phone)),
                    const SizedBox(width: 12),
                    Expanded(
                        child: AppTextField(
                            hint: 'Fecha nac. (YYYY-MM-DD)',
                            controller: fechaNacCtrl,
                            prefixIcon: Icons.event)),
                  ]),
                  const SizedBox(height: 12),

                  AppTextField(
                      hint: 'Dirección (opcional)',
                      controller: dirCtrl,
                      prefixIcon: Icons.place_outlined),
                  const SizedBox(height: 12),

                  Row(children: [
                    Expanded(
                        child: AppTextField(
                            hint: 'Ocupación (opcional)',
                            controller: ocupCtrl,
                            prefixIcon: Icons.work_outline)),
                    const SizedBox(width: 12),
                    Expanded(
                        child: AppTextField(
                            hint: 'Ingresos mensuales (opcional)',
                            controller: ingresosCtrl,
                            prefixIcon: Icons.attach_money,
                            keyboardType: TextInputType.number)),
                  ]),

                  const SizedBox(height: 12),
                  if (error != null)
                    Text(error!, style: const TextStyle(color: Colors.red)),
                  const SizedBox(height: 18),

                  AppButton('Registrarse', onPressed: _submit),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
