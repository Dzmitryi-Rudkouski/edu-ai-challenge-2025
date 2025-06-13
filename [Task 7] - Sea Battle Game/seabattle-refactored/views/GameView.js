import { GameConfig } from '../models/GameConfig.js';
import readline from 'readline';

/**
 * Класс, отвечающий за отображение игры
 */
export class GameView {
  #rl;

  constructor() {
    this.#rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  /**
   * Показать приветственное сообщение
   */
  showWelcome() {
    console.clear();
    console.log('Добро пожаловать в игру "Морской бой"!');
    console.log('Правила игры:');
    console.log('1. Игровое поле 10x10');
    console.log('2. Корабли:');
    console.log('   - 1 линкор (4 клетки)');
    console.log('   - 2 крейсера (3 клетки)');
    console.log('   - 3 эсминца (2 клетки)');
    console.log('   - 4 катера (1 клетка)');
    console.log('3. Корабли не могут касаться друг друга');
    console.log('4. Ходы по очереди: игрок -> компьютер');
    console.log('\nНажмите Enter для начала игры...');
  }

  /**
   * Получить ход от игрока
   * @returns {Promise<{row: number, col: number}>}
   */
  async getPlayerGuess() {
    return new Promise((resolve) => {
      this.#rl.question('\nВаш ход (например, A5): ', (answer) => {
        const guess = this.#parseGuess(answer);
        if (guess) {
          resolve(guess);
        } else {
          console.log('Некорректный формат. Используйте букву (A-J) и цифру (0-9)');
          resolve(this.getPlayerGuess());
        }
      });
    });
  }

  /**
   * Показать результат хода
   * @param {{type: string, coordinates: {row: number, col: number}}} result
   * @param {string} player - 'player' или 'cpu'
   */
  showGuessResult(result, player) {
    const { type, coordinates } = result;
    const coordStr = this.#formatCoordinates(coordinates);
    const playerName = player === 'player' ? 'Вы' : 'Компьютер';

    console.log(`\n${playerName} выбрали клетку ${coordStr}`);
    console.log(type === 'hit' ? 'Попадание!' : 'Промах!');
  }

  /**
   * Показать ошибку
   * @param {string} message
   */
  showError(message) {
    console.log(`\nОшибка: ${message}`);
  }

  /**
   * Показать результат игры
   * @param {string} winner - 'player' или 'cpu'
   */
  showGameOver(winner) {
    console.log('\nИгра окончена!');
    console.log(winner === 'player' ? 'Вы победили!' : 'Компьютер победил!');
    this.#rl.close();
  }

  /**
   * Ожидать нажатия Enter
   * @returns {Promise<void>}
   */
  async waitForEnter() {
    return new Promise((resolve) => {
      this.#rl.question('\nНажмите Enter для продолжения...', () => {
        resolve();
      });
    });
  }

  /**
   * Разобрать ввод игрока
   * @private
   * @param {string} input
   * @returns {{row: number, col: number}|null}
   */
  #parseGuess(input) {
    const match = input.trim().toUpperCase().match(/^([A-J])([0-9])$/);
    if (!match) return null;

    const [, col, row] = match;
    return {
      row: parseInt(row),
      col: col.charCodeAt(0) - 'A'.charCodeAt(0)
    };
  }

  /**
   * Форматировать координаты для вывода
   * @private
   * @param {{row: number, col: number}} coordinates
   * @returns {string}
   */
  #formatCoordinates(coordinates) {
    const { row, col } = coordinates;
    return `${String.fromCharCode('A'.charCodeAt(0) + col)}${row}`;
  }
} 