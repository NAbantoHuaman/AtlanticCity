// Cliente Dashboard JavaScript

// ===== CONSTANTES =====
const API_BASE_URL = 'http://localhost:8001';
const ROUTES = {
    LOGIN: '/static/index.html',
    CLIENT_DATA: (id) => `/clientes/${id}`,
    PROMOTIONS: (id) => `/promociones/activas?cliente_id=${id}`,
    TRANSACTIONS: (id) => `/transacciones/cliente/${id}`,
    TICKETS: (id) => `/tickets/cliente/${id}`,
    CREATE_TRANSACTION: '/transacciones',
    CREATE_TICKET: '/tickets',
    CLAIM_PROMOTION: (code, id) => `/promociones/${code}/canjear?cliente_id=${id}`
};

const STORAGE_KEYS = {
    USER: 'currentUser',
    USER_TYPE: 'userType',
    AUTH_TOKEN: 'authToken'
};

const TOAST_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
};

const MODAL_CONFIG = {
    backdrop: 'static',
    keyboard: false
};

const VALIDATION = {
    MIN_RECHARGE: 10,
    MAX_RECHARGE: 1000,
    MODAL_CLEANUP_DELAY: 150
};

// ===== VARIABLES GLOBALES =====
let currentUser = null;

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    initializeClientApp();
});

// ===== FUNCIONES DE AUTENTICACIÓN =====
function initializeClientApp() {
    const storedUser = getStorageItem(STORAGE_KEYS.USER);
    const userType = getStorageItem(STORAGE_KEYS.USER_TYPE);
    
    if (!isValidStoredUser(storedUser)) {
        redirectToLogin();
        return;
    }
    
    try {
        currentUser = JSON.parse(storedUser);
        if (!isValidUser(currentUser)) {
            redirectToLogin();
            return;
        }
        
        if (!isClientUser(userType)) {
            showToast('Acceso denegado. Esta área es solo para clientes.', TOAST_TYPES.ERROR);
            redirectToLogin();
            return;
        }
        
        loadClientDashboard();
    } catch (error) {
        console.error('Error al parsear usuario:', error);
        redirectToLogin();
    }
}

function redirectToLogin() {
    clearUserData();
    window.location.href = ROUTES.LOGIN;
}

function logout() {
    clearUserData();
    showToast('Sesión cerrada exitosamente', TOAST_TYPES.SUCCESS);
    setTimeout(() => {
        window.location.href = ROUTES.LOGIN;
    }, 1000);
}

// ===== FUNCIONES AUXILIARES DE AUTENTICACIÓN =====
function getStorageItem(key) {
    return localStorage.getItem(key);
}

function isValidStoredUser(storedUser) {
    return storedUser && storedUser !== 'undefined' && storedUser !== 'null';
}

function isValidUser(user) {
    return user && user.id;
}

function isClientUser(userType) {
    return userType === 'cliente';
}

function clearUserData() {
    Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
    });
}

function getAuthHeaders() {
    const token = getStorageItem(STORAGE_KEYS.AUTH_TOKEN);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ===== FUNCIONES DE CARGA DE DATOS =====
async function loadClientDashboard() {
    if (!isValidUser(currentUser)) {
        redirectToLogin();
        return;
    }
    
    try {
        updateWelcomeMessage();
        await Promise.all([
            loadClientData(),
            loadGames(),
            loadPromotions()
        ]);
        showGamesSection();
    } catch (error) {
        console.error('Error al cargar dashboard:', error);
        showToast('Error al cargar el dashboard', TOAST_TYPES.ERROR);
    }
}

function updateWelcomeMessage() {
    const welcomeElement = document.getElementById('welcomeMessage');
    if (welcomeElement) {
        welcomeElement.textContent = `Bienvenido, ${currentUser.nombre || 'Cliente'}`;
    }
}

async function loadClientData() {
    try {
        const response = await makeApiRequest(ROUTES.CLIENT_DATA(currentUser.id));
        if (response.ok) {
            const result = await response.json();
            updateClientDataDisplay(result.data);
        } else {
            console.error('Error response:', response.status, response.statusText);
            setDefaultClientData();
        }
    } catch (error) {
        console.error('Error al cargar datos del cliente:', error);
        setDefaultClientData();
    }
}

function updateClientDataDisplay(clientData) {
    const balance = clientData.saldo || 0;
    const points = clientData.puntos_acumulados || 0;
    
    updateElementText('userBalance', `$${balance.toFixed(2)}`);
    updateElementText('userPoints', `${points} puntos disponibles`);
}

function setDefaultClientData() {
    updateElementText('userBalance', '$0.00');
    updateElementText('userPoints', '0 puntos disponibles');
}

function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

async function makeApiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
        }
    };
    
    return fetch(`${API_BASE_URL}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });
}

// Navegación entre secciones
function showSection(sectionId) {
    // Ocultar todas las secciones
    const sections = document.querySelectorAll('.section-content');
    sections.forEach(section => section.style.display = 'none');
    
    // Mostrar la sección seleccionada
    document.getElementById(sectionId).style.display = 'block';
}

function showGamesSection() {
    showSection('gamesSection');
}

function showPromotionsSection() {
    showSection('promotionsSection');
}

function showTransactionsSection() {
    showSection('transactionsSection');
    loadTransactions();
}

function showSupportSection() {
    showSection('supportSection');
    loadUserTickets();
}

// Cargar juegos
async function loadGames() {
    const gamesList = document.getElementById('gamesList');
    
    // Juegos simulados (puedes conectar con una API real)
    const games = [
        { id: 1, name: 'Blackjack', description: 'Juego clásico de cartas', image: 'fas fa-spade', minBet: 5 },
        { id: 2, name: 'Ruleta', description: 'Ruleta europea', image: 'fas fa-circle-notch', minBet: 1 },
        { id: 3, name: 'Poker', description: 'Texas Hold\'em', image: 'fas fa-heart', minBet: 10 },
        { id: 4, name: 'Slots', description: 'Máquinas tragamonedas', image: 'fas fa-coins', minBet: 0.25 },
        { id: 5, name: 'Baccarat', description: 'Juego de cartas elegante', image: 'fas fa-diamond', minBet: 25 },
        { id: 6, name: 'Craps', description: 'Juego de dados', image: 'fas fa-dice', minBet: 5 }
    ];
    
    gamesList.innerHTML = games.map(game => `
        <div class="col-md-4 mb-3">
            <div class="card game-card h-100" onclick="playGame(${game.id}, '${game.name}')">
                <div class="card-body text-center">
                    <i class="${game.image} fa-3x mb-3 text-primary"></i>
                    <h5 class="card-title">${game.name}</h5>
                    <p class="card-text">${game.description}</p>
                    <small class="text-muted">Apuesta mínima: $${game.minBet}</small>
                </div>
            </div>
        </div>
    `).join('');
}

async function loadPromotions() {
    try {
        const response = await makeApiRequest(ROUTES.PROMOTIONS(currentUser.id));
        if (response.ok) {
            const result = await response.json();
            renderPromotions(result.data);
        } else {
            renderPromotionsError();
        }
    } catch (error) {
        console.error('Error al cargar promociones:', error);
        renderPromotionsError();
    }
}

function renderPromotions(promotions) {
    const promotionsList = document.getElementById('promotionsList');
    if (!promotionsList) return;
    
    if (promotions.length === 0) {
        promotionsList.innerHTML = '<div class="col-12"><p class="text-center text-muted">No hay promociones activas en este momento.</p></div>';
        return;
    }
    
    promotionsList.innerHTML = promotions.map(promo => createPromotionCard(promo)).join('');
}

function createPromotionCard(promo) {
    return `
        <div class="col-md-6 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${promo.titulo}</h5>
                    <p class="card-text">${promo.descripcion}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">Válido hasta: ${new Date(promo.fecha_fin).toLocaleDateString()}</small>
                        <button class="btn btn-primary btn-sm" onclick="claimPromotion('${promo.codigo}')">
                            <i class="fas fa-gift"></i> Reclamar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderPromotionsError() {
    const promotionsList = document.getElementById('promotionsList');
    if (promotionsList) {
        promotionsList.innerHTML = '<div class="col-12"><p class="text-center text-danger">Error al cargar promociones.</p></div>';
    }
}

async function loadTransactions() {
    try {
        const response = await makeApiRequest(ROUTES.TRANSACTIONS(currentUser.id));
        if (response.ok) {
            const result = await response.json();
            renderTransactions(result.data);
        } else {
            renderTransactionsError();
        }
    } catch (error) {
        console.error('Error al cargar transacciones:', error);
        renderTransactionsError();
    }
}

function renderTransactions(transactions) {
    const transactionsTable = document.getElementById('transactionsTable');
    if (!transactionsTable) return;
    
    if (transactions.length === 0) {
        transactionsTable.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No hay transacciones registradas.</td></tr>';
        return;
    }
    
    transactionsTable.innerHTML = transactions.map(transaction => createTransactionRow(transaction)).join('');
}

function createTransactionRow(transaction) {
    const typeClass = transaction.tipo === 'deposito' ? 'success' : 'primary';
    const typeText = transaction.tipo.charAt(0).toUpperCase() + transaction.tipo.slice(1);
    
    return `
        <tr>
            <td>${new Date(transaction.fecha_transaccion).toLocaleDateString()}</td>
            <td>
                <span class="badge bg-${typeClass}">
                    ${typeText}
                </span>
            </td>
            <td>$${transaction.monto.toFixed(2)}</td>
            <td>
                <span class="badge bg-success">Completado</span>
            </td>
        </tr>
    `;
}

function renderTransactionsError() {
    const transactionsTable = document.getElementById('transactionsTable');
    if (transactionsTable) {
        transactionsTable.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error al cargar transacciones.</td></tr>';
    }
}

// Cargar tickets del usuario
async function loadUserTickets() {
    try {
        const response = await makeApiRequest(ROUTES.TICKETS(currentUser.id));
        if (response.ok) {
            const result = await response.json();
            renderUserTickets(result.data);
        } else {
            renderUserTicketsError();
        }
    } catch (error) {
        console.error('Error al cargar tickets:', error);
        renderUserTicketsError();
    }
}

function renderUserTickets(tickets) {
    const userTickets = document.getElementById('userTickets');
    if (!userTickets) return;
    
    if (tickets.length === 0) {
        userTickets.innerHTML = '<p class="text-muted">No tienes tickets de soporte.</p>';
        return;
    }
    
    userTickets.innerHTML = tickets.map(ticket => createUserTicketCard(ticket)).join('');
}

function createUserTicketCard(ticket) {
    const statusClass = ticket.estado === 'abierto' ? 'warning' : 'success';
    const statusText = ticket.estado.charAt(0).toUpperCase() + ticket.estado.slice(1);
    
    return `
        <div class="card mb-2">
            <div class="card-body p-2">
                <h6 class="card-title mb-1">${ticket.asunto}</h6>
                <small class="text-muted">${ticket.categoria}</small>
                <div class="mt-1">
                    <span class="badge bg-${statusClass} text-dark">
                        ${statusText}
                    </span>
                </div>
            </div>
        </div>
    `;
}

function renderUserTicketsError() {
    const userTickets = document.getElementById('userTickets');
    if (userTickets) {
        userTickets.innerHTML = '<p class="text-danger">Error al cargar tickets.</p>';
    }
}

// Funciones de interacción
function playGame(gameId, gameName) {
    openGameModal(gameId, gameName);
}

// Modal de juego
function openGameModal(gameId, gameName) {
    const modal = document.getElementById('gameModal');
    const gameTitle = document.getElementById('gameTitle');
    const gameContent = document.getElementById('gameContent');
    
    if (!modal) {
        createGameModal();
        return openGameModal(gameId, gameName);
    }
    
    gameTitle.textContent = gameName;
    gameContent.innerHTML = createGameInterface(gameId, gameName);
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeGameModal() {
    const modal = document.getElementById('gameModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

function createGameModal() {
    const modalHTML = `
        <div id="gameModal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); align-items: center; justify-content: center;">
            <div class="modal-content" style="background: white; padding: 20px; border-radius: 10px; max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;">
                <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 id="gameTitle">Juego</h3>
                    <button onclick="closeGameModal()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
                </div>
                <div id="gameContent"></div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function createGameInterface(gameId, gameName) {
    const games = {
        1: createBlackjackInterface,
        2: createRouletteInterface,
        3: createPokerInterface,
        4: createSlotsInterface,
        5: createBaccaratInterface,
        6: createCrapsInterface
    };
    
    return games[gameId] ? games[gameId]() : createDefaultGameInterface(gameName);
}

function createDefaultGameInterface(gameName) {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="1" max="${currentUser.saldo_actual || 0}" step="0.01" placeholder="Ingrese su apuesta">
            </div>
            <button class="btn btn-primary" onclick="playSimpleGame('${gameName}')">Jugar</button>
        </div>
    `;
}

function createBlackjackInterface() {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="5" max="${currentUser.saldo_actual || 0}" step="0.01" placeholder="Mínimo $5">
            </div>
            <div id="gameArea" class="mb-3" style="min-height: 200px;">
                <p>¡Bienvenido al Blackjack! El objetivo es llegar lo más cerca posible a 21 sin pasarse.</p>
            </div>
            <button class="btn btn-primary" onclick="startBlackjack()">Iniciar Juego</button>
        </div>
    `;
}

function createRouletteInterface() {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="1" max="${currentUser.saldo_actual || 0}" step="0.01" placeholder="Mínimo $1">
            </div>
            <div class="mb-3">
                <label>Tipo de apuesta:</label>
                <select id="betType" class="form-control">
                    <option value="red">Rojo (2x)</option>
                    <option value="black">Negro (2x)</option>
                    <option value="even">Par (2x)</option>
                    <option value="odd">Impar (2x)</option>
                    <option value="number">Número específico (36x)</option>
                </select>
            </div>
            <div id="numberBet" style="display: none;" class="mb-3">
                <input type="number" id="specificNumber" class="form-control" min="0" max="36" placeholder="Número (0-36)">
            </div>
            <button class="btn btn-primary" onclick="spinRoulette()">Girar Ruleta</button>
        </div>
    `;
}

function createSlotsInterface() {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="0.25" max="${currentUser.saldo_actual || 0}" step="0.25" placeholder="Mínimo $0.25">
            </div>
            <div id="slotsDisplay" class="mb-3" style="font-size: 48px; height: 100px; display: flex; justify-content: center; align-items: center; border: 2px solid #ddd; border-radius: 10px;">
                🎰 🎰 🎰
            </div>
            <p class="small text-muted">3 iguales = 10x | 2 iguales = 3x | 3 🍒 = 50x</p>
            <button class="btn btn-primary" onclick="spinSlots()">Girar</button>
        </div>
    `;
}

function createPokerInterface() {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="10" max="${currentUser.saldo_actual || 0}" step="1" placeholder="Mínimo $10">
            </div>
            <div id="pokerArea" class="mb-3" style="min-height: 150px; border: 2px solid #ddd; border-radius: 10px; padding: 20px;">
                <p>🃏 Texas Hold'em Poker 🃏</p>
                <p class="small text-muted">Obtén la mejor mano de 5 cartas</p>
            </div>
            <button class="btn btn-primary" onclick="playPoker()">Jugar Poker</button>
        </div>
    `;
}

function createBaccaratInterface() {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="25" max="${currentUser.saldo_actual || 0}" step="5" placeholder="Mínimo $25">
            </div>
            <div class="mb-3">
                <label>Apostar a:</label>
                <select id="baccaratBet" class="form-control">
                    <option value="player">Jugador (2x)</option>
                    <option value="banker">Banca (1.95x)</option>
                    <option value="tie">Empate (8x)</option>
                </select>
            </div>
            <div id="baccaratArea" class="mb-3" style="min-height: 100px;">
                <p>🎴 Juego de cartas elegante 🎴</p>
            </div>
            <button class="btn btn-primary" onclick="playBaccarat()">Jugar Baccarat</button>
        </div>
    `;
}

function createCrapsInterface() {
    return `
        <div class="game-interface text-center">
            <p>Saldo actual: <strong>$${currentUser.saldo_actual?.toFixed(2) || '0.00'}</strong></p>
            <div class="mb-3">
                <label>Cantidad a apostar:</label>
                <input type="number" id="betAmount" class="form-control" min="5" max="${currentUser.saldo_actual || 0}" step="1" placeholder="Mínimo $5">
            </div>
            <div class="mb-3">
                <label>Tipo de apuesta:</label>
                <select id="crapsBet" class="form-control">
                    <option value="pass">Pass Line (2x)</option>
                    <option value="dontpass">Don't Pass (2x)</option>
                    <option value="field">Field (2x)</option>
                    <option value="any7">Any 7 (4x)</option>
                </select>
            </div>
            <div id="crapsDisplay" class="mb-3" style="font-size: 36px; height: 80px; display: flex; justify-content: center; align-items: center;">
                🎲 🎲
            </div>
            <button class="btn btn-primary" onclick="rollDice()">Lanzar Dados</button>
        </div>
    `;
}

// Funciones de juego
async function playSimpleGame(gameName) {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    
    if (!validateBet(betAmount)) return;
    
    const winChance = 0.45; // 45% de probabilidad de ganar
    const isWin = Math.random() < winChance;
    const multiplier = isWin ? 2 : 0;
    
    await processBet(betAmount, multiplier, `${gameName} - ${isWin ? 'Ganaste' : 'Perdiste'}`);
}

async function startBlackjack() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    
    if (!validateBet(betAmount, 5)) return;
    
    const playerCard = Math.floor(Math.random() * 10) + 1;
    const dealerCard = Math.floor(Math.random() * 10) + 1;
    const playerTotal = playerCard + (Math.floor(Math.random() * 10) + 1);
    const dealerTotal = dealerCard + (Math.floor(Math.random() * 10) + 1);
    
    let result = '';
    let multiplier = 0;
    
    if (playerTotal > 21) {
        result = 'Te pasaste de 21. Perdiste.';
        multiplier = 0;
    } else if (dealerTotal > 21) {
        result = 'El dealer se pasó de 21. ¡Ganaste!';
        multiplier = 2;
    } else if (playerTotal > dealerTotal) {
        result = `Tu: ${playerTotal}, Dealer: ${dealerTotal}. ¡Ganaste!`;
        multiplier = 2;
    } else if (playerTotal === dealerTotal) {
        result = `Empate: ${playerTotal}. Recuperas tu apuesta.`;
        multiplier = 1;
    } else {
        result = `Tu: ${playerTotal}, Dealer: ${dealerTotal}. Perdiste.`;
        multiplier = 0;
    }
    
    document.getElementById('gameArea').innerHTML = `<div class="alert alert-info">${result}</div>`;
    
    await processBet(betAmount, multiplier, `Blackjack - ${result}`);
}

async function spinRoulette() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    const betType = document.getElementById('betType').value;
    const specificNumber = document.getElementById('specificNumber')?.value;
    
    if (!validateBet(betAmount, 1)) return;
    
    const winningNumber = Math.floor(Math.random() * 37); // 0-36
    const isRed = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(winningNumber);
    const isEven = winningNumber > 0 && winningNumber % 2 === 0;
    
    let isWin = false;
    let multiplier = 0;
    
    switch(betType) {
        case 'red':
            isWin = isRed;
            multiplier = isWin ? 2 : 0;
            break;
        case 'black':
            isWin = !isRed && winningNumber > 0;
            multiplier = isWin ? 2 : 0;
            break;
        case 'even':
            isWin = isEven;
            multiplier = isWin ? 2 : 0;
            break;
        case 'odd':
            isWin = !isEven && winningNumber > 0;
            multiplier = isWin ? 2 : 0;
            break;
        case 'number':
            isWin = parseInt(specificNumber) === winningNumber;
            multiplier = isWin ? 36 : 0;
            break;
    }
    
    const color = winningNumber === 0 ? 'Verde' : (isRed ? 'Rojo' : 'Negro');
    const result = `Número ganador: ${winningNumber} (${color}). ${isWin ? '¡Ganaste!' : 'Perdiste.'}`;
    
    await processBet(betAmount, multiplier, `Ruleta - ${result}`);
}

async function spinSlots() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    
    if (!validateBet(betAmount, 0.25)) return;
    
    const symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎'];
    const reel1 = symbols[Math.floor(Math.random() * symbols.length)];
    const reel2 = symbols[Math.floor(Math.random() * symbols.length)];
    const reel3 = symbols[Math.floor(Math.random() * symbols.length)];
    
    document.getElementById('slotsDisplay').innerHTML = `${reel1} ${reel2} ${reel3}`;
    
    let multiplier = 0;
    let result = '';
    
    if (reel1 === reel2 && reel2 === reel3) {
        if (reel1 === '🍒') {
            multiplier = 50;
            result = '¡JACKPOT! 3 Cerezas';
        } else {
            multiplier = 10;
            result = '¡3 iguales!';
        }
    } else if (reel1 === reel2 || reel2 === reel3 || reel1 === reel3) {
        multiplier = 3;
        result = '2 iguales';
    } else {
        multiplier = 0;
        result = 'Sin premio';
    }
    
    await processBet(betAmount, multiplier, `Slots - ${result}`);
}

async function playPoker() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    
    if (!validateBet(betAmount, 10)) return;
    
    // Simular mano de poker
    const hands = [
        { name: 'Par', chance: 0.4, multiplier: 1.5 },
        { name: 'Doble Par', chance: 0.2, multiplier: 2 },
        { name: 'Trío', chance: 0.1, multiplier: 3 },
        { name: 'Escalera', chance: 0.05, multiplier: 5 },
        { name: 'Color', chance: 0.03, multiplier: 6 },
        { name: 'Full House', chance: 0.02, multiplier: 8 },
        { name: 'Poker', chance: 0.005, multiplier: 25 },
        { name: 'Escalera Real', chance: 0.001, multiplier: 100 }
    ];
    
    const random = Math.random();
    let cumulativeChance = 0;
    let result = { name: 'Carta Alta', multiplier: 0 };
    
    for (const hand of hands) {
        cumulativeChance += hand.chance;
        if (random <= cumulativeChance) {
            result = hand;
            break;
        }
    }
    
    document.getElementById('pokerArea').innerHTML = `
        <div class="alert alert-info">
            <h5>🃏 ${result.name} 🃏</h5>
            <p>${result.multiplier > 0 ? `¡Ganaste ${result.multiplier}x!` : 'Sin premio'}</p>
        </div>
    `;
    
    await processBet(betAmount, result.multiplier, `Poker - ${result.name}`);
}

async function playBaccarat() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    const betType = document.getElementById('baccaratBet').value;
    
    if (!validateBet(betAmount, 25)) return;
    
    const playerTotal = (Math.floor(Math.random() * 9) + 1) + (Math.floor(Math.random() * 9) + 1);
    const bankerTotal = (Math.floor(Math.random() * 9) + 1) + (Math.floor(Math.random() * 9) + 1);
    const playerFinal = playerTotal % 10;
    const bankerFinal = bankerTotal % 10;
    
    let isWin = false;
    let multiplier = 0;
    let result = '';
    
    if (betType === 'player' && playerFinal > bankerFinal) {
        isWin = true;
        multiplier = 2;
        result = `Jugador: ${playerFinal}, Banca: ${bankerFinal}. ¡Ganó el Jugador!`;
    } else if (betType === 'banker' && bankerFinal > playerFinal) {
        isWin = true;
        multiplier = 1.95;
        result = `Jugador: ${playerFinal}, Banca: ${bankerFinal}. ¡Ganó la Banca!`;
    } else if (betType === 'tie' && playerFinal === bankerFinal) {
        isWin = true;
        multiplier = 8;
        result = `Jugador: ${playerFinal}, Banca: ${bankerFinal}. ¡Empate!`;
    } else {
        result = `Jugador: ${playerFinal}, Banca: ${bankerFinal}. Perdiste.`;
    }
    
    document.getElementById('baccaratArea').innerHTML = `<div class="alert alert-info">${result}</div>`;
    
    await processBet(betAmount, multiplier, `Baccarat - ${result}`);
}

async function rollDice() {
    const betAmount = parseFloat(document.getElementById('betAmount').value);
    const betType = document.getElementById('crapsBet').value;
    
    if (!validateBet(betAmount, 5)) return;
    
    const die1 = Math.floor(Math.random() * 6) + 1;
    const die2 = Math.floor(Math.random() * 6) + 1;
    const total = die1 + die2;
    
    document.getElementById('crapsDisplay').innerHTML = `${die1} + ${die2} = ${total}`;
    
    let isWin = false;
    let multiplier = 0;
    let result = '';
    
    switch(betType) {
        case 'pass':
            isWin = [7, 11].includes(total);
            multiplier = isWin ? 2 : 0;
            result = `Dados: ${total}. ${isWin ? '¡Pass Line gana!' : 'Pass Line pierde.'}`;
            break;
        case 'dontpass':
            isWin = [2, 3].includes(total);
            multiplier = isWin ? 2 : 0;
            result = `Dados: ${total}. ${isWin ? '¡Don\'t Pass gana!' : 'Don\'t Pass pierde.'}`;
            break;
        case 'field':
            isWin = [2, 3, 4, 9, 10, 11, 12].includes(total);
            multiplier = isWin ? 2 : 0;
            result = `Dados: ${total}. ${isWin ? '¡Field gana!' : 'Field pierde.'}`;
            break;
        case 'any7':
            isWin = total === 7;
            multiplier = isWin ? 4 : 0;
            result = `Dados: ${total}. ${isWin ? '¡Any 7 gana!' : 'Any 7 pierde.'}`;
            break;
    }
    
    await processBet(betAmount, multiplier, `Craps - ${result}`);
}

function validateBet(amount, minBet = 1) {
    if (!amount || amount < minBet) {
        showToast(`La apuesta mínima es $${minBet}`, TOAST_TYPES.ERROR);
        return false;
    }
    
    if (amount > currentUser.saldo_actual) {
        showToast('Saldo insuficiente', TOAST_TYPES.ERROR);
        return false;
    }
    
    return true;
}

async function processBet(betAmount, multiplier, description) {
    try {
        // Crear transacción de apuesta (débito)
        const betResponse = await makeApiRequest(ROUTES.CREATE_TRANSACTION, {
            method: 'POST',
            body: JSON.stringify({
                cliente_id: currentUser.id,
                tipo: 'juego',
                monto: -betAmount,
                descripcion: `Apuesta - ${description}`,
                metodo_pago: 'saldo'
            })
        });
        
        if (!betResponse.ok) {
            throw new Error('Error al procesar apuesta');
        }
        
        // Si hay ganancia, crear transacción de premio
        if (multiplier > 0) {
            const winAmount = betAmount * multiplier;
            const prizeResponse = await makeApiRequest(ROUTES.CREATE_TRANSACTION, {
                method: 'POST',
                body: JSON.stringify({
                    cliente_id: currentUser.id,
                    tipo: 'ingreso',
                    monto: winAmount,
                    descripcion: `Premio - ${description}`,
                    metodo_pago: 'premio'
                })
            });
            
            if (prizeResponse.ok) {
                const netWin = winAmount - betAmount;
                showToast(`¡Ganaste $${winAmount.toFixed(2)}! (Ganancia neta: $${netWin.toFixed(2)})`, TOAST_TYPES.SUCCESS);
            }
        } else {
            showToast(`Perdiste $${betAmount.toFixed(2)}`, TOAST_TYPES.ERROR);
        }
        
        // Actualizar datos del cliente
        await loadClientData();
        
    } catch (error) {
        console.error('Error procesando apuesta:', error);
        showToast('Error al procesar la apuesta', TOAST_TYPES.ERROR);
    }
}

// Event listener para mostrar campo de número específico en ruleta
document.addEventListener('change', function(e) {
    if (e.target.id === 'betType') {
        const numberBet = document.getElementById('numberBet');
        if (numberBet) {
            numberBet.style.display = e.target.value === 'number' ? 'block' : 'none';
        }
    }
});

async function claimPromotion(codigo) {
    try {
        const response = await makeApiRequest(ROUTES.CLAIM_PROMOTION(codigo, currentUser.id), {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Promoción reclamada exitosamente!', TOAST_TYPES.SUCCESS);
            await loadPromotions();
            await loadClientData();
        } else {
            const result = await response.json();
            showToast(result.detail || 'Error al reclamar la promoción', TOAST_TYPES.ERROR);
        }
    } catch (error) {
        console.error('Error al reclamar promoción:', error);
        showToast('Error al reclamar la promoción', TOAST_TYPES.ERROR);
    }
}

// Función para abrir el modal de recarga personalizado
function openRechargeModal() {
    const modal = document.getElementById('customRechargeModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevenir scroll del body
    }
}

// Función para mostrar el modal de recarga (compatibilidad)
function showRechargeModal() {
    openRechargeModal();
}

// Función para cerrar el modal de recarga personalizado
function closeCustomRechargeModal() {
    const modal = document.getElementById('customRechargeModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restaurar scroll del body
        // Limpiar el formulario
        const form = document.getElementById('customRechargeForm');
        if (form) {
            form.reset();
        }
    }
}

// Función para cerrar el modal de recarga (compatibilidad)
function closeRechargeModal() {
    closeCustomRechargeModal();
}

// ===== FUNCIONES DE VALIDACIÓN =====
function validateRechargeAmount(amount) {
    return amount && parseFloat(amount) >= VALIDATION.MIN_RECHARGE && parseFloat(amount) <= VALIDATION.MAX_RECHARGE;
}

// ===== FUNCIONES DE RECARGA =====
// Función para el modal personalizado
async function submitCustomRecharge() {
    const amount = parseFloat(document.getElementById('customRechargeAmount').value);
    const paymentMethod = document.getElementById('customPaymentMethod').value;
    
    if (!validateRechargeAmount(amount)) {
        showToast(`El monto debe estar entre $${VALIDATION.MIN_RECHARGE} y $${VALIDATION.MAX_RECHARGE}`, TOAST_TYPES.ERROR);
        return;
    }
    
    try {
        const response = await makeApiRequest(ROUTES.CREATE_TRANSACTION, {
            method: 'POST',
            body: JSON.stringify({
                cliente_id: currentUser.id,
                tipo: 'ingreso',
                monto: amount,
                descripcion: `Recarga de saldo - ${paymentMethod}`,
                metodo_pago: paymentMethod
            })
        });
        
        if (response.ok) {
            showToast('Recarga procesada exitosamente!', TOAST_TYPES.SUCCESS);
            closeCustomRechargeModal();
            await loadClientData();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error al procesar la recarga', TOAST_TYPES.ERROR);
        }
    } catch (error) {
        console.error('Error en recarga:', error);
        showToast('Error al procesar la recarga', TOAST_TYPES.ERROR);
    }
}

// Función original para compatibilidad
async function submitRecharge() {
    const amount = parseFloat(document.getElementById('rechargeAmount').value);
    const paymentMethod = document.getElementById('paymentMethod').value;
    
    if (!validateRechargeAmount(amount)) {
        showToast(`El monto debe estar entre $${VALIDATION.MIN_RECHARGE} y $${VALIDATION.MAX_RECHARGE}`, TOAST_TYPES.ERROR);
        return;
    }
    
    try {
        const response = await makeApiRequest(ROUTES.CREATE_TRANSACTION, {
            method: 'POST',
            body: JSON.stringify({
                cliente_id: currentUser.id,
                tipo: 'ingreso',
                monto: amount,
                descripcion: `Recarga de saldo - ${paymentMethod}`,
                metodo_pago: paymentMethod
            })
        });
        
        if (response.ok) {
            showToast('Recarga procesada exitosamente!', TOAST_TYPES.SUCCESS);
            closeRechargeModal();
            await loadClientData();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error al procesar la recarga', TOAST_TYPES.ERROR);
        }
    } catch (error) {
        console.error('Error en recarga:', error);
        showToast('Error al procesar la recarga', TOAST_TYPES.ERROR);
    }
}

// ===== FUNCIONES DE SOPORTE =====
async function submitSupportTicket() {
    const subject = document.getElementById('ticketSubject').value;
    const category = document.getElementById('ticketCategory').value;
    const description = document.getElementById('ticketDescription').value;
    
    try {
        const response = await makeApiRequest(ROUTES.CREATE_TICKET, {
            method: 'POST',
            body: JSON.stringify({
                cliente_id: currentUser.id,
                tipo: 'consulta',
                asunto: subject,
                categoria: category,
                descripcion: description
            })
        });
        
        if (response.ok) {
            showToast('Ticket creado exitosamente!', TOAST_TYPES.SUCCESS);
            document.getElementById('supportForm').reset();
            await loadUserTickets();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Error al crear el ticket', TOAST_TYPES.ERROR);
        }
    } catch (error) {
        console.error('Error al crear ticket:', error);
        showToast('Error al crear el ticket', TOAST_TYPES.ERROR);
    }
}

// ===== EVENT LISTENERS =====
// Cerrar modal con tecla Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('customRechargeModal');
        if (modal && modal.style.display === 'flex') {
            closeCustomRechargeModal();
        }
    }
});

// Formularios
// Event listener para el formulario de recarga personalizado
const customRechargeForm = document.getElementById('customRechargeForm');
if (customRechargeForm) {
    customRechargeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await submitCustomRecharge();
    });
}

// Event listener para el formulario de recarga original (compatibilidad)
const rechargeForm = document.getElementById('rechargeForm');
if (rechargeForm) {
    rechargeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await submitRecharge();
    });
}

document.getElementById('supportForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    await submitSupportTicket();
});

// Función para mostrar toasts
// ===== FUNCIONES DE UI =====
function showToast(message, type = TOAST_TYPES.INFO) {
    const toastElement = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    if (!toastElement || !toastMessage) {
        console.error('Toast elements not found');
        return;
    }
    
    // Configurar el mensaje y el tipo
    toastMessage.textContent = message;
    
    // Configurar el color según el tipo
    toastElement.className = 'toast';
    const toastConfig = getToastConfig(type);
    toastElement.classList.add(...toastConfig.classes);
    
    // Mostrar el toast
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Limpiar clases después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.className = 'toast';
    }, { once: true });
}

function getToastConfig(type) {
    const configs = {
        [TOAST_TYPES.SUCCESS]: { classes: ['bg-success', 'text-white'] },
        [TOAST_TYPES.ERROR]: { classes: ['bg-danger', 'text-white'] },
        [TOAST_TYPES.WARNING]: { classes: ['bg-warning', 'text-dark'] },
        [TOAST_TYPES.INFO]: { classes: ['bg-info', 'text-white'] }
    };
    
    return configs[type] || configs[TOAST_TYPES.INFO];
}