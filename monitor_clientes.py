from repository import DatabaseRepository, DatabaseConfig
import time

def monitor_clientes():
    config = DatabaseConfig()
    repo = DatabaseRepository(config)
    
    print("Monitoreando cambios en la tabla de clientes...")
    print("Presiona Ctrl+C para detener")
    
    # Obtener estado inicial
    clientes_inicial = repo.listar_clientes()
    count_inicial = len(clientes_inicial)
    print(f"Clientes iniciales: {count_inicial}")
    
    if clientes_inicial:
        ultimo_cliente = clientes_inicial[-1]
        print(f"Último cliente: ID {ultimo_cliente.id} - {ultimo_cliente.nombres} {ultimo_cliente.apellidos}")
    
    print("\nEsperando nuevos clientes...")
    
    try:
        while True:
            time.sleep(5)  # Verificar cada 5 segundos
            clientes_actual = repo.listar_clientes()
            count_actual = len(clientes_actual)
            
            if count_actual > count_inicial:
                print(f"\n¡Nuevo cliente detectado!")
                print(f"Total clientes: {count_inicial} -> {count_actual}")
                
                # Mostrar nuevos clientes
                nuevos_clientes = clientes_actual[count_inicial:]
                for cliente in nuevos_clientes:
                    print(f"Nuevo cliente: ID {cliente.id} - {cliente.nombres} {cliente.apellidos} - {cliente.email}")
                
                count_inicial = count_actual
                
    except KeyboardInterrupt:
        print("\nMonitoreo detenido.")
        
    except Exception as e:
        print(f"Error durante el monitoreo: {e}")

if __name__ == "__main__":
    monitor_clientes()