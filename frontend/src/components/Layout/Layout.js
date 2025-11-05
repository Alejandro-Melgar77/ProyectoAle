import React from "react";
import Sidebar from "../Sidebar/Sidebar";
import "./Layout.css";

/**
 * Layout base con Sidebar + contenedor para las páginas.
 * Ajusta el padding-left según el ancho del sidebar (por CSS).
 */
export default function Layout({ children }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        <div className="app-main__inner">
          {children}
        </div>
      </main>
    </div>
  );
}
