#!/usr/bin/env python3
"""
Script para mostrar los IDs de clientes disponibles en la base de datos
"""

import sqlite3
from datetime import datetime

def mostrar_clientes():
    """Mostrar todos los clientes disponibles con sus IDs"""
    try:
        conn = sqlite3.connect('atlantic_city_casino.db')
        cursor = conn.cursor()
        
        # Obtener todos los clientes
        cursor.execute("""
            SELECT id, numero_documento, nombre_completo, email, tipo_cliente, 
                   total_visitas, total_gastado, puntos_acumulados, activo
            FROM clientes 
            ORDER BY id
        """)
        
        clientes = cursor.fetchall()
        
        if not clientes:
            print("No hay clientes registrados en la base de datos.")
            return
        
        print("=== CLIENTES DISPONIBLES ===")
        print(f"{'ID':<4} {'Documento':<15} {'Nombre':<25} {'Email':<30} {'Tipo':<10} {'Visitas':<8} {'Gastado':<12} {'Puntos':<8} {'Activo':<6}")
        print("-" * 120)
        
        for cliente in clientes:
            id_cliente, documento, nombre, email, tipo, visitas, gastado, puntos, activo = cliente
            activo_str = "Sí" if activo else "No"
            gastado_str = f"${gastado:,.0f}" if gastado else "$0"
            
            print(f"{id_cliente:<4} {documento:<15} {nombre:<25} {email:<30} {tipo:<10} {visitas:<8} {gastado_str:<12} {puntos:<8} {activo_str:<6}")
        
        print(f"\nTotal de clientes: {len(clientes)}")
        
        # Mostrar algunos clientes con transacciones
        cursor.execute("""
            SELECT DISTINCT c.id, c.nombre_completo, COUNT(t.id) as num_transacciones
            FROM clientes c
            LEFT JOIN transacciones t ON c.id = t.cliente_id
            GROUP BY c.id, c.nombre_completo
            HAVING COUNT(t.id) > 0
            ORDER BY COUNT(t.id) DESC
            LIMIT 5
        """)
        
        clientes_con_transacciones = cursor.fetchall()
        
        if clientes_con_transacciones:
            print("\n=== CLIENTES CON TRANSACCIONES (para probar) ===")
            for cliente_id, nombre, num_trans in clientes_con_transacciones:
                print(f"ID: {cliente_id} - {nombre} ({num_trans} transacciones)")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")

def mostrar_transacciones_recientes():
    """Mostrar las transacciones más recientes"""
    try:
        conn = sqlite3.connect('atlantic_city_casino.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.cliente_id, c.nombre_completo, t.tipo, t.monto, 
                   t.descripcion, t.fecha, t.ubicacion
            FROM transacciones t
            JOIN clientes c ON t.cliente_id = c.id
            ORDER BY t.fecha DESC
            LIMIT 10
        """)
        
        transacciones = cursor.fetchall()
        
        if transacciones:
            print("\n=== TRANSACCIONES RECIENTES ===")
            print(f"{'ID':<4} {'Cliente ID':<10} {'Cliente':<25} {'Tipo':<10} {'Monto':<12} {'Descripción':<30} {'Fecha':<20}")
            print("-" * 120)
            
            for trans in transacciones:
                trans_id, cliente_id, nombre, tipo, monto, desc, fecha, ubicacion = trans
                monto_str = f"${monto:,.0f}"
                desc_str = (desc[:27] + "...") if desc and len(desc) > 30 else (desc or "N/A")
                
                print(f"{trans_id:<4} {cliente_id:<10} {nombre:<25} {tipo:<10} {monto_str:<12} {desc_str:<30} {fecha:<20}")
        else:
            print("\nNo hay transacciones registradas.")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al consultar transacciones: {e}")

if __name__ == "__main__":
    print("Consultando base de datos del Casino Atlantic City...\n")
    mostrar_clientes()
    mostrar_transacciones_recientes()
    print("\n=== INSTRUCCIONES ===")
    print("1. En la página de administración, ve a la sección 'Transacciones'")
    print("2. Ingresa uno de los IDs de cliente mostrados arriba en el campo 'Cliente ID'")
    print("3. Haz clic en 'Buscar' para ver las transacciones de ese cliente")
    print("4. Si no aparecen transacciones, puedes crear nuevas usando el botón 'Nueva Transacción'")