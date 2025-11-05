class Validators {
  /// Verifica que el texto tenga al menos [min] caracteres.
  static bool minLen(String value, int min) {
    return value.trim().length >= min;
  }

  /// Verifica si un correo electrónico es válido (por si lo usas en otros formularios)
  static bool isEmail(String email) {
    final emailRegex = RegExp(r'^[\w\.\-]+@([\w\-]+\.)+[a-zA-Z]{2,4}$');
    return emailRegex.hasMatch(email.trim());
  }

  /// Valida un nombre de usuario: mínimo 3 caracteres, solo letras, números, guiones o guion_bajo.
  static bool isUsername(String username) {
    final regex = RegExp(r'^[a-zA-Z0-9._-]{3,}$');
    return regex.hasMatch(username.trim());
  }
}
