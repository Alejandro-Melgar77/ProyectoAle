// ...existing code...
import React, { useEffect, useState } from "react";
import api from "../../config/axios";

/**
 * Página de gestión de empresas.
 * - Lista empresas (GET /empresas/)
 * - Formulario para crear empresa (POST /empresas/)
 *
 * Nota: Ajusta los nombres de los campos payload según el serializer del backend.
 */

function EmpresaForm({ onCreated }) {
  const [nombre, setNombre] = useState("");
  const [ruc, setRuc] = useState("");
  const [direccion, setDireccion] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const reset = () => {
    setNombre("");
    setRuc("");
    setDireccion("");
    setTelefono("");
    setEmail("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nombre.trim()) {
      alert("El nombre de la empresa es obligatorio.");
      return;
    }

    setLoading(true);
    try {
      const payload = { nombre: nombre.trim(), ruc: ruc.trim(), direccion: direccion.trim(), telefono: telefono.trim(), email: email.trim() };
      const { data } = await api.post("empresas/", payload);
      if (onCreated) onCreated(data);
      reset();
      alert("Empresa creada correctamente.");
    } catch (err) {
      console.error("Error creando empresa:", err);
      const msg = err?.response?.data || err?.message || "Error al crear la empresa.";
      alert(JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
      <h3>Registrar nueva empresa</h3>

      <div style={{ marginBottom: 8 }}>
        <label style={{ display: "block", fontSize: 14 }}>Nombre *</label>
        <input
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
          <input type="text" value={ruc} onChange={(e) => setRuc(e.target.value)} style={{ width: "100%", padding: 8 }} />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: "block", fontSize: 14 }}>Teléfono</label>
          <input type="text" value={telefono} onChange={(e) => setTelefono(e.target.value)} style={{ width: "100%", padding: 8 }} />
        </div>
      </div>

      <div style={{ marginBottom: 8 }}>
        <label style={{ display: "block", fontSize: 14 }}>Dirección</label>
        <input type="text" value={direccion} onChange={(e) => setDireccion(e.target.value)} style={{ width: "100%", padding: 8 }} />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: "block", fontSize: 14 }}>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%", padding: 8 }} />
      </div>

      <div>
        <button type="submit" disabled={loading} style={{ padding: "8px 12px" }}>
          {loading ? "Guardando..." : "Registrar empresa"}
        </button>
      </div>
    </form>
  );
}

export default function EmpresaManagement() {
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let mounted = true;
    const fetchEmpresas = async () => {
      setLoading(true);
      try {
        const { data } = await api.get("empresas/");
        if (mounted) setEmpresas(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Error cargando empresas:", err);
        if (mounted) setEmpresas([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchEmpresas();
    return () => {
      mounted = false;
    };
  }, [refreshKey]);

  const handleCreated = (newEmpresa) => {
    // Si el backend devuelve el nuevo objeto, lo agregamos al inicio
    setEmpresas((prev) => [newEmpresa, ...prev]);
  };

  const handleRefresh = () => setRefreshKey((k) => k + 1);

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar esta empresa? Esta acción no se puede deshacer.")) return;
    try {
      await api.delete(`empresas/${id}/`);
      setEmpresas((prev) => prev.filter((e) => e.id !== id));
      alert("Empresa eliminada.");
    } catch (err) {
      console.error("Error eliminando empresa:", err);
      alert("No se pudo eliminar la empresa.");
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <h2>Gestión de Empresas</h2>

      <EmpresaForm onCreated={handleCreated} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Empresas registradas</h3>
        <div>
          <button onClick={handleRefresh} style={{ padding: "6px 10px" }}>
            {loading ? "Cargando..." : "Actualizar"}
          </button>
        </div>
      </div>

      {loading ? (
        <p>Cargando empresas...</p>
      ) : empresas.length === 0 ? (
        <p>No hay empresas registradas.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>Nombre</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>RUC</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>Contacto</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {empresas.map((e) => (
              <tr key={e.id}>
                <td style={{ padding: 8, borderBottom: "1px solid #f1f1f1" }}>{e.nombre}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f1f1f1" }}>{e.ruc || "—"}</td>
                <td style={{ padding: 8, borderBottom: "1px solid #f1f1f1" }}>
                  {e.telefono || ""} {e.email ? ` / ${e.email}` : ""}
                </td>
                <td style={{ padding: 8, borderBottom: "1px solid #f1f1f1" }}>
                  {/* Editar puede implementarse luego */}
                  <button
                    onClick={() => alert("Implementar edición si es necesario")}
                    style={{ marginRight: 8, padding: "6px 10px" }}
                  >
                    Editar
                  </button>
                  <button onClick={() => handleDelete(e.id)} style={{ padding: "6px 10px" }}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
// ...existing code...