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
    console.log('   - 3 линкора (3 клетки)');
    console.log('3. Корабли не могут касаться друг друга');
    console.log('4. Ходы по очереди: игрок -> компьютер');
    console.log('5. Введите координаты в формате: 00, 34, 98');
    console.log('\nНажмите Enter для начала игры...');
  }

  /**
   * Получить ход от игрока
   * @returns {Promise<{row: number, col: number}>}
   */
  async getPlayerGuess() {
    return new Promise((resolve) => {
      this.#rl.question('\nВаш ход (например, 00): ', (answer) => {
        const guess = this.#parseGuess(answer);
        if (guess) {
          resolve(guess);
        } else {
          console.log('Некорректный формат. Используйте две цифры (например, 00, 34, 98)');
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
    
    if (player === 'player') {
      console.log(type === 'hit' ? 'PLAYER HIT!' : 'PLAYER MISS.');
    } else {
      console.log(`CPU ${type === 'hit' ? 'HIT' : 'MISS'} at ${coordStr}!`);
    }
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
    console.log('\n*** ' + (winner === 'player' ? 'CONGRATULATIONS! You sunk all enemy battleships!' : 'GAME OVER! The CPU sunk all your battleships!') + ' ***');
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
   * Отобразить игровые доски
   * @param {Array<Array<string>>} playerBoard - Доска игрока
   * @param {Array<Array<string>>} cpuBoard - Доска CPU
   */
  displayBoards(playerBoard, cpuBoard) {
    console.log('\n   --- OPPONENT BOARD ---          --- YOUR BOARD ---');
    let header = '  ';
    for (let h = 0; h < GameConfig.BOARD_SIZE; h++) {
      header += h + ' ';
    }
    console.log(header + '     ' + header);

    for (let i = 0; i < GameConfig.BOARD_SIZE; i++) {
      let rowStr = i + ' ';

      // CPU board (скрытая)
      for (let j = 0; j < GameConfig.BOARD_SIZE; j++) {
        const cell = cpuBoard[i][j];
        rowStr += (cell === 'S' ? '~' : cell) + ' ';
      }
      rowStr += '    ' + i + ' ';

      // Player board (видимая)
      for (let j = 0; j < GameConfig.BOARD_SIZE; j++) {
        rowStr += playerBoard[i][j] + ' ';
      }
      console.log(rowStr);
    }
    console.log('\n');
  }

  /**
   * Разобрать ввод игрока (формат: 00, 34, 98)
   * @private
   * @param {string} input
   * @returns {{row: number, col: number}|null}
   */
  #parseGuess(input) {
    const match = input.trim().match(/^([0-9])([0-9])$/);
    if (!match) return null;

    const [, row, col] = match;
    const rowNum = parseInt(row);
    const colNum = parseInt(col);

    if (rowNum >= 0 && rowNum < GameConfig.BOARD_SIZE && 
        colNum >= 0 && colNum < GameConfig.BOARD_SIZE) {
      return { row: rowNum, col: colNum };
    }
    return null;
  }

  /**
   * Форматировать координаты для вывода
   * @private
   * @param {{row: number, col: number}} coordinates
   * @returns {string}
   */
  #formatCoordinates(coordinates) {
    const { row, col } = coordinates;
    return `${row}${col}`;
  }
} 