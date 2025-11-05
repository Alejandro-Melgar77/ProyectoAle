import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router.dart';
import 'core/theme.dart';
import 'data/api_client.dart';
import 'features/auth/auth.dart';

class MyApp extends ConsumerStatefulWidget {
  const MyApp({super.key});
  @override
  ConsumerState<MyApp> createState() => _MyAppState();
}

class _MyAppState extends ConsumerState<MyApp> {
  late final router = AppRouter.create(ref);

  @override
  void initState() {
    super.initState();
    ApiClient.I.init();
    // intenta levantar sesión si hay tokens guardados
    Future.microtask(() => ref.read(authProvider.notifier).loadSession());
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Entidad Financiera',
      theme: appTheme(),
      routerConfig: router,
    );
  }
}
