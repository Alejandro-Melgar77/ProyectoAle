import 'package:flutter/material.dart';

class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    required this.hint,
    required this.controller,
    this.prefixIcon,
    this.keyboardType,
    this.obscure = false,
    this.textInputAction = TextInputAction.done,
    this.onSubmitted, // 👈 nuevo
    this.suffixIcon, // 👈 nuevo
  });

  final String hint;
  final TextEditingController controller;
  final IconData? prefixIcon;
  final TextInputType? keyboardType;
  final bool obscure;
  final TextInputAction textInputAction;
  final ValueChanged<String>? onSubmitted; // 👈 nuevo
  final Widget? suffixIcon; // 👈 nuevo

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      obscureText: obscure,
      textInputAction: textInputAction,
      onSubmitted: onSubmitted, // 👈 pasa directo al TextField
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: prefixIcon == null ? null : Icon(prefixIcon),
        suffixIcon: suffixIcon, // 👈 nuevo
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
      ),
    );
  }
}
