import { GameState } from '../models/GameState.js';
import { GameView } from '../views/GameView.js';

/**
 * Класс, управляющий игровым процессом
 */
export class GameController {
  #gameState;
  #gameView;

  constructor() {
    this.#gameState = new GameState();
    this.#gameView = new GameView();
  }

  /**
   * Начать игру
   * @returns {Promise<void>}
   */
  async start() {
    try {
      this.#gameState.initialize();
      this.#gameView.showWelcome();
      await this.#gameLoop();
    } catch (error) {
      this.#gameView.showError(error.message);
      throw error;
    }
  }

  /**
   * Основной игровой цикл
   * @private
   * @returns {Promise<void>}
   */
  async #gameLoop() {
    while (!this.#gameState.isGameOver()) {
      await this.#processPlayerTurn();
      if (this.#gameState.isGameOver()) break;
      await this.#processCPUTurn();
    }
    this.#showGameResult();
  }

  /**
   * Обработать ход игрока
   * @private
   * @returns {Promise<void>}
   */
  async #processPlayerTurn() {
    try {
      const guess = await this.#gameView.getPlayerGuess();
      const result = this.#gameState.processPlayerGuess(guess);
      this.#gameView.showGuessResult(result, 'player');
    } catch (error) {
      this.#gameView.showError(error.message);
      await this.#processPlayerTurn();
    }
  }

  /**
   * Обработать ход CPU
   * @private
   * @returns {Promise<void>}
   */
  async #processCPUTurn() {
    try {
      const result = this.#gameState.processCPUGuess();
      this.#gameView.showGuessResult(result, 'cpu');
      await this.#gameView.waitForEnter();
    } catch (error) {
      this.#gameView.showError(error.message);
      throw error;
    }
  }

  /**
   * Показать результат игры
   * @private
   */
  #showGameResult() {
    const playerShips = this.#gameState.getPlayerShips();
    const cpuShips = this.#gameState.getCPUShips();
    const playerSunk = playerShips.every(ship => ship.isSunk());
    const cpuSunk = cpuShips.every(ship => ship.isSunk());

    if (playerSunk) {
      this.#gameView.showGameOver('cpu');
    } else if (cpuSunk) {
      this.#gameView.showGameOver('player');
    }
  }
} 