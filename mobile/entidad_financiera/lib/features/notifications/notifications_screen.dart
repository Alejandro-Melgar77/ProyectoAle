import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'notifications_controller.dart';

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});
  @override
  ConsumerState<NotificationsScreen> createState() =>
      _NotificationsScreenState();
}

class _NotificationsScreenState extends ConsumerState<NotificationsScreen> {
  int tab = 0; // 0 todas, 1 no leídas

  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(notificationsProvider.notifier).load());
  }

  Future<void> _refresh() => ref.read(notificationsProvider.notifier).load();

  @override
  Widget build(BuildContext context) {
    final st = ref.watch(notificationsProvider);

    final items = st.items.where((n) => tab == 0 ? true : !n.leida).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Notificaciones')),
      body: Column(
        children: [
          const SizedBox(height: 8),
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(
                  value: 0,
                  label: Text('Todas'),
                  icon: Icon(Icons.inbox_outlined)),
              ButtonSegment(
                  value: 1,
                  label: Text('No leídas'),
                  icon: Icon(Icons.markunread_outlined)),
            ],
            selected: {tab},
            onSelectionChanged: (s) => setState(() => tab = s.first),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _refresh,
              child: st.loading
                  ? const Center(child: CircularProgressIndicator())
                  : items.isEmpty
                      ? const ListTile(title: Text('Sin notificaciones'))
                      : ListView.separated(
                          padding: const EdgeInsets.all(8),
                          itemCount: items.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 6),
                          itemBuilder: (ctx, i) {
                            final n = items[i];
                            return Dismissible(
                              key: ValueKey(n.id),
                              direction: n.leida
                                  ? DismissDirection.none
                                  : DismissDirection.endToStart,
                              background: Container(
                                alignment: Alignment.centerRight,
                                padding:
                                    const EdgeInsets.symmetric(horizontal: 16),
                                color: Colors.green,
                                child:
                                    const Icon(Icons.done, color: Colors.white),
                              ),
                              onDismissed: (_) => ref
                                  .read(notificationsProvider.notifier)
                                  .markRead(n.id),
                              child: Card(
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12)),
                                child: ListTile(
                                  leading: Icon(_icon(n.tipo),
                                      color:
                                          n.leida ? Colors.grey : Colors.blue),
                                  title: Text(n.titulo,
                                      style: TextStyle(
                                        fontWeight: n.leida
                                            ? FontWeight.w400
                                            : FontWeight.w700,
                                      )),
                                  subtitle: Text(n.cuerpo),
                                  trailing: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text(_niceDate(n.creada),
                                          style: const TextStyle(
                                              color: Colors.grey,
                                              fontSize: 12)),
                                      if (!n.leida)
                                        const Padding(
                                          padding: EdgeInsets.only(top: 6),
                                          child: CircleAvatar(
                                              radius: 4,
                                              backgroundColor: Colors.blue),
                                        )
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
            ),
          )
        ],
      ),
    );
  }

  String _niceDate(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year} '
      '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

  IconData _icon(String tipo) {
    switch (tipo.toUpperCase()) {
      case 'SOLICITUD':
        return Icons.description_outlined;
      case 'PLAN':
        return Icons.receipt_long_outlined;
      case 'PAGO':
        return Icons.payments_outlined;
    }
    return Icons.notifications_outlined;
  }
}
