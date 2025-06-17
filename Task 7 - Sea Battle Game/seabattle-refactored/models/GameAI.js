import { GameConfig } from './GameConfig.js';

/**
 * Класс, реализующий искусственный интеллект для игры
 */
export class GameAI {
  #gameState;
  #lastHit;
  #possibleDirections;
  #currentDirection;
  #possibleShipSizes;

  /**
   * @param {GameState} gameState - Состояние игры
   */
  constructor(gameState) {
    this.#gameState = gameState;
    this.#lastHit = null;
    this.#possibleDirections = ['up', 'right', 'down', 'left'];
    this.#currentDirection = null;
    this.#possibleShipSizes = new Set([4, 3, 2, 1]);
  }

  /**
   * Сделать ход
   * @returns {{row: number, col: number}} Координаты хода
   */
  makeGuess() {
    if (this.#lastHit) {
      return this.#getHuntGuess();
    }
    return this.#getRandomGuess();
  }

  /**
   * Обновить состояние ИИ после хода
   * @param {{row: number, col: number}} guess - Координаты хода
   * @param {string} result - Результат хода ('hit' или 'miss')
   */
  updateState(guess, result) {
    if (result === 'hit') {
      this.#lastHit = guess;
      this.#updatePossibleShipSizes();
      if (!this.#currentDirection) {
        this.#resetDirections();
      }
    } else if (this.#currentDirection) {
      this.#switchDirection();
    }
  }

  /**
   * Получить случайный ход
   * @private
   * @returns {{row: number, col: number}}
   */
  #getRandomGuess() {
    const availableCells = this.#getAvailableCells();
    const randomIndex = Math.floor(Math.random() * availableCells.length);
    return availableCells[randomIndex];
  }

  /**
   * Получить ход в режиме охоты
   * @private
   * @returns {{row: number, col: number}}
   */
  #getHuntGuess() {
    if (!this.#lastHit) {
      return this.#getRandomGuess();
    }

    if (this.#currentDirection) {
      const nextGuess = this.#getNextGuessInDirection();
      if (this.#isValidGuess(nextGuess)) {
        return nextGuess;
      }
      this.#switchDirection();
    }

    for (const direction of this.#possibleDirections) {
      const guess = this.#getGuessInDirection(direction);
      if (this.#isValidGuess(guess)) {
        this.#currentDirection = direction;
        return guess;
      }
    }

    this.#resetHunt();
    return this.#getRandomGuess();
  }

  /**
   * Получить следующий ход в текущем направлении
   * @private
   * @returns {{row: number, col: number}}
   */
  #getNextGuessInDirection() {
    return this.#getGuessInDirection(this.#currentDirection);
  }

  /**
   * Получить ход в указанном направлении
   * @private
   * @param {string} direction
   * @returns {{row: number, col: number}}
   */
  #getGuessInDirection(direction) {
    const { row, col } = this.#lastHit;
    switch (direction) {
      case 'up': return { row: row - 1, col };
      case 'right': return { row, col: col + 1 };
      case 'down': return { row: row + 1, col };
      case 'left': return { row, col: col - 1 };
      default: return null;
    }
  }

  /**
   * Проверить валидность хода
   * @private
   * @param {{row: number, col: number}} guess
   * @returns {boolean}
   */
  #isValidGuess(guess) {
    if (!guess) return false;
    const { row, col } = guess;
    return (
      row >= 0 &&
      row < GameConfig.BOARD_SIZE &&
      col >= 0 &&
      col < GameConfig.BOARD_SIZE &&
      !this.#gameState.isCellGuessed(guess)
    );
  }

  /**
   * Получить список доступных клеток
   * @private
   * @returns {Array<{row: number, col: number}>}
   */
  #getAvailableCells() {
    const cells = [];
    for (let row = 0; row < GameConfig.BOARD_SIZE; row++) {
      for (let col = 0; col < GameConfig.BOARD_SIZE; col++) {
        const guess = { row, col };
        if (!this.#gameState.isCellGuessed(guess)) {
          cells.push(guess);
        }
      }
    }
    return cells;
  }

  /**
   * Переключить направление поиска
   * @private
   */
  #switchDirection() {
    this.#currentDirection = null;
    this.#possibleDirections = this.#possibleDirections.filter(dir => dir !== this.#currentDirection);
  }

  /**
   * Сбросить направления поиска
   * @private
   */
  #resetDirections() {
    this.#possibleDirections = ['up', 'right', 'down', 'left'];
    this.#currentDirection = null;
  }

  /**
   * Сбросить режим охоты
   * @private
   */
  #resetHunt() {
    this.#lastHit = null;
    this.#resetDirections();
  }

  /**
   * Обновить возможные размеры кораблей
   * @private
   */
  #updatePossibleShipSizes() {
    const sunkShips = this.#gameState.getCPUShips().filter(ship => ship.isSunk());
    sunkShips.forEach(ship => this.#possibleShipSizes.delete(ship.size));
  }
} 