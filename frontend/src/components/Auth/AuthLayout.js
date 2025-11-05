// src/components/Auth/AuthLayout.js
import React from "react";
import "./AuthLayout.css";

/**
 * Layout centrado a pantalla completa para páginas de autenticación.
 * No renderiza header ni footer. Solo centra el contenido (Login / Reset).
 */
export default function AuthLayout({ children }) {
  return (
    <div className="auth-screen">
      <div className="auth-card">
        {children}
      </div>
    </div>
  );
}
