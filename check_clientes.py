from repository import DatabaseRepository, DatabaseConfig
from models import Cliente

def check_clientes_in_sqlserver():
    try:
        config = DatabaseConfig()
        repo = DatabaseRepository(config)
        
        print("Verificando clientes en SQL Server...")
        clientes = repo.listar_clientes()
        print(f"Total clientes en SQL Server: {len(clientes)}")
        
        if clientes:
            print("\nÚltimos 5 clientes:")
            for cliente in clientes[-5:]:
                print(f"ID: {cliente.id}, Nombre: {cliente.nombres} {cliente.apellidos}, Email: {cliente.email}")
        else:
            print("No hay clientes en la base de datos SQL Server")
            
    except Exception as e:
        print(f"Error al consultar SQL Server: {e}")

if __name__ == "__main__":
    check_clientes_in_sqlserver()