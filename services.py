from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import logging
import uuid
import json
from models import (
    Cliente, Promocion, Transaccion, Ticket, Empleado,
    TipoCliente, EstadoPromocion, TipoPromocion, EstadoTicket, TipoTicket, TipoTransaccion,
    validar_email, validar_telefono, validar_documento
)
from repository import DatabaseRepository
from config import CasinoConfig

class ClienteService:
    """Servicio para gestión de clientes del casino"""
    
    def __init__(self, repository: DatabaseRepository, casino_config: CasinoConfig):
        self.repository = repository
        self.casino_config = casino_config
        self.logger = logging.getLogger(__name__)
    
    def registrar_cliente(self, datos_cliente: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Registra un nuevo cliente con validaciones"""
        try:
            # Validaciones
            if not validar_documento(datos_cliente.get('numero_documento', ''), datos_cliente.get('tipo_documento', 'CC')):
                return False, "Número de documento inválido", None
            
            if datos_cliente.get('email') and not validar_email(datos_cliente['email']):
                return False, "Email inválido", None
            
            if datos_cliente.get('telefono') and not validar_telefono(datos_cliente['telefono']):
                return False, "Teléfono inválido", None
            
            # Verificar si ya existe
            cliente_existente = self.repository.obtener_cliente_por_documento(datos_cliente['numero_documento'])
            if cliente_existente:
                return False, "Ya existe un cliente con este documento", None
            
            # Crear cliente
            cliente = Cliente(
                numero_documento=datos_cliente['numero_documento'],
                tipo_documento=datos_cliente.get('tipo_documento', 'CC'),
                nombres=datos_cliente['nombres'],
                apellidos=datos_cliente['apellidos'],
                email=datos_cliente.get('email', ''),
                telefono=datos_cliente.get('telefono', ''),
                fecha_nacimiento=datos_cliente.get('fecha_nacimiento'),
                direccion=datos_cliente.get('direccion', ''),
                ciudad=datos_cliente.get('ciudad', ''),
                tipo_cliente=TipoCliente.NUEVO,
                puntos_acumulados=self.casino_config.puntos_bienvenida
            )
            
            cliente_id = self.repository.crear_cliente(cliente)
            
            # Crear promoción de bienvenida si está configurada
            if self.casino_config.promocion_bienvenida_activa:
                self._crear_promocion_bienvenida(cliente_id)
            
            self.logger.info(f"Cliente registrado exitosamente: {cliente_id}")
            return True, "Cliente registrado exitosamente", cliente_id
            
        except Exception as e:
            self.logger.error(f"Error al registrar cliente: {e}")
            return False, f"Error interno: {str(e)}", None
    
    def actualizar_tipo_cliente(self, cliente_id: int) -> bool:
        """Actualiza automáticamente el tipo de cliente basado en su actividad"""
        try:
            cliente = self.repository.obtener_cliente(cliente_id)
            if not cliente:
                return False
            
            nuevo_tipo = self._calcular_tipo_cliente(cliente)
            
            if nuevo_tipo != cliente.tipo_cliente:
                cliente.tipo_cliente = nuevo_tipo
                self.repository.actualizar_cliente(cliente)
                
                # Crear promociones automáticas según el nuevo tipo
                self._crear_promociones_automaticas(cliente)
                
                self.logger.info(f"Tipo de cliente actualizado a {nuevo_tipo.value} para cliente {cliente_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al actualizar tipo de cliente: {e}")
            return False
    
    def registrar_visita(self, cliente_id: int, monto_gastado: float = 0.0) -> bool:
        """Registra una visita del cliente y actualiza sus estadísticas"""
        try:
            cliente = self.repository.obtener_cliente(cliente_id)
            if not cliente:
                return False
            
            cliente.total_visitas += 1
            cliente.total_gastado += monto_gastado
            cliente.fecha_ultima_visita = datetime.now()
            
            # Calcular puntos ganados
            puntos_ganados = int(monto_gastado * self.casino_config.puntos_por_peso)
            cliente.puntos_acumulados += puntos_ganados
            
            self.repository.actualizar_cliente(cliente)
            
            # Actualizar tipo de cliente si es necesario
            self.actualizar_tipo_cliente(cliente_id)
            
            self.logger.info(f"Visita registrada para cliente {cliente_id}: ${monto_gastado}, {puntos_ganados} puntos")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al registrar visita: {e}")
            return False
    
    def _calcular_tipo_cliente(self, cliente: Cliente) -> TipoCliente:
        """Calcula el tipo de cliente basado en su actividad"""
        if cliente.total_gastado >= self.casino_config.umbral_vip:
            return TipoCliente.VIP
        elif cliente.total_visitas >= self.casino_config.umbral_frecuente:
            return TipoCliente.FRECUENTE
        elif cliente.total_visitas >= self.casino_config.umbral_regular:
            return TipoCliente.REGULAR
        else:
            return TipoCliente.NUEVO
    
    def _crear_promocion_bienvenida(self, cliente_id: int):
        """Crea una promoción de bienvenida para un nuevo cliente"""
        promocion = Promocion(
            titulo="Bienvenida al Casino",
            descripcion="Promoción especial para nuevos clientes",
            tipo=TipoPromocion.PUNTOS_BONUS,
            valor=self.casino_config.puntos_bienvenida,
            fecha_inicio=datetime.now(),
            fecha_fin=datetime.now() + timedelta(days=30),
            cliente_id=cliente_id,
            creado_por="SISTEMA"
        )
        
        self.repository.crear_promocion(promocion)
    
    def _crear_promociones_automaticas(self, cliente: Cliente):
        """Crea promociones automáticas basadas en el tipo de cliente"""
        promociones = []
        
        if cliente.tipo_cliente == TipoCliente.VIP:
            promociones.extend([
                Promocion(
                    titulo="Descuento VIP",
                    descripcion="20% de descuento en consumos",
                    tipo=TipoPromocion.DESCUENTO,
                    valor=20.0,
                    fecha_inicio=datetime.now(),
                    fecha_fin=datetime.now() + timedelta(days=90),
                    cliente_id=cliente.id,
                    creado_por="SISTEMA"
                ),
                Promocion(
                    titulo="Bebida VIP Gratis",
                    descripcion="Bebida premium gratuita",
                    tipo=TipoPromocion.BEBIDA_GRATIS,
                    valor=1.0,
                    fecha_inicio=datetime.now(),
                    fecha_fin=datetime.now() + timedelta(days=30),
                    cliente_id=cliente.id,
                    usos_maximos=5,
                    creado_por="SISTEMA"
                )
            ])
        
        elif cliente.tipo_cliente == TipoCliente.FRECUENTE:
            promociones.append(
                Promocion(
                    titulo="Puntos Bonus Frecuente",
                    descripcion="Puntos adicionales por ser cliente frecuente",
                    tipo=TipoPromocion.PUNTOS_BONUS,
                    valor=500.0,
                    fecha_inicio=datetime.now(),
                    fecha_fin=datetime.now() + timedelta(days=60),
                    cliente_id=cliente.id,
                    creado_por="SISTEMA"
                )
            )
        
        for promocion in promociones:
            self.repository.crear_promocion(promocion)

class PromocionService:
    """Servicio para gestión de promociones"""
    
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    def crear_promocion_personalizada(self, datos_promocion: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Crea una promoción personalizada"""
        try:
            promocion = Promocion(
                titulo=datos_promocion['titulo'],
                descripcion=datos_promocion.get('descripcion', ''),
                tipo=TipoPromocion(datos_promocion['tipo']),
                valor=datos_promocion.get('valor', 0.0),
                fecha_inicio=datos_promocion['fecha_inicio'],
                fecha_fin=datos_promocion['fecha_fin'],
                cliente_id=datos_promocion.get('cliente_id'),
                usos_maximos=datos_promocion.get('usos_maximos', 1),
                condiciones=datos_promocion.get('condiciones', ''),
                creado_por=datos_promocion.get('creado_por', 'ADMIN')
            )
            
            promocion_id = self.repository.crear_promocion(promocion)
            
            self.logger.info(f"Promoción creada: {promocion_id}")
            return True, "Promoción creada exitosamente", promocion_id
            
        except Exception as e:
            self.logger.error(f"Error al crear promoción: {e}")
            return False, f"Error interno: {str(e)}", None
    
    def canjear_promocion(self, codigo_promocion: str, cliente_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Canjea una promoción por código"""
        try:
            # Buscar promoción por código
            promocion = self._obtener_promocion_por_codigo(codigo_promocion)
            if not promocion:
                return False, "Código de promoción no válido", None
            
            # Verificar si puede canjearse
            if not promocion.puede_canjearse:
                return False, "La promoción no puede canjearse (expirada o agotada)", None
            
            # Verificar si es para un cliente específico
            if promocion.cliente_id and promocion.cliente_id != cliente_id:
                return False, "Esta promoción no está disponible para este cliente", None
            
            # Canjear promoción
            if promocion.canjear():
                self._actualizar_promocion(promocion)
                
                # Aplicar beneficio según el tipo
                beneficio = self._aplicar_beneficio_promocion(promocion, cliente_id)
                
                self.logger.info(f"Promoción canjeada: {codigo_promocion} por cliente {cliente_id}")
                return True, "Promoción canjeada exitosamente", beneficio
            else:
                return False, "Error al canjear la promoción", None
                
        except Exception as e:
            self.logger.error(f"Error al canjear promoción: {e}")
            return False, f"Error interno: {str(e)}", None
    
    def _obtener_promocion_por_codigo(self, codigo: str) -> Optional[Promocion]:
        """Obtiene una promoción por su código"""
        # Implementar búsqueda en base de datos
        # Por ahora retornamos None, se implementaría con el repository
        return None
    
    def _actualizar_promocion(self, promocion: Promocion):
        """Actualiza el estado de una promoción"""
        # Implementar actualización en base de datos
        pass
    
    def _aplicar_beneficio_promocion(self, promocion: Promocion, cliente_id: int) -> Dict[str, Any]:
        """Aplica el beneficio de la promoción al cliente"""
        beneficio = {
            'tipo': promocion.tipo.value,
            'valor': promocion.valor,
            'descripcion': promocion.descripcion
        }
        
        if promocion.tipo == TipoPromocion.PUNTOS_BONUS:
            # Agregar puntos al cliente
            cliente = self.repository.obtener_cliente(cliente_id)
            if cliente:
                cliente.puntos_acumulados += int(promocion.valor)
                self.repository.actualizar_cliente(cliente)
                beneficio['puntos_agregados'] = int(promocion.valor)
        
        return beneficio

class TransaccionService:
    """Servicio para gestión de transacciones"""
    
    def __init__(self, repository: DatabaseRepository, casino_config: CasinoConfig):
        self.repository = repository
        self.casino_config = casino_config
        self.logger = logging.getLogger(__name__)
    
    def procesar_transaccion(self, datos_transaccion: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Procesa una nueva transacción"""
        try:
            # Calcular puntos ganados
            puntos_ganados = 0
            if datos_transaccion['tipo'] in ['juego', 'consumo']:
                puntos_ganados = int(datos_transaccion['monto'] * self.casino_config.puntos_por_peso)
            
            transaccion = Transaccion(
                cliente_id=datos_transaccion['cliente_id'],
                tipo=TipoTransaccion(datos_transaccion['tipo']),
                monto=datos_transaccion['monto'],
                descripcion=datos_transaccion.get('descripcion', ''),
                ubicacion=datos_transaccion.get('ubicacion', ''),
                promocion_id=datos_transaccion.get('promocion_id'),
                puntos_ganados=puntos_ganados,
                metodo_pago=datos_transaccion.get('metodo_pago', ''),
                numero_referencia=datos_transaccion.get('numero_referencia'),
                empleado_id=datos_transaccion.get('empleado_id'),
                notas=datos_transaccion.get('notas', '')
            )
            
            transaccion_id = self.repository.crear_transaccion(transaccion)
            
            # Actualizar estadísticas del cliente
            if datos_transaccion['tipo'] in ['juego', 'consumo']:
                cliente_service = ClienteService(self.repository, self.casino_config)
                cliente_service.registrar_visita(datos_transaccion['cliente_id'], datos_transaccion['monto'])
            
            # Actualizar saldo del cliente para recargas
            if datos_transaccion['tipo'] == 'ingreso':
                self.logger.info(f"Procesando recarga para cliente {datos_transaccion['cliente_id']}, monto: {datos_transaccion['monto']}")
                cliente = self.repository.obtener_cliente(datos_transaccion['cliente_id'])
                if cliente:
                    saldo_anterior = cliente.saldo
                    cliente.saldo += datos_transaccion['monto']
                    self.logger.info(f"Actualizando saldo: {saldo_anterior} -> {cliente.saldo}")
                    resultado = self.repository.actualizar_cliente(cliente)
                    self.logger.info(f"Resultado actualización cliente: {resultado}")
                else:
                    self.logger.error(f"Cliente {datos_transaccion['cliente_id']} no encontrado para actualizar saldo")
            
            self.logger.info(f"Transacción procesada: {transaccion_id}")
            return True, "Transacción procesada exitosamente", transaccion_id
            
        except Exception as e:
            self.logger.error(f"Error al procesar transacción: {e}")
            return False, f"Error interno: {str(e)}", None
    
    def obtener_resumen_diario(self, fecha: date = None) -> Dict[str, Any]:
        """Obtiene resumen de transacciones del día"""
        if not fecha:
            fecha = date.today()
        
        fecha_inicio = datetime.combine(fecha, datetime.min.time())
        fecha_fin = datetime.combine(fecha, datetime.max.time())
        
        try:
            transacciones = self.repository.obtener_transacciones_periodo(fecha_inicio, fecha_fin)
            
            resumen = {
                'fecha': fecha.isoformat(),
                'total_transacciones': sum(t['cantidad'] for t in transacciones),
                'total_ingresos': sum(t['total_monto'] for t in transacciones if t['tipo'] in ['juego', 'consumo']),
                'por_tipo': transacciones
            }
            
            return resumen
            
        except Exception as e:
            self.logger.error(f"Error al obtener resumen diario: {e}")
            return {}

class TicketService:
    """Servicio para gestión de tickets de atención al cliente"""
    
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    def crear_ticket(self, datos_ticket: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Crea un nuevo ticket de atención"""
        try:
            ticket = Ticket(
                cliente_id=datos_ticket['cliente_id'],
                tipo=TipoTicket(datos_ticket['tipo']),
                prioridad=datos_ticket.get('prioridad', 'MEDIA'),
                asunto=datos_ticket['asunto'],
                descripcion=datos_ticket['descripcion'],
                categoria=datos_ticket.get('categoria', ''),
                subcategoria=datos_ticket.get('subcategoria', '')
            )
            
            # Asignar automáticamente según la prioridad
            if ticket.prioridad == 'CRITICA':
                ticket.asignado_a = self._obtener_agente_disponible('supervisor')
            else:
                ticket.asignado_a = self._obtener_agente_disponible('agente')
            
            ticket_id = self.repository.crear_ticket(ticket)
            
            self.logger.info(f"Ticket creado: {ticket_id}")
            return True, "Ticket creado exitosamente", ticket_id
            
        except Exception as e:
            self.logger.error(f"Error al crear ticket: {e}")
            return False, f"Error interno: {str(e)}", None
    
    def resolver_ticket(self, ticket_id: int, resolucion: str, usuario: str) -> Tuple[bool, str]:
        """Resuelve un ticket"""
        try:
            ticket = self.repository.obtener_ticket(ticket_id)
            if not ticket:
                return False, "Ticket no encontrado"
            
            ticket.resolver(resolucion, usuario)
            self.repository.actualizar_ticket(ticket)
            
            self.logger.info(f"Ticket resuelto: {ticket_id}")
            return True, "Ticket resuelto exitosamente"
            
        except Exception as e:
            self.logger.error(f"Error al resolver ticket: {e}")
            return False, f"Error interno: {str(e)}"
    
    def _obtener_agente_disponible(self, tipo: str) -> Optional[str]:
        """Obtiene un agente disponible para asignar el ticket"""
        # Implementar lógica de asignación automática
        # Por ahora retorna un valor por defecto
        if tipo == 'supervisor':
            return 'supervisor@casino.com'
        else:
            return 'agente@casino.com'
    
    def obtener_metricas_atencion(self) -> Dict[str, Any]:
        """Obtiene métricas de atención al cliente"""
        try:
            tickets_abiertos = self.repository.obtener_tickets_abiertos()
            
            metricas = {
                'tickets_abiertos': len(tickets_abiertos),
                'tickets_criticos': len([t for t in tickets_abiertos if t.prioridad == 'CRITICA']),
                'tiempo_promedio_respuesta': self._calcular_tiempo_promedio_respuesta(),
                'satisfaccion_promedio': self._calcular_satisfaccion_promedio()
            }
            
            return metricas
            
        except Exception as e:
            self.logger.error(f"Error al obtener métricas: {e}")
            return {}
    
    def _calcular_tiempo_promedio_respuesta(self) -> float:
        """Calcula el tiempo promedio de respuesta"""
        # Implementar cálculo basado en tickets resueltos
        return 0.0
    
    def _calcular_satisfaccion_promedio(self) -> float:
        """Calcula la satisfacción promedio del cliente"""
        # Implementar cálculo basado en encuestas de satisfacción
        return 0.0

class ReporteService:
    """Servicio para generación de reportes"""
    
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    def generar_reporte_clientes(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Genera reporte de clientes"""
        try:
            estadisticas = self.repository.obtener_estadisticas_clientes()
            
            # Obtener clientes según filtros
            filtros = parametros.get('filtros', {})
            clientes = self.repository.listar_clientes(filtros, parametros.get('limite', 1000))
            
            reporte = {
                'tipo': 'clientes',
                'fecha_generacion': datetime.now().isoformat(),
                'parametros': parametros,
                'estadisticas_generales': estadisticas,
                'total_registros': len(clientes),
                'clientes': [{
                    'id': c.id,
                    'nombre_completo': c.nombre_completo,
                    'tipo_cliente': c.tipo_cliente.value,
                    'total_visitas': c.total_visitas,
                    'total_gastado': c.total_gastado,
                    'puntos_acumulados': c.puntos_acumulados,
                    'fecha_ultima_visita': c.fecha_ultima_visita.isoformat() if c.fecha_ultima_visita else None
                } for c in clientes]
            }
            
            return reporte
            
        except Exception as e:
            self.logger.error(f"Error al generar reporte de clientes: {e}")
            return {}
    
    def generar_reporte_transacciones(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Genera reporte de transacciones por período"""
        try:
            transacciones = self.repository.obtener_transacciones_periodo(fecha_inicio, fecha_fin)
            
            reporte = {
                'tipo': 'transacciones',
                'fecha_generacion': datetime.now().isoformat(),
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                },
                'resumen_por_tipo': transacciones,
                'total_transacciones': sum(t['cantidad'] for t in transacciones),
                'total_monto': sum(t['total_monto'] for t in transacciones)
            }
            
            return reporte
            
        except Exception as e:
            self.logger.error(f"Error al generar reporte de transacciones: {e}")
            return {}
    
    def exportar_reporte(self, reporte: Dict[str, Any], formato: str = 'JSON') -> Tuple[bool, str, Optional[str]]:
        """Exporta un reporte en el formato especificado"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"reporte_{reporte['tipo']}_{timestamp}"
            
            if formato.upper() == 'JSON':
                archivo_path = f"{nombre_archivo}.json"
                with open(archivo_path, 'w', encoding='utf-8') as f:
                    json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)
            
            elif formato.upper() == 'CSV':
                import pandas as pd
                archivo_path = f"{nombre_archivo}.csv"
                
                if reporte['tipo'] == 'clientes':
                    df = pd.DataFrame(reporte['clientes'])
                    df.to_csv(archivo_path, index=False, encoding='utf-8')
                elif reporte['tipo'] == 'transacciones':
                    df = pd.DataFrame(reporte['resumen_por_tipo'])
                    df.to_csv(archivo_path, index=False, encoding='utf-8')
            
            else:
                return False, "Formato no soportado", None
            
            self.logger.info(f"Reporte exportado: {archivo_path}")
            return True, "Reporte exportado exitosamente", archivo_path
            
        except Exception as e:
            self.logger.error(f"Error al exportar reporte: {e}")
            return False, f"Error interno: {str(e)}", None