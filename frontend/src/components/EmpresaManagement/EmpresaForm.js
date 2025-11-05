import React, { useState, useEffect } from "react";
import api from "../../config/axios";

export default function EmpresaForm({ onCreated, initialData = null, onCancel = null }) {
  const [nombre, setNombre] = useState("");
  const [ruc, setRuc] = useState("");
  const [direccion, setDireccion] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialData) {
      setNombre(initialData.nombre || "");
      setRuc(initialData.ruc || "");
      setDireccion(initialData.direccion || "");
      setTelefono(initialData.telefono || "");
      setEmail(initialData.email || "");
    }
  }, [initialData]);

  const reset = () => {
    setNombre("");
    setRuc("");
    setDireccion("");
    setTelefono("");
    setEmail("");
  };

  const validate = () => {
    if (!nombre.trim()) return "El nombre es obligatorio.";
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Email inválido.";
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) {
      alert(err);
      return;
    }
    setLoading(true);
    try {
      const payload = {
        nombre: nombre.trim(),
        ruc: ruc.trim() || null,
        direccion: direccion.trim() || null,
        telefono: telefono.trim() || null,
        email: email.trim() || null,
      };

      let resp;
      if (initialData && initialData.id) {
        resp = await api.put(`empresas/${initialData.id}/`, payload);
      } else {
        resp = await api.post("empresas/", payload);
      }

      if (onCreated) onCreated(resp.data);
      if (!initialData) reset();
      alert("Empresa guardada correctamente.");
    } catch (error) {
      console.error("Error guardando empresa:", error);
      const message = error?.response?.data || error?.message || "Error al guardar la empresa.";
      alert(JSON.stringify(message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
      <h3>{initialData ? "Editar empresa" : "Registrar nueva empresa"}</h3>

      <div style={{ marginBottom: 8 }}>
        <label style={{ display: "block", fontSize: 14 }}>Nombre *</label>
        <input
          aria-label="nombre-empresa"
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
          style={{ width: "100%", padding: 8 }}
        />
      </div>

      <div style={{ marginBottom: 8, display: "flex", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", fontSize: 14 }}>RUC</label>
          <input
            aria-label="ruc-empresa"
            type="text"
            value={ruc}
            onChange={(e) => setRuc(e.target.value)}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", fontSize: 14 }}>Teléfono</label>
          <input
            aria-label="telefono-empresa"
            type="text"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
      </div>

      <div style={{ marginBottom: 8 }}>
        <label style={{ display: "block", fontSize: 14 }}>Dirección</label>
        <input
          aria-label="direccion-empresa"
          type="text"
          value={direccion}
          onChange={(e) => setDireccion(e.target.value)}
          style={{ width: "100%", padding: 8 }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: "block", fontSize: 14 }}>Email</label>
        <input
          aria-label="email-empresa"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: "100%", padding: 8 }}
        />
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" disabled={loading} style={{ padding: "8px 12px" }}>
          {loading ? "Guardando..." : initialData ? "Guardar cambios" : "Registrar empresa"}
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            style={{ padding: "8px 12px", background: "#f0f0f0" }}
          >
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}