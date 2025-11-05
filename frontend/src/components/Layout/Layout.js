import React, { useEffect } from "react";
import Sidebar from "../Sidebar/Sidebar";
import { useTheme } from "../../context/ThemeContext";
import "./Layout.css";

/**
 * Layout base con Sidebar + contenedor para las páginas.
 * Ajusta el padding-left según el ancho del sidebar (por CSS).
 */
export default function Layout({ children }) {
  const { darkMode, toggleDarkMode } = useTheme();

  useEffect(() => {
    document.body.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        <div className="app-main__inner">
          <button 
            onClick={toggleDarkMode}
            className="theme-toggle-button"
          >
            {darkMode ? '☀️ Modo Claro' : '🌙 Modo Oscuro'}
          </button>
          {children}
        </div>
      </main>
    </div>
  );
}
