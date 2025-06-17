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
      await this.#gameView.waitForEnter();
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
      // Отображаем доски перед каждым ходом
      this.#gameView.displayBoards(
        this.#gameState.getPlayerBoard(),
        this.#gameState.getCPUBoard()
      );
      
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
      console.log("\n--- CPU's Turn ---");
      const result = this.#gameState.processCPUGuess();
      this.#gameView.showGuessResult(result, 'cpu');
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