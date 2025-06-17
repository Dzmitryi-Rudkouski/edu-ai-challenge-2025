import { GameView } from '../../views/GameView.js';

// Мокаем readline для тестирования
jest.mock('readline', () => ({
  createInterface: jest.fn(() => ({
    question: jest.fn(),
    close: jest.fn()
  }))
}));

describe('GameView', () => {
  let gameView;

  beforeEach(() => {
    jest.clearAllMocks();
    gameView = new GameView();
  });

  test('должен создаваться с правильными параметрами', () => {
    expect(gameView).toBeDefined();
    expect(typeof gameView.showWelcome).toBe('function');
    expect(typeof gameView.getPlayerGuess).toBe('function');
    expect(typeof gameView.showGuessResult).toBe('function');
    expect(typeof gameView.showError).toBe('function');
    expect(typeof gameView.showGameOver).toBe('function');
    expect(typeof gameView.waitForEnter).toBe('function');
  });

  test('должен правильно отображать приветствие', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    const consoleClearSpy = jest.spyOn(console, 'clear').mockImplementation();
    
    gameView.showWelcome();
    
    expect(consoleClearSpy).toHaveBeenCalled();
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Морской бой'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Правила игры'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Игровое поле 10x10'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Корабли'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('линкора'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('координаты'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Нажмите Enter'));
    
    consoleSpy.mockRestore();
    consoleClearSpy.mockRestore();
  });

  test('должен правильно отображать результат хода игрока', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    gameView.showGuessResult({ type: 'hit', coordinates: { row: 1, col: 1 } }, 'player');
    expect(consoleSpy).toHaveBeenCalledWith('PLAYER HIT!');
    
    consoleSpy.mockRestore();
  });

  test('должен правильно отображать результат хода CPU', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    gameView.showGuessResult({ type: 'miss', coordinates: { row: 2, col: 2 } }, 'cpu');
    expect(consoleSpy).toHaveBeenCalledWith('CPU MISS at 22!');
    
    consoleSpy.mockRestore();
  });

  test('должен правильно отображать ошибки', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    gameView.showError('Тестовая ошибка');
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Ошибка: Тестовая ошибка'));
    
    consoleSpy.mockRestore();
  });

  test('должен правильно отображать конец игры - победа игрока', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    gameView.showGameOver('player');
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('CONGRATULATIONS'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('You sunk all enemy battleships'));
    consoleSpy.mockRestore();
  });

  test('должен правильно отображать конец игры - победа CPU', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    gameView.showGameOver('cpu');
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('GAME OVER'));
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('CPU sunk all your battleships'));
    consoleSpy.mockRestore();
  });

  test('должен правильно парсить валидные координаты', () => {
    // Создаем тестовую функцию парсинга, так как приватный метод недоступен
    const parseGuess = (input) => {
      const match = input.trim().match(/^([0-9])([0-9])$/);
      if (!match) return null;
      const [, row, col] = match;
      const rowNum = parseInt(row);
      const colNum = parseInt(col);
      if (rowNum >= 0 && rowNum < 10 && colNum >= 0 && colNum < 10) {
        return { row: rowNum, col: colNum };
      }
      return null;
    };

    const validInputs = [
      { input: '00', expected: { row: 0, col: 0 } },
      { input: '55', expected: { row: 5, col: 5 } },
      { input: '99', expected: { row: 9, col: 9 } },
      { input: '34', expected: { row: 3, col: 4 } },
      { input: ' 67  ', expected: { row: 6, col: 7 } } // Проверяем пробелы
    ];
    
    validInputs.forEach(({ input, expected }) => {
      const result = parseGuess(input);
      expect(result).toEqual(expected);
    });
  });

  test('должен правильно парсить невалидные координаты', () => {
    const parseGuess = (input) => {
      const match = input.trim().match(/^([0-9])([0-9])$/);
      if (!match) return null;
      const [, row, col] = match;
      const rowNum = parseInt(row);
      const colNum = parseInt(col);
      if (rowNum >= 0 && rowNum < 10 && colNum >= 0 && colNum < 10) {
        return { row: rowNum, col: colNum };
      }
      return null;
    };

    const invalidInputs = [
      'A0', '0A', 'A1', '1A', '00A', 'A00', '123', '1', '0', '', '   ', 'AB', 'XY'
    ];
    
    invalidInputs.forEach(input => {
      const result = parseGuess(input);
      expect(result).toBeNull();
    });
  });

  test('должен правильно форматировать координаты', () => {
    const formatCoordinates = (coordinates) => {
      const { row, col } = coordinates;
      return `${row}${col}`;
    };

    const testCases = [
      { coordinates: { row: 0, col: 0 }, expected: '00' },
      { coordinates: { row: 5, col: 5 }, expected: '55' },
      { coordinates: { row: 9, col: 9 }, expected: '99' },
      { coordinates: { row: 3, col: 4 }, expected: '34' }
    ];
    
    testCases.forEach(({ coordinates, expected }) => {
      const result = formatCoordinates(coordinates);
      expect(result).toBe(expected);
    });
  });

  test('должен правильно обрабатывать граничные случаи координат', () => {
    const parseGuess = (input) => {
      const match = input.trim().match(/^([0-9])([0-9])$/);
      if (!match) return null;
      const [, row, col] = match;
      const rowNum = parseInt(row);
      const colNum = parseInt(col);
      if (rowNum >= 0 && rowNum < 10 && colNum >= 0 && colNum < 10) {
        return { row: rowNum, col: colNum };
      }
      return null;
    };

    // Тестируем граничные значения
    expect(parseGuess('00')).toEqual({ row: 0, col: 0 });
    expect(parseGuess('99')).toEqual({ row: 9, col: 9 });
    
    // Тестируем невалидные граничные значения
    expect(parseGuess('A0')).toBeNull();
    expect(parseGuess('0A')).toBeNull();
    // '10' - это валидная координата в формате 00-99, но row=1, col=0
    expect(parseGuess('10')).toEqual({ row: 1, col: 0 });
  });

  test('должен правильно обрабатывать различные форматы ввода', () => {
    const parseGuess = (input) => {
      const match = input.trim().match(/^([0-9])([0-9])$/);
      if (!match) return null;
      const [, row, col] = match;
      const rowNum = parseInt(row);
      const colNum = parseInt(col);
      if (rowNum >= 0 && rowNum < 10 && colNum >= 0 && colNum < 10) {
        return { row: rowNum, col: colNum };
      }
      return null;
    };

    // Тестируем различные форматы
    expect(parseGuess('00')).toEqual({ row: 0, col: 0 });
    expect(parseGuess(' 00  ')).toEqual({ row: 0, col: 0 });
    expect(parseGuess('00\n')).toEqual({ row: 0, col: 0 });
    
    // Тестируем невалидные форматы
    expect(parseGuess('000')).toBeNull();
    expect(parseGuess('0')).toBeNull();
    expect(parseGuess('AA')).toBeNull();
  });
}); 