import sys
sys.path.append('.')

from datetime import datetime
from repository import DatabaseRepository
from services import ClienteService
from config import DatabaseConfig, CasinoConfig

def debug_registrar_visita():
    """Debug detallado del proceso de registrar_visita"""
    
    print("=== DEBUG REGISTRAR_VISITA ===")
    print(f"Fecha/hora actual: {datetime.now()}")
    print()
    
    # Inicializar servicios
    db_config = DatabaseConfig()
    casino_config = CasinoConfig()
    repository = DatabaseRepository(db_config)
    cliente_service = ClienteService(repository, casino_config)
    
    cliente_id = 6  # Cliente que creamos anteriormente
    
    try:
        print("1. Obteniendo cliente ANTES de registrar visita...")
        cliente_antes = repository.obtener_cliente(cliente_id)
        
        if cliente_antes:
            print(f"   ID: {cliente_antes.id}")
            print(f"   Nombre: {cliente_antes.nombre_completo}")
            print(f"   Total visitas: {cliente_antes.total_visitas}")
            print(f"   Fecha última visita: {cliente_antes.fecha_ultima_visita}")
            print(f"   Total gastado: {cliente_antes.total_gastado}")
            print(f"   Puntos acumulados: {cliente_antes.puntos_acumulados}")
        else:
            print("   ❌ Cliente no encontrado")
            return
        
        print()
        print("2. Registrando visita...")
        
        # Registrar visita
        resultado = cliente_service.registrar_visita(cliente_id, 0.0)
        print(f"   Resultado: {resultado}")
        
        print()
        print("3. Obteniendo cliente DESPUÉS de registrar visita...")
        cliente_despues = repository.obtener_cliente(cliente_id)
        
        if cliente_despues:
            print(f"   ID: {cliente_despues.id}")
            print(f"   Nombre: {cliente_despues.nombre_completo}")
            print(f"   Total visitas: {cliente_despues.total_visitas}")
            print(f"   Fecha última visita: {cliente_despues.fecha_ultima_visita}")
            print(f"   Total gastado: {cliente_despues.total_gastado}")
            print(f"   Puntos acumulados: {cliente_despues.puntos_acumulados}")
            
            print()
            print("4. Comparación de cambios:")
            print(f"   Visitas: {cliente_antes.total_visitas} -> {cliente_despues.total_visitas} (cambio: {cliente_despues.total_visitas - cliente_antes.total_visitas})")
            print(f"   Fecha última visita: {cliente_antes.fecha_ultima_visita} -> {cliente_despues.fecha_ultima_visita}")
            print(f"   Total gastado: {cliente_antes.total_gastado} -> {cliente_despues.total_gastado}")
            print(f"   Puntos: {cliente_antes.puntos_acumulados} -> {cliente_despues.puntos_acumulados}")
            
            if cliente_despues.fecha_ultima_visita:
                print("   ✅ ÉXITO: fecha_ultima_visita se actualizó")
            else:
                print("   ❌ ERROR: fecha_ultima_visita sigue siendo NULL")
                
        else:
            print("   ❌ Cliente no encontrado después de la actualización")
            
        print()
        print("5. Verificando directamente en la base de datos...")
        
        # Consulta directa a la base de datos
        with repository.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombres, apellidos, total_visitas, fecha_ultima_visita, 
                       total_gastado, puntos_acumulados, fecha_actualizacion
                FROM clientes 
                WHERE id = ?
            """, (cliente_id,))
            
            row = cursor.fetchone()
            if row:
                print(f"   ID: {row[0]}")
                print(f"   Nombre: {row[1]} {row[2]}")
                print(f"   Total visitas: {row[3]}")
                print(f"   Fecha última visita: {row[4]}")
                print(f"   Total gastado: {row[5]}")
                print(f"   Puntos acumulados: {row[6]}")
                print(f"   Fecha actualización: {row[7]}")
                
                if row[4]:  # fecha_ultima_visita
                    print("   ✅ CONFIRMADO: fecha_ultima_visita está en la BD")
                else:
                    print("   ❌ CONFIRMADO: fecha_ultima_visita es NULL en la BD")
            else:
                print("   ❌ No se encontró el cliente en la consulta directa")
                
    except Exception as e:
        print(f"❌ Error durante el debug: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== FIN DEL DEBUG ===")

if __name__ == "__main__":
    debug_registrar_visita()