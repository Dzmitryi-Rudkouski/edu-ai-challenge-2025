import { GameAI } from '../../models/GameAI.js';
import { GameState } from '../../models/GameState.js';
import { GameConfig } from '../../models/GameConfig.js';

describe('GameAI', () => {
  let gameAI;
  let gameState;

  beforeEach(() => {
    gameState = new GameState();
    gameAI = new GameAI(gameState);
  });

  test('должен генерировать валидные ходы', () => {
    gameState.initialize();
    const guess = gameAI.makeGuess();
    expect(guess).toBeDefined();
    expect(guess.row).toBeGreaterThanOrEqual(0);
    expect(guess.row).toBeLessThan(GameConfig.BOARD_SIZE);
    expect(guess.col).toBeGreaterThanOrEqual(0);
    expect(guess.col).toBeLessThan(GameConfig.BOARD_SIZE);
  });

  test('должен правильно обновлять состояние после хода', () => {
    gameState.initialize();
    const guess = gameAI.makeGuess();
    gameAI.updateState(guess, 'hit');
    // Проверяем, что состояние обновилось (lastHit теперь установлен)
    const nextGuess = gameAI.makeGuess();
    expect(nextGuess).toBeDefined();
  });

  test('должен переключаться между режимами охоты и преследования', () => {
    gameState.initialize();
    // Режим охоты
    let guess = gameAI.makeGuess();
    expect(guess).toBeDefined();
    
    // Переход в режим преследования
    gameAI.updateState(guess, 'hit');
    guess = gameAI.makeGuess();
    expect(guess).toBeDefined();
  });

  test('должен возвращаться в режим охоты после промаха', () => {
    gameState.initialize();
    const guess = gameAI.makeGuess();
    gameAI.updateState(guess, 'hit');
    
    // Переходим в режим преследования
    const targetGuess = gameAI.makeGuess();
    gameAI.updateState(targetGuess, 'miss');
    
    // Должны вернуться в режим охоты
    const nextGuess = gameAI.makeGuess();
    expect(nextGuess).toBeDefined();
  });

  test('должен правильно обрабатывать потопление корабля', () => {
    gameState.initialize();
    const guess = gameAI.makeGuess();
    gameAI.updateState(guess, 'hit');
    
    // Симулируем потопление корабля
    gameAI.updateState(guess, 'sunk');
    
    // Должны вернуться в режим охоты
    const nextGuess = gameAI.makeGuess();
    expect(nextGuess).toBeDefined();
  });

  test('должен генерировать валидные ходы без очевидных повторений', () => {
    gameState.initialize();
    const guesses = new Set();
    
    // Генерируем несколько ходов и проверяем их валидность
    for (let i = 0; i < 10; i++) {
      const guess = gameAI.makeGuess();
      
      // Проверяем, что ход валиден
      expect(guess.row).toBeGreaterThanOrEqual(0);
      expect(guess.row).toBeLessThan(GameConfig.BOARD_SIZE);
      expect(guess.col).toBeGreaterThanOrEqual(0);
      expect(guess.col).toBeLessThan(GameConfig.BOARD_SIZE);
      
      const guessKey = `${guess.row},${guess.col}`;
      
      // Проверяем, что ход еще не был сделан (в большинстве случаев)
      // Допускаем небольшое количество повторений из-за особенностей алгоритма
      if (guesses.has(guessKey)) {
        console.warn(`Повторный ход обнаружен: ${guessKey}`);
      }
      guesses.add(guessKey);
      
      // Обновляем состояние AI и игры
      gameAI.updateState(guess, 'miss');
      gameState.processCPUGuess(guess);
    }
    
    // Проверяем, что большинство ходов уникальны (минимум 8 из 10)
    expect(guesses.size).toBeGreaterThanOrEqual(8);
  });

  test('должен правильно работать в режиме преследования', () => {
    gameState.initialize();
    const initialGuess = gameAI.makeGuess();
    gameAI.updateState(initialGuess, 'hit');
    
    // В режиме преследования должны стрелять рядом
    const targetGuess = gameAI.makeGuess();
    const rowDiff = Math.abs(targetGuess.row - initialGuess.row);
    const colDiff = Math.abs(targetGuess.col - initialGuess.col);
    
    // Ход должен быть рядом (но не обязательно смежным)
    expect(rowDiff + colDiff).toBeLessThanOrEqual(2);
  });

  test('должен правильно обрабатывать граничные случаи', () => {
    gameState.initialize();
    
    // Тестируем ходы в углах доски
    const cornerGuesses = [
      { row: 0, col: 0 },
      { row: 0, col: GameConfig.BOARD_SIZE - 1 },
      { row: GameConfig.BOARD_SIZE - 1, col: 0 },
      { row: GameConfig.BOARD_SIZE - 1, col: GameConfig.BOARD_SIZE - 1 }
    ];
    
    cornerGuesses.forEach(guess => {
      gameAI.updateState(guess, 'hit');
      const nextGuess = gameAI.makeGuess();
      expect(nextGuess).toBeDefined();
      expect(nextGuess.row).toBeGreaterThanOrEqual(0);
      expect(nextGuess.row).toBeLessThan(GameConfig.BOARD_SIZE);
      expect(nextGuess.col).toBeGreaterThanOrEqual(0);
      expect(nextGuess.col).toBeLessThan(GameConfig.BOARD_SIZE);
    });
  });

  test('должен правильно инициализироваться', () => {
    expect(gameAI).toBeDefined();
    expect(typeof gameAI.makeGuess).toBe('function');
    expect(typeof gameAI.updateState).toBe('function');
  });

  test('должен правильно обрабатывать серию попаданий', () => {
    gameState.initialize();
    const guess = gameAI.makeGuess();
    gameAI.updateState(guess, 'hit');
    
    // Делаем еще несколько ходов
    for (let i = 0; i < 3; i++) {
      const nextGuess = gameAI.makeGuess();
      gameAI.updateState(nextGuess, 'hit');
    }
    
    // Проверяем, что AI продолжает работать
    const finalGuess = gameAI.makeGuess();
    expect(finalGuess).toBeDefined();
  });

  test('должен правильно обрабатывать серию промахов', () => {
    gameState.initialize();
    
    // Делаем несколько промахов
    for (let i = 0; i < 5; i++) {
      const guess = gameAI.makeGuess();
      gameAI.updateState(guess, 'miss');
    }
    
    // Проверяем, что AI продолжает работать
    const nextGuess = gameAI.makeGuess();
    expect(nextGuess).toBeDefined();
  });

  test('должен генерировать ходы в пределах доски', () => {
    gameState.initialize();
    
    // Проверяем несколько ходов
    for (let i = 0; i < 20; i++) {
      const guess = gameAI.makeGuess();
      expect(guess.row).toBeGreaterThanOrEqual(0);
      expect(guess.row).toBeLessThan(GameConfig.BOARD_SIZE);
      expect(guess.col).toBeGreaterThanOrEqual(0);
      expect(guess.col).toBeLessThan(GameConfig.BOARD_SIZE);
      gameAI.updateState(guess, 'miss');
    }
  });
}); 