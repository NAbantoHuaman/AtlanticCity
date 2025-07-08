// Configuración global
const API_BASE_URL = 'http://localhost:8001';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Verificar si estamos en la página del cliente
const isClientePage = window.location.pathname.includes('cliente.html');

// Inicialización de la aplicación
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Si estamos en la página del cliente, no inicializar app.js
    if (isClientePage) {
        return;
    }
    
    // Verificar si hay token de autenticación
    if (authToken) {
        const userType = localStorage.getItem('userType') || 'admin';
        const storedUser = localStorage.getItem('currentUser');
        if (storedUser && storedUser !== 'undefined' && storedUser !== 'null') {
            try {
                currentUser = JSON.parse(storedUser);
            } catch (error) {
                console.error('Error parsing currentUser from localStorage:', error);
                currentUser = null;
            }
        }
        showMainApp(userType);
        if (userType === 'cliente') {
            // Redirigir a la página del cliente
            window.location.href = '/static/cliente.html';
        } else {
            loadDashboard();
        }
    } else {
        showLoginScreen();
    }
    
    // Event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Login type change
    document.querySelectorAll('input[name="loginType"]').forEach(radio => {
        radio.addEventListener('change', handleLoginTypeChange);
    });
    
    // Navigation buttons
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const section = this.dataset.section;
            showSection(section);
        });
    });
    
    // Modal forms
    setupModalForms();
    
    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });
}

function setupModalForms() {
    // Cliente form
    const clienteForm = document.getElementById('clienteForm');
    if (clienteForm) {
        clienteForm.addEventListener('submit', handleClienteSubmit);
    }
    
    // Promoción form
    const promocionForm = document.getElementById('promocionForm');
    if (promocionForm) {
        promocionForm.addEventListener('submit', handlePromocionSubmit);
    }
    
    // Transacción form
    const transaccionForm = document.getElementById('transaccionForm');
    if (transaccionForm) {
        transaccionForm.addEventListener('submit', handleTransaccionSubmit);
    }
    
    // Ticket form
    const ticketForm = document.getElementById('ticketForm');
    if (ticketForm) {
        ticketForm.addEventListener('submit', handleTicketSubmit);
    }
    
    // Cliente ticket form
    const clienteTicketForm = document.getElementById('clienteTicketForm');
    if (clienteTicketForm) {
        clienteTicketForm.addEventListener('submit', handleClienteTicketSubmit);
    }
 }

// Nota: Las funciones específicas del cliente se han movido a cliente.js para evitar duplicación

function handleLoginTypeChange(e) {
    const loginType = e.target.value;
    const passwordGroup = document.getElementById('passwordGroup');
    const usernameLabel = document.getElementById('usernameLabel');
    const usernameIcon = document.getElementById('usernameIcon');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    if (loginType === 'cliente') {
        passwordGroup.style.display = 'none';
        passwordInput.required = false;
        usernameLabel.textContent = 'Número de Documento';
        usernameIcon.className = 'fas fa-id-card';
        usernameInput.placeholder = 'Ingrese su número de documento';
    } else {
        passwordGroup.style.display = 'block';
        passwordInput.required = true;
        usernameLabel.textContent = 'Usuario';
        usernameIcon.className = 'fas fa-user';
        usernameInput.placeholder = 'Ingrese su usuario';
    }
}

// Autenticación
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginType = formData.get('loginType');
    const username = formData.get('username');
    const password = formData.get('password');
    
    let endpoint, credentials;
    
    if (loginType === 'cliente') {
         endpoint = '/auth/cliente-login';
         credentials = {
             numero_documento: username
         };
     } else {
        endpoint = '/auth/login';
        credentials = {
            username: username,
            password: password
        };
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            authToken = data.data.access_token;
            currentUser = loginType === 'cliente' ? data.data.cliente : data.data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userType', loginType);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            const welcomeMessage = loginType === 'cliente' 
                 ? `Bienvenido ${currentUser.nombre_completo}`
                 : 'Bienvenido al sistema';
            
            showToast(welcomeMessage, 'success');
            showMainApp(loginType);
            if (loginType !== 'cliente') {
                loadDashboard();
            }
        } else {
            showToast(data.message || 'Error de autenticación', 'error');
        }
    } catch (error) {
        console.error('Error de login:', error);
        showToast('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

// Nota: loadClienteDashboard se ha movido a cliente.js para evitar duplicación

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userType');
    localStorage.removeItem('currentUser');
    showLoginScreen();
    showToast('Sesión cerrada correctamente', 'info');
}

// Funciones para las pestañas de login/registro
function showLoginTab() {
    document.getElementById('loginForm').classList.add('active');
    document.getElementById('registerForm').classList.remove('active');
    
    const tabs = document.querySelectorAll('.tab-btn');
    tabs[0].classList.add('active');
    tabs[1].classList.remove('active');
}

function showRegisterTab() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('registerForm').classList.add('active');
    
    const tabs = document.querySelectorAll('.tab-btn');
    tabs[0].classList.remove('active');
    tabs[1].classList.add('active');
}

// Manejo del registro de clientes
async function handleRegister(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const clienteData = {
        tipo_documento: formData.get('tipo_documento'),
        numero_documento: formData.get('numero_documento'),
        nombres: formData.get('nombres'),
        apellidos: formData.get('apellidos'),
        email: formData.get('email') || null,
        telefono: formData.get('telefono') || null,
        fecha_nacimiento: formData.get('fecha_nacimiento') || null,
        direccion: formData.get('direccion') || null,
        ciudad: formData.get('ciudad') || null
    };
    
    // Validaciones básicas
    if (!clienteData.numero_documento || clienteData.numero_documento.length < 6) {
        showToast('El número de documento debe tener al menos 6 caracteres', 'error');
        return;
    }
    
    if (!clienteData.nombres || !clienteData.apellidos) {
        showToast('Nombres y apellidos son obligatorios', 'error');
        return;
    }
    
    // Validar edad mínima si se proporciona fecha de nacimiento
    if (clienteData.fecha_nacimiento) {
        const fechaNac = new Date(clienteData.fecha_nacimiento);
        const hoy = new Date();
        const edad = hoy.getFullYear() - fechaNac.getFullYear();
        
        if (edad < 18) {
            showToast('Debe ser mayor de 18 años para registrarse', 'error');
            return;
        }
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/registro`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clienteData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast(data.message, 'success');
            
            // Mostrar información del cliente registrado
            const clienteInfo = data.data;
            showToast(`Cliente registrado: ${clienteInfo.nombre_completo} (ID: ${clienteInfo.cliente_id})`, 'info');
            
            // Limpiar formulario
            e.target.reset();
            
            // Cambiar a pestaña de login
            showLoginTab();
            
        } else {
            // Manejar errores específicos
            let errorMessage = data.message || 'Error en el registro';
            
            // Si es un error de cliente duplicado, mostrar mensaje más específico
            if (errorMessage.includes('Ya existe un cliente con este número de documento')) {
                errorMessage = `Ya existe un cliente registrado con el documento ${clienteData.numero_documento}. Si eres tú, puedes iniciar sesión directamente.`;
                
                // Mostrar botón para ir al login
                setTimeout(() => {
                    if (confirm('¿Deseas ir a la pantalla de inicio de sesión?')) {
                        showLoginTab();
                        // Pre-llenar el número de documento en el login
                        const loginDocumento = document.querySelector('#loginForm input[name="numero_documento"]');
                        if (loginDocumento) {
                            loginDocumento.value = clienteData.numero_documento;
                        }
                    }
                }, 2000);
            }
            
            showToast(errorMessage, 'error');
        }
    } catch (error) {
        console.error('Error de registro:', error);
        showToast('Error de conexión durante el registro', 'error');
    } finally {
        showLoading(false);
    }
}

// Navegación
function showLoginScreen() {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

function showMainApp(userType = 'admin') {
    if (userType === 'cliente') {
        // Redirigir a la interfaz específica de cliente
        window.location.href = 'cliente.html';
        return;
    }
    
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('mainApp').style.display = 'flex';
    
    // Mostrar elementos de admin
    const adminElements = document.querySelectorAll('.admin-only');
    const clienteElements = document.querySelectorAll('.cliente-only');
    const navButtons = document.querySelectorAll('.nav-btn');
    
    adminElements.forEach(el => el.style.display = 'block');
    clienteElements.forEach(el => el.style.display = 'none');
    
    // Mostrar todos los botones de navegación
    navButtons.forEach(btn => btn.style.display = 'block');
    
    // Ocultar la vista del cliente
    const clienteView = document.getElementById('clienteView');
    if (clienteView) {
        clienteView.classList.remove('active');
    }
    
    // Mostrar dashboard de admin
    showSection('dashboard');
}

function showSection(sectionName) {
    // Ocultar todas las secciones
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Mostrar la sección seleccionada
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Actualizar navegación
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.section === sectionName) {
            btn.classList.add('active');
        }
    });
    
    // Cargar datos específicos de la sección
    loadSectionData(sectionName);
}

function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'clientes':
            loadClientes();
            break;
        case 'promociones':
            loadPromociones();
            break;
        case 'transacciones':
            loadTransacciones();
            break;
        case 'tickets':
            loadTickets();
            break;
        case 'reportes':
            // Los reportes se cargan bajo demanda
            break;
    }
}

// Dashboard
async function loadDashboard() {
    showLoading(true);
    
    try {
        const response = await apiRequest('/estadisticas/dashboard');
        
        if (response.success) {
            const stats = response.data;
            const clientesStats = stats.clientes || {};
            const ticketsStats = stats.tickets || {};
            
            // Actualizar estadísticas de clientes
            document.getElementById('totalClientes').textContent = clientesStats.total_clientes || 0;
            document.getElementById('clientesActivos').textContent = clientesStats.clientes_activos || 0;
            document.getElementById('clientesVip').textContent = clientesStats.clientes_vip || 0;
            document.getElementById('promedioGastado').textContent = `$${formatNumber(clientesStats.promedio_gastado || 0)}`;
            document.getElementById('totalPuntos').textContent = formatNumber(clientesStats.total_puntos || 0);
            
            // Actualizar estadísticas de tickets
            document.getElementById('ticketsAbiertos').textContent = ticketsStats.tickets_abiertos || 0;
        }
    } catch (error) {
        console.error('Error cargando dashboard:', error);
        showToast('Error cargando estadísticas', 'error');
    } finally {
        showLoading(false);
    }
}

// Gestión de Clientes
async function loadClientes() {
    showLoading(true);
    
    try {
        const response = await apiRequest('/clientes/');
        
        if (response.success) {
            renderClientesTable(response.data);
        }
    } catch (error) {
        console.error('Error cargando clientes:', error);
        showToast('Error cargando clientes', 'error');
    } finally {
        showLoading(false);
    }
}

function renderClientesTable(clientes) {
    const tbody = document.querySelector('#tablaClientes tbody');
    tbody.innerHTML = '';
    
    clientes.forEach(cliente => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${cliente.id}</td>
            <td>${cliente.numero_documento}</td>
            <td>${cliente.nombres} ${cliente.apellidos}</td>
            <td>${cliente.email || 'N/A'}</td>
            <td><span class="badge ${cliente.tipo_cliente}">${cliente.tipo_cliente}</span></td>
            <td>${cliente.total_visitas}</td>
            <td>$${formatNumber(cliente.total_gastado)}</td>
            <td>${formatNumber(cliente.puntos_acumulados)}</td>
            <td><span class="badge ${cliente.activo ? 'activo' : 'inactivo'}">${cliente.activo ? 'Activo' : 'Inactivo'}</span></td>
            <td>
                <button class="btn-secondary" onclick="editCliente(${cliente.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showClienteModal(clienteId = null) {
    const modal = document.getElementById('clienteModal');
    const form = document.getElementById('clienteForm');
    const title = document.getElementById('clienteModalTitle');
    
    if (clienteId) {
        title.textContent = 'Editar Cliente';
        // Cargar datos del cliente para edición
        loadClienteData(clienteId);
    } else {
        title.textContent = 'Nuevo Cliente';
        form.reset();
    }
    
    modal.classList.add('show');
}

async function handleClienteSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const clienteData = {
        tipo_documento: formData.get('tipo_documento'),
        numero_documento: formData.get('numero_documento'),
        nombres: formData.get('nombres'),
        apellidos: formData.get('apellidos'),
        email: formData.get('email'),
        telefono: formData.get('telefono'),
        fecha_nacimiento: formData.get('fecha_nacimiento'),
        ciudad: formData.get('ciudad'),
        direccion: formData.get('direccion')
    };
    
    showLoading(true);
    
    try {
        const response = await apiRequest('/clientes/', {
            method: 'POST',
            body: JSON.stringify(clienteData)
        });
        
        if (response.success) {
            showToast('Cliente creado exitosamente', 'success');
            closeModal('clienteModal');
            loadClientes();
        } else {
            showToast(response.message || 'Error creando cliente', 'error');
        }
    } catch (error) {
        console.error('Error creando cliente:', error);
        showToast('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

function filtrarClientes() {
    const tipo = document.getElementById('filtroTipoCliente').value;
    const estado = document.getElementById('filtroEstadoCliente').value;
    const ciudad = document.getElementById('filtroCiudad').value;
    
    let url = '/clientes/?';
    const params = [];
    
    if (tipo) params.push(`tipo=${tipo}`);
    if (estado) params.push(`activo=${estado}`);
    if (ciudad) params.push(`ciudad=${encodeURIComponent(ciudad)}`);
    
    url += params.join('&');
    
    loadClientesWithFilter(url);
}

async function loadClientesWithFilter(url) {
    showLoading(true);
    
    try {
        const response = await apiRequest(url);
        
        if (response.success) {
            renderClientesTable(response.data);
        }
    } catch (error) {
        console.error('Error filtrando clientes:', error);
        showToast('Error aplicando filtros', 'error');
    } finally {
        showLoading(false);
    }
}

// Gestión de Promociones
async function loadPromociones() {
    showLoading(true);
    
    try {
        const response = await apiRequest('/promociones/activas');
        
        if (response.success) {
            renderPromocionesGrid(response.data);
        }
    } catch (error) {
        console.error('Error cargando promociones:', error);
        showToast('Error cargando promociones', 'error');
    } finally {
        showLoading(false);
    }
}

function renderPromocionesGrid(promociones) {
    const grid = document.getElementById('promocionesGrid');
    grid.innerHTML = '';
    
    promociones.forEach(promocion => {
        const card = document.createElement('div');
        card.className = 'promocion-card';
        card.innerHTML = `
            <div class="promocion-header">
                <h3 class="promocion-title">${promocion.titulo}</h3>
                <span class="promocion-tipo">${promocion.tipo}</span>
            </div>
            <div class="promocion-content">
                <p>${promocion.descripcion || 'Sin descripción'}</p>
                <p><strong>Valor:</strong> ${promocion.valor}</p>
                <p><strong>Condiciones:</strong> ${promocion.condiciones || 'Sin condiciones especiales'}</p>
            </div>
            <div class="promocion-meta">
                <span>Usos: ${promocion.usos_actuales}/${promocion.usos_maximos}</span>
                <span>Válida hasta: ${formatDate(promocion.fecha_fin)}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function showPromocionModal() {
    const modal = document.getElementById('promocionModal');
    const form = document.getElementById('promocionForm');
    
    form.reset();
    
    // Establecer fechas por defecto
    const now = new Date();
    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    
    document.getElementById('fechaInicioPromocion').value = tomorrow.toISOString().slice(0, 16);
    document.getElementById('fechaFinPromocion').value = nextWeek.toISOString().slice(0, 16);
    
    modal.classList.add('show');
}

async function handlePromocionSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const promocionData = {
        titulo: formData.get('titulo'),
        descripcion: formData.get('descripcion'),
        tipo: formData.get('tipo'),
        valor: parseFloat(formData.get('valor')),
        fecha_inicio: formData.get('fecha_inicio'),
        fecha_fin: formData.get('fecha_fin'),
        cliente_id: formData.get('cliente_id') ? parseInt(formData.get('cliente_id')) : null,
        usos_maximos: parseInt(formData.get('usos_maximos')),
        condiciones: formData.get('condiciones')
    };
    
    showLoading(true);
    
    try {
        const response = await apiRequest('/promociones/', {
            method: 'POST',
            body: JSON.stringify(promocionData)
        });
        
        if (response.success) {
            showToast('Promoción creada exitosamente', 'success');
            closeModal('promocionModal');
            loadPromociones();
        } else {
            showToast(response.message || 'Error creando promoción', 'error');
        }
    } catch (error) {
        console.error('Error creando promoción:', error);
        showToast('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

// Gestión de Transacciones
async function loadTransacciones() {
    await cargarTransacciones();
}

async function cargarTransacciones() {
    const clienteId = document.getElementById('filtroClienteId').value;
    
    showLoading(true);
    
    try {
        let response;
        if (clienteId) {
            // Si hay un cliente específico, filtrar por ese cliente
            response = await apiRequest(`/transacciones/cliente/${clienteId}`);
        } else {
            // Si no hay cliente específico, mostrar todas las transacciones
            response = await apiRequest('/transacciones');
        }
        
        if (response.success) {
            renderTransaccionesTable(response.data);
        }
    } catch (error) {
        console.error('Error cargando transacciones:', error);
        showToast('Error cargando transacciones', 'error');
    } finally {
        showLoading(false);
    }
}

function renderTransaccionesTable(transacciones) {
    const tbody = document.querySelector('#tablaTransacciones tbody');
    tbody.innerHTML = '';
    
    if (transacciones.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No se encontraron transacciones</td></tr>';
        return;
    }
    
    transacciones.forEach(transaccion => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaccion.id}</td>
            <td><span class="badge ${transaccion.tipo}">${transaccion.tipo}</span></td>
            <td>$${formatNumber(transaccion.monto)}</td>
            <td>${transaccion.descripcion || 'N/A'}</td>
            <td>${formatDateTime(transaccion.fecha_transaccion)}</td>
            <td>${transaccion.ubicacion || 'N/A'}</td>
            <td>${transaccion.puntos_ganados || 0}</td>
            <td>${transaccion.metodo_pago || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });
}

function showTransaccionModal() {
    const modal = document.getElementById('transaccionModal');
    const form = document.getElementById('transaccionForm');
    
    form.reset();
    modal.classList.add('show');
}

async function handleTransaccionSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const transaccionData = {
        cliente_id: parseInt(formData.get('cliente_id')),
        tipo: formData.get('tipo'),
        monto: parseFloat(formData.get('monto')),
        descripcion: formData.get('descripcion'),
        ubicacion: formData.get('ubicacion'),
        numero_referencia: formData.get('numero_referencia'),
        metodo_pago: formData.get('metodo_pago')
    };
    
    showLoading(true);
    
    try {
        const response = await apiRequest('/transacciones/', {
            method: 'POST',
            body: JSON.stringify(transaccionData)
        });
        
        if (response.success) {
            showToast('Transacción registrada exitosamente', 'success');
            closeModal('transaccionModal');
            
            // Recargar todas las transacciones
            cargarTransacciones();
        } else {
            showToast(response.message || 'Error registrando transacción', 'error');
        }
    } catch (error) {
        console.error('Error registrando transacción:', error);
        showToast('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

// Gestión de Tickets
async function loadTickets() {
    showLoading(true);
    
    try {
        const response = await apiRequest('/tickets/abiertos');
        
        if (response.success) {
            renderTicketsGrid(response.data);
        }
    } catch (error) {
        console.error('Error cargando tickets:', error);
        showToast('Error cargando tickets', 'error');
    } finally {
        showLoading(false);
    }
}

function renderTicketsGrid(tickets) {
    const grid = document.getElementById('ticketsGrid');
    grid.innerHTML = '';
    
    if (tickets.length === 0) {
        grid.innerHTML = '<p class="text-center text-muted">No hay tickets abiertos</p>';
        return;
    }
    
    tickets.forEach(ticket => {
        const card = document.createElement('div');
        card.className = 'ticket-card';
        card.innerHTML = `
            <div class="ticket-header">
                <span class="ticket-id">#${ticket.id}</span>
                <span class="ticket-priority ${ticket.prioridad}">${ticket.prioridad}</span>
            </div>
            <div class="ticket-content">
                <div class="ticket-asunto">${ticket.asunto}</div>
                <div class="ticket-descripcion">${ticket.descripcion}</div>
            </div>
            <div class="ticket-meta">
                <span>Cliente: ${ticket.cliente_id}</span>
                <span>Tipo: ${ticket.tipo}</span>
                <span>${formatDateTime(ticket.fecha_creacion)}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function showTicketModal() {
    const modal = document.getElementById('ticketModal');
    const form = document.getElementById('ticketForm');
    
    form.reset();
    modal.classList.add('show');
}

async function handleTicketSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const ticketData = {
        cliente_id: parseInt(formData.get('cliente_id')),
        tipo: formData.get('tipo'),
        prioridad: formData.get('prioridad'),
        categoria: formData.get('categoria'),
        asunto: formData.get('asunto'),
        descripcion: formData.get('descripcion')
    };
    
    showLoading(true);
    
    try {
        const response = await apiRequest('/tickets/', {
            method: 'POST',
            body: JSON.stringify(ticketData)
        });
        
        if (response.success) {
            showToast('Ticket creado exitosamente', 'success');
            closeModal('ticketModal');
            loadTickets();
        } else {
            showToast(response.message || 'Error creando ticket', 'error');
        }
    } catch (error) {
        console.error('Error creando ticket:', error);
        showToast('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

// Función para manejar el envío de tickets del cliente
async function handleClienteTicketSubmit(event) {
    event.preventDefault();
    
    // Verificar que currentUser existe
    if (!currentUser || !currentUser.id) {
        console.error('currentUser no está definido para enviar ticket');
        showToast('Error: Usuario no identificado', 'error');
        return;
    }
    
    const formData = new FormData(event.target);
    const ticketData = {
        cliente_id: currentUser.id,
        asunto: formData.get('asunto'),
        categoria: formData.get('categoria'),
        descripcion: formData.get('descripcion'),
        tipo: 'consulta',
        prioridad: 'media'
    };
    
    showLoading(true);
    
    try {
        const response = await apiRequest('/tickets/', {
            method: 'POST',
            body: JSON.stringify(ticketData)
        });
        
        if (response.success) {
            showToast('Consulta enviada exitosamente', 'success');
            event.target.reset();
            loadClienteTickets(); // Recargar tickets
        } else {
            showToast(response.message || 'Error al enviar consulta', 'error');
        }
    } catch (error) {
        console.error('Error al enviar ticket:', error);
        showToast('Error al enviar consulta', 'error');
    } finally {
        showLoading(false);
    }
}

// Reportes
async function generarReporteClientes() {
    showLoading(true);
    
    try {
        const response = await apiRequest('/reportes/clientes', {
            method: 'POST',
            body: JSON.stringify({
                formato: 'excel',
                incluir_inactivos: true
            })
        });
        
        if (response.success) {
            showToast('Reporte generado exitosamente', 'success');
            // Aquí podrías descargar el archivo o mostrar un enlace
        }
    } catch (error) {
        console.error('Error generando reporte:', error);
        showToast('Error generando reporte', 'error');
    } finally {
        showLoading(false);
    }
}

async function generarReporteTransacciones() {
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    
    if (!fechaInicio || !fechaFin) {
        showToast('Seleccione el rango de fechas', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await apiRequest('/reportes/transacciones', {
            method: 'POST',
            body: JSON.stringify({
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin,
                formato: 'excel'
            })
        });
        
        if (response.success) {
            showToast('Reporte generado exitosamente', 'success');
        }
    } catch (error) {
        console.error('Error generando reporte:', error);
        showToast('Error generando reporte', 'error');
    } finally {
        showLoading(false);
    }
}

// Utilidades
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    if (options.headers) {
        finalOptions.headers = { ...defaultOptions.headers, ...options.headers };
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, finalOptions);
    
    if (response.status === 401) {
        // Token expirado o inválido
        logout();
        throw new Error('Sesión expirada');
    }
    
    return await response.json();
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

function showToast(message, type = 'info', title = '') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="${icons[type] || icons.info}"></i>
        </div>
        <div class="toast-content">
            ${title ? `<div class="toast-title">${title}</div>` : ''}
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
}

function formatNumber(number) {
    return new Intl.NumberFormat('es-CO').format(number);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO');
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-CO');
}

// Funciones específicas para edición (placeholders)
function editCliente(clienteId) {
    showClienteModal(clienteId);
}

async function loadClienteData(clienteId) {
    try {
        const response = await apiRequest(`/clientes/${clienteId}`);
        
        if (response.success) {
            const cliente = response.data;
            
            // Llenar el formulario con los datos del cliente
            document.getElementById('tipoDocumento').value = cliente.tipo_documento;
            document.getElementById('numeroDocumento').value = cliente.numero_documento;
            document.getElementById('nombres').value = cliente.nombres;
            document.getElementById('apellidos').value = cliente.apellidos;
            document.getElementById('email').value = cliente.email || '';
            document.getElementById('telefono').value = cliente.telefono || '';
            document.getElementById('fechaNacimiento').value = cliente.fecha_nacimiento || '';
            document.getElementById('ciudad').value = cliente.ciudad || '';
            document.getElementById('direccion').value = cliente.direccion || '';
        }
    } catch (error) {
        console.error('Error cargando datos del cliente:', error);
        showToast('Error cargando datos del cliente', 'error');
    }
}

// Inicializar fechas por defecto en reportes
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    
    const fechaInicioInput = document.getElementById('fechaInicio');
    const fechaFinInput = document.getElementById('fechaFin');
    
    if (fechaInicioInput) {
        fechaInicioInput.value = firstDay.toISOString().split('T')[0];
    }
    
    if (fechaFinInput) {
        fechaFinInput.value = today.toISOString().split('T')[0];
    }
});