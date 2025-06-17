import { GameConfig } from './GameConfig.js';

/**
 * Класс, представляющий корабль в игре
 */
export class Ship {
  #size;
  #locations;
  #hits;

  /**
   * @param {number} size - Размер корабля
   * @throws {Error} Если размер корабля недопустим
   */
  constructor(size) {
    if (size < 1 || size > 4) {
      throw new Error('Недопустимый размер корабля');
    }
    this.#size = size;
    this.#locations = new Set();
    this.#hits = new Set();
  }

  /**
   * Получить размер корабля
   * @returns {number}
   */
  get size() {
    return this.#size;
  }

  /**
   * Получить все локации корабля
   * @returns {Set<{row: number, col: number}>}
   */
  getLocations() {
    return new Set(this.#locations);
  }

  /**
   * Получить все попадания по кораблю
   * @returns {Set<{row: number, col: number}>}
   */
  getHits() {
    return new Set(this.#hits);
  }

  /**
   * Добавить локацию корабля
   * @param {{row: number, col: number}} location
   * @throws {Error} Если координаты недопустимы
   */
  addLocation(location) {
    if (!this.#isValidLocation(location)) {
      throw new Error(GameConfig.ERROR_MESSAGES.INVALID_COORDINATES);
    }
    this.#locations.add(location);
  }

  /**
   * Проверить, находится ли корабль в указанной локации
   * @param {{row: number, col: number}} location
   * @returns {boolean}
   */
  isAtLocation(location) {
    return this.#locations.has(location);
  }

  /**
   * Проверить, было ли попадание в указанную локацию
   * @param {{row: number, col: number}} location
   * @returns {boolean}
   */
  isHit(location) {
    return this.#hits.has(location);
  }

  /**
   * Зарегистрировать попадание в корабль
   * @param {{row: number, col: number}} location
   * @throws {Error} Если координаты недопустимы или корабль уже потоплен
   */
  hit(location) {
    if (!this.#isValidLocation(location)) {
      throw new Error(GameConfig.ERROR_MESSAGES.INVALID_COORDINATES);
    }
    if (!this.isAtLocation(location)) {
      throw new Error('Попадание не по кораблю');
    }
    if (this.isSunk()) {
      throw new Error('Корабль уже потоплен');
    }
    this.#hits.add(location);
  }

  /**
   * Проверить, потоплен ли корабль
   * @returns {boolean}
   */
  isSunk() {
    return this.#hits.size === this.#size;
  }

  /**
   * Проверить валидность координат
   * @private
   * @param {{row: number, col: number}} location
   * @returns {boolean}
   */
  #isValidLocation(location) {
    return (
      location &&
      typeof location.row === 'number' &&
      typeof location.col === 'number' &&
      location.row >= 0 &&
      location.row < GameConfig.BOARD_SIZE &&
      location.col >= 0 &&
      location.col < GameConfig.BOARD_SIZE
    );
  }
} 