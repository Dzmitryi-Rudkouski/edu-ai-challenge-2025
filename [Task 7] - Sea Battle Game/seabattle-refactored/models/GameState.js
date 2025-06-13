import { GameConfig } from './GameConfig.js';
import { Ship } from './Ship.js';
import { GameAI } from './GameAI.js';

/**
 * Класс, управляющий состоянием игры
 */
export class GameState {
  #initialized;
  #playerShips;
  #cpuShips;
  #playerGuesses;
  #cpuGuesses;
  #gameAI;
  #maxPlacementAttempts;

  constructor() {
    this.#initialized = false;
    this.#playerShips = [];
    this.#cpuShips = [];
    this.#playerGuesses = new Set();
    this.#cpuGuesses = new Set();
    this.#gameAI = null;
    this.#maxPlacementAttempts = GameConfig.MAX_PLACEMENT_ATTEMPTS;
  }

  /**
   * Инициализировать игру
   * @throws {Error} Если игра уже инициализирована
   */
  initialize() {
    if (this.#initialized) {
      throw new Error('Игра уже инициализирована');
    }

    this.#placeShips();
    this.#gameAI = new GameAI(this);
    this.#initialized = true;
  }

  /**
   * Проверить, инициализирована ли игра
   * @returns {boolean}
   */
  isInitialized() {
    return this.#initialized;
  }

  /**
   * Получить корабли игрока
   * @returns {Array<Ship>}
   */
  getPlayerShips() {
    return [...this.#playerShips];
  }

  /**
   * Получить корабли CPU
   * @returns {Array<Ship>}
   */
  getCPUShips() {
    return [...this.#cpuShips];
  }

  /**
   * Проверить, была ли клетка уже проверена игроком
   * @param {{row: number, col: number}} guess
   * @returns {boolean}
   */
  isCellGuessed(guess) {
    return this.#playerGuesses.has(this.#getGuessKey(guess));
  }

  /**
   * Обработать ход игрока
   * @param {{row: number, col: number}} guess
   * @returns {{type: string, coordinates: {row: number, col: number}}}
   * @throws {Error} Если игра не инициализирована или ход недопустим
   */
  processPlayerGuess(guess) {
    this.#validateGameState();
    this.#validateGuess(guess);

    const guessKey = this.#getGuessKey(guess);
    if (this.#playerGuesses.has(guessKey)) {
      throw new Error('Эта клетка уже проверена');
    }

    this.#playerGuesses.add(guessKey);
    const hitShip = this.#findShipAtLocation(this.#cpuShips, guess);

    if (hitShip) {
      hitShip.hit(guess);
      return { type: 'hit', coordinates: guess };
    }

    return { type: 'miss', coordinates: guess };
  }

  /**
   * Обработать ход CPU
   * @returns {{type: string, coordinates: {row: number, col: number}}}
   * @throws {Error} Если игра не инициализирована
   */
  processCPUGuess() {
    this.#validateGameState();

    const guess = this.#gameAI.makeGuess();
    const guessKey = this.#getGuessKey(guess);

    if (this.#cpuGuesses.has(guessKey)) {
      return this.processCPUGuess();
    }

    this.#cpuGuesses.add(guessKey);
    const hitShip = this.#findShipAtLocation(this.#playerShips, guess);

    if (hitShip) {
      hitShip.hit(guess);
      this.#gameAI.updateState(guess, 'hit');
      return { type: 'hit', coordinates: guess };
    }

    this.#gameAI.updateState(guess, 'miss');
    return { type: 'miss', coordinates: guess };
  }

  /**
   * Проверить, окончена ли игра
   * @returns {boolean}
   */
  isGameOver() {
    if (!this.#initialized) return false;
    return this.#areAllShipsSunk(this.#playerShips) || this.#areAllShipsSunk(this.#cpuShips);
  }

  /**
   * Разместить корабли на поле
   * @private
   */
  #placeShips() {
    this.#placeShipsForPlayer();
    this.#placeShipsForCPU();
  }

  /**
   * Разместить корабли игрока
   * @private
   */
  #placeShipsForPlayer() {
    for (const { size, count } of GameConfig.SHIPS) {
      for (let i = 0; i < count; i++) {
        let attempts = 0;
        let placed = false;

        while (!placed && attempts < this.#maxPlacementAttempts) {
          try {
            const ship = new Ship(size);
            const location = this.#getRandomLocation();
            const direction = this.#getRandomDirection();
            this.#placeShip(ship, location, direction, this.#playerShips);
            this.#playerShips.push(ship);
            placed = true;
          } catch (error) {
            attempts++;
          }
        }

        if (!placed) {
          throw new Error('Не удалось разместить корабли');
        }
      }
    }
  }

  /**
   * Разместить корабли CPU
   * @private
   */
  #placeShipsForCPU() {
    for (const { size, count } of GameConfig.SHIPS) {
      for (let i = 0; i < count; i++) {
        let attempts = 0;
        let placed = false;

        while (!placed && attempts < this.#maxPlacementAttempts) {
          try {
            const ship = new Ship(size);
            const location = this.#getRandomLocation();
            const direction = this.#getRandomDirection();
            this.#placeShip(ship, location, direction, this.#cpuShips);
            this.#cpuShips.push(ship);
            placed = true;
          } catch (error) {
            attempts++;
          }
        }

        if (!placed) {
          throw new Error('Не удалось разместить корабли CPU');
        }
      }
    }
  }

  /**
   * Разместить корабль на поле
   * @private
   * @param {Ship} ship
   * @param {{row: number, col: number}} location
   * @param {string} direction
   * @param {Array<Ship>} ships
   * @throws {Error} Если размещение невозможно
   */
  #placeShip(ship, location, direction, ships) {
    const locations = this.#getShipLocations(location, direction, ship.size);
    
    if (!this.#areLocationsValid(locations)) {
      throw new Error(GameConfig.ERROR_MESSAGES.INVALID_SHIP_PLACEMENT);
    }

    if (this.#doLocationsOverlap(locations, ships)) {
      throw new Error(GameConfig.ERROR_MESSAGES.INVALID_SHIP_PLACEMENT);
    }

    locations.forEach(loc => ship.addLocation(loc));
  }

  /**
   * Получить локации корабля
   * @private
   * @param {{row: number, col: number}} location
   * @param {string} direction
   * @param {number} size
   * @returns {Array<{row: number, col: number}>}
   */
  #getShipLocations(location, direction, size) {
    const locations = [];
    let { row, col } = location;

    for (let i = 0; i < size; i++) {
      locations.push({ row, col });
      switch (direction) {
        case 'up': row--; break;
        case 'right': col++; break;
        case 'down': row++; break;
        case 'left': col--; break;
      }
    }

    return locations;
  }

  /**
   * Проверить валидность локаций
   * @private
   * @param {Array<{row: number, col: number}>} locations
   * @returns {boolean}
   */
  #areLocationsValid(locations) {
    return locations.every(loc =>
      loc.row >= 0 &&
      loc.row < GameConfig.BOARD_SIZE &&
      loc.col >= 0 &&
      loc.col < GameConfig.BOARD_SIZE
    );
  }

  /**
   * Проверить пересечение с другими кораблями
   * @private
   * @param {Array<{row: number, col: number}>} locations
   * @param {Array<Ship>} ships
   * @returns {boolean}
   */
  #doLocationsOverlap(locations, ships) {
    return ships.some(ship =>
      locations.some(loc => ship.isAtLocation(loc))
    );
  }

  /**
   * Получить случайную локацию
   * @private
   * @returns {{row: number, col: number}}
   */
  #getRandomLocation() {
    return {
      row: Math.floor(Math.random() * GameConfig.BOARD_SIZE),
      col: Math.floor(Math.random() * GameConfig.BOARD_SIZE)
    };
  }

  /**
   * Получить случайное направление
   * @private
   * @returns {string}
   */
  #getRandomDirection() {
    const directions = ['up', 'right', 'down', 'left'];
    return directions[Math.floor(Math.random() * directions.length)];
  }

  /**
   * Найти корабль по локации
   * @private
   * @param {Array<Ship>} ships
   * @param {{row: number, col: number}} location
   * @returns {Ship|null}
   */
  #findShipAtLocation(ships, location) {
    return ships.find(ship => ship.isAtLocation(location));
  }

  /**
   * Проверить, потоплены ли все корабли
   * @private
   * @param {Array<Ship>} ships
   * @returns {boolean}
   */
  #areAllShipsSunk(ships) {
    return ships.every(ship => ship.isSunk());
  }

  /**
   * Получить ключ для хода
   * @private
   * @param {{row: number, col: number}} guess
   * @returns {string}
   */
  #getGuessKey(guess) {
    return `${guess.row},${guess.col}`;
  }

  /**
   * Проверить состояние игры
   * @private
   * @throws {Error} Если игра не инициализирована
   */
  #validateGameState() {
    if (!this.#initialized) {
      throw new Error(GameConfig.ERROR_MESSAGES.GAME_NOT_INITIALIZED);
    }
    if (this.isGameOver()) {
      throw new Error(GameConfig.ERROR_MESSAGES.GAME_OVER);
    }
  }

  /**
   * Проверить валидность хода
   * @private
   * @param {{row: number, col: number}} guess
   * @throws {Error} Если ход недопустим
   */
  #validateGuess(guess) {
    if (!guess || typeof guess.row !== 'number' || typeof guess.col !== 'number') {
      throw new Error(GameConfig.ERROR_MESSAGES.INVALID_COORDINATES);
    }
    if (
      guess.row < 0 ||
      guess.row >= GameConfig.BOARD_SIZE ||
      guess.col < 0 ||
      guess.col >= GameConfig.BOARD_SIZE
    ) {
      throw new Error(GameConfig.ERROR_MESSAGES.INVALID_COORDINATES);
    }
  }
} 