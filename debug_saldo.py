from config import get_connection_string, DatabaseConfig
from repository import DatabaseRepository

def test_saldo_fix():
    try:
        config = DatabaseConfig()
        repository = DatabaseRepository(config)
        
        cliente = repository.obtener_cliente(1)
        print(f"Saldo en objeto Cliente: {cliente.saldo}")
        print(f"Tipo de saldo en Cliente: {type(cliente.saldo)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_saldo_fix()