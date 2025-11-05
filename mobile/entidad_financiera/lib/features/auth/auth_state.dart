class AuthState {
  final bool loading;
  final bool authenticated;
  final Map<String, dynamic>? user;

  const AuthState({
    this.loading = false,
    this.authenticated = false,
    this.user,
  });

  AuthState copyWith({
    bool? loading,
    bool? authenticated,
    Map<String, dynamic>? user,
  }) {
    return AuthState(
      loading: loading ?? this.loading,
      authenticated: authenticated ?? this.authenticated,
      user: user ?? this.user,
    );
  }
}
