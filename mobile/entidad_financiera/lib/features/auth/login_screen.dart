// lib/features/auth/login_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/widgets/app_button.dart';
import '../../core/widgets/app_text_field.dart';
import '../auth/auth.dart'; // authProvider

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final usernameCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  bool _hide = true;
  String? error;

  @override
  void dispose() {
    usernameCtrl.dispose();
    passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = usernameCtrl.text.trim();
    final pass = passCtrl.text;

    if (username.isEmpty || pass.isEmpty) {
      setState(() => error = 'Ingresa usuario y contraseña');
      return;
    }

    // marca UI en “cargando” leyendo el estado
    setState(() => error = null);

    final ok = await ref.read(authProvider.notifier).login(username, pass);

    // LOGS para depurar
    // ignore: avoid_print
    print('[UI] login() returned: $ok');

    if (!mounted) return;

    if (ok) {
      // limpiar el mensaje y navegar
      setState(() => error = null);
      context.go('/home');
    } else {
      setState(() => error = 'Credenciales inválidas');
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text(''),
        leading: context.canPop()
            ? BackButton(onPressed: () => context.pop())
            : null,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Iniciar sesión',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 18),

                  AppTextField(
                    hint: 'Usuario',
                    controller: usernameCtrl,
                    prefixIcon: Icons.person_outline,
                    keyboardType: TextInputType.text,
                    onSubmitted: (_) => _submit(),
                  ),
                  const SizedBox(height: 12),

                  AppTextField(
                    hint: 'Contraseña',
                    controller: passCtrl,
                    obscure: _hide,
                    prefixIcon: Icons.lock_outline,
                    suffixIcon: IconButton(
                      icon:
                          Icon(_hide ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setState(() => _hide = !_hide),
                    ),
                    onSubmitted: (_) => _submit(),
                  ),

                  const SizedBox(height: 8),

                  // solo muestra error si hay mensaje
                  if (error != null && error!.isNotEmpty)
                    Text(error!, style: const TextStyle(color: Colors.red)),

                  const Spacer(),

                  AppButton(
                    'Iniciar sesión',
                    loading: auth.loading,
                    onPressed: auth.loading ? null : _submit,
                  ),

                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: () => context.go('/register'),
                    child: const Text('¿No tienes cuenta? Registrarse'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
