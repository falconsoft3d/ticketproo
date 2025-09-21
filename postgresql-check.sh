#!/bin/bash

# Script de diagnóstico rápido para PostgreSQL
# Ejecutar antes del deployment principal

echo "🔍 TicketProo - Diagnóstico PostgreSQL"
echo "======================================"

# Verificar PostgreSQL
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL instalado"
    
    # Obtener versión
    PG_VERSION=$(sudo -u postgres psql --version | grep -oP '\d+\.\d+' | head -1)
    echo "📦 Versión: $PG_VERSION"
    
    # Buscar directorios de configuración
    echo "📁 Buscando archivos de configuración..."
    PG_CONFIG=$(find /etc/postgresql -name "postgresql.conf" -type f 2>/dev/null | head -1)
    PG_HBA=$(find /etc/postgresql -name "pg_hba.conf" -type f 2>/dev/null | head -1)
    
    if [ -n "$PG_CONFIG" ]; then
        echo "✓ postgresql.conf: $PG_CONFIG"
        PG_DIR=$(dirname "$PG_CONFIG")
        echo "📂 Directorio config: $PG_DIR"
    else
        echo "❌ postgresql.conf no encontrado"
    fi
    
    if [ -n "$PG_HBA" ]; then
        echo "✓ pg_hba.conf: $PG_HBA"
    else
        echo "❌ pg_hba.conf no encontrado"
    fi
    
    # Verificar estado del servicio
    if systemctl is-active --quiet postgresql; then
        echo "✓ PostgreSQL servicio activo"
    else
        echo "⚠️  PostgreSQL servicio inactivo - iniciando..."
        systemctl start postgresql
        sleep 3
        if systemctl is-active --quiet postgresql; then
            echo "✓ PostgreSQL iniciado correctamente"
        else
            echo "❌ Error al iniciar PostgreSQL"
        fi
    fi
    
    # Verificar conectividad
    if sudo -u postgres psql -c "SELECT version();" &>/dev/null; then
        echo "✓ Conexión PostgreSQL OK"
        sudo -u postgres psql -c "SELECT version();" | head -2
    else
        echo "❌ Error de conexión PostgreSQL"
    fi
    
else
    echo "❌ PostgreSQL no instalado"
fi

echo ""
echo "🔧 Comandos útiles:"
echo "   Reiniciar: sudo systemctl restart postgresql"
echo "   Estado: sudo systemctl status postgresql"
echo "   Logs: sudo journalctl -u postgresql -f"
echo "   Conectar: sudo -u postgres psql"