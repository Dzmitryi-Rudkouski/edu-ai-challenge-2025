/**
 * Все тесты проекта "Морской бой"
 * Этот файл объединяет все модульные и интеграционные тесты
 */

import { GameConfig } from '../models/GameConfig.js';
import { GameState } from '../models/GameState.js';
import { GameAI } from '../models/GameAI.js';
import { Ship } from '../models/Ship.js';

// Модульные тесты для GameConfig
describe('GameConfig', () => {
  test('должен иметь правильные настройки игры', () => {
    expect(GameConfig.BOARD_SIZE).toBe(10);
    expect(GameConfig.SHIPS).toEqual([
      { size: 4, count: 1 }, // Линкор
      { size: 3, count: 2 }, // Крейсер
      { size: 2, count: 3 }, // Эсминец
      { size: 1, count: 4 }  // Катер
    ]);
  });

  test('должен иметь правильные символы для отображения', () => {
    expect(GameConfig.SYMBOLS).toEqual({
      EMPTY: '·',
      SHIP: '■',
      HIT: 'X',
      MISS: '○',
      HIDDEN: '□'
    });
  });
});

// Модульные тесты для Ship
describe('Ship', () => {
  let ship;

  beforeEach(() => {
    ship = new Ship(3); // Создаем крейсер
  });

  test('должен создаваться с правильными параметрами', () => {
    expect(ship.size).toBe(3);
    expect(ship.isSunk()).toBe(false);
    expect(ship.getHits()).toEqual(new Set());
  });

  test('должен правильно обрабатывать попадания', () => {
    const location = { row: 1, col: 1 };
    ship.addLocation(location);
    ship.hit(location);
    expect(ship.getHits().size).toBe(1);
    expect(ship.isHit(location)).toBe(true);
  });

  test('должен правильно определять потопление', () => {
    const locations = [
      { row: 1, col: 1 },
      { row: 1, col: 2 },
      { row: 1, col: 3 }
    ];
    locations.forEach(loc => {
      ship.addLocation(loc);
      ship.hit(loc);
    });
    expect(ship.isSunk()).toBe(true);
  });

  test('должен проверять валидность координат', () => {
    const validLoc = { row: 1, col: 1 };
    const invalidLoc = { row: -1, col: 11 };
    
    expect(() => ship.addLocation(validLoc)).not.toThrow();
    expect(() => ship.addLocation(invalidLoc)).toThrow('Недопустимые координаты');
  });
});

// Модульные тесты для GameState
describe('GameState', () => {
  let gameState;

  beforeEach(() => {
    gameState = new GameState();
  });

  test('должен инициализировать игру', () => {
    expect(gameState.isInitialized()).toBe(false);
    gameState.initialize();
    expect(gameState.isInitialized()).toBe(true);
  });

  test('должен правильно размещать корабли', () => {
    gameState.initialize();
    const ships = gameState.getPlayerShips();
    expect(ships.length).toBe(10); // 1 линкор + 2 крейсера + 3 эсминца + 4 катера
  });

  test('должен правильно обрабатывать ходы игрока', () => {
    gameState.initialize();
    const result = gameState.processPlayerGuess({ row: 0, col: 0 });
    expect(['hit', 'miss']).toContain(result.type);
  });

  test('должен правильно обрабатывать ходы CPU', () => {
    gameState.initialize();
    const result = gameState.processCPUGuess();
    expect(['hit', 'miss']).toContain(result.type);
    expect(result.coordinates).toBeDefined();
  });

  test('должен определять конец игры', () => {
    gameState.initialize();
    expect(gameState.isGameOver()).toBe(false);
    // Симулируем потопление всех кораблей
    gameState.getPlayerShips().forEach(ship => {
      ship.getLocations().forEach(loc => ship.hit(loc));
    });
    expect(gameState.isGameOver()).toBe(true);
  });
});

// Модульные тесты для GameAI
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
    expect(gameAI.lastHit).toEqual(guess);
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
});

// Интеграционные тесты
describe('Интеграционные тесты', () => {
  let gameState;
  let gameAI;

  beforeEach(() => {
    gameState = new GameState();
    gameAI = new GameAI(gameState);
    gameState.initialize();
  });

  test('полный игровой процесс', () => {
    // Проверяем начальное состояние
    expect(gameState.isInitialized()).toBe(true);
    expect(gameState.getPlayerShips().length).toBe(10);
    expect(gameState.getCPUShips().length).toBe(10);

    // Симулируем несколько ходов
    for (let i = 0; i < 5; i++) {
      const playerGuess = { row: i, col: i };
      const playerResult = gameState.processPlayerGuess(playerGuess);
      expect(['hit', 'miss']).toContain(playerResult.type);

      const cpuGuess = gameAI.makeGuess();
      const cpuResult = gameState.processCPUGuess();
      expect(['hit', 'miss']).toContain(cpuResult.type);
      gameAI.updateState(cpuGuess, cpuResult.type);
    }
  });

  test('правила размещения кораблей', () => {
    const ships = gameState.getPlayerShips();
    const locations = new Set();

    // Проверяем, что корабли не пересекаются
    ships.forEach(ship => {
      ship.getLocations().forEach(loc => {
        const key = `${loc.row},${loc.col}`;
        expect(locations.has(key)).toBe(false);
        locations.add(key);
      });
    });

    // Проверяем количество кораблей каждого типа
    const shipCounts = ships.reduce((acc, ship) => {
      acc[ship.size] = (acc[ship.size] || 0) + 1;
      return acc;
    }, {});

    expect(shipCounts[4]).toBe(1); // 1 линкор
    expect(shipCounts[3]).toBe(2); // 2 крейсера
    expect(shipCounts[2]).toBe(3); // 3 эсминца
    expect(shipCounts[1]).toBe(4); // 4 катера
  });

  test('обработка граничных случаев', () => {
    // Попытка хода вне доски
    expect(() => gameState.processPlayerGuess({ row: -1, col: 0 })).toThrow();
    expect(() => gameState.processPlayerGuess({ row: 0, col: 10 })).toThrow();

    // Попытка повторного хода
    const guess = { row: 0, col: 0 };
    gameState.processPlayerGuess(guess);
    expect(() => gameState.processPlayerGuess(guess)).toThrow();

    // Попытка хода до инициализации
    const newGameState = new GameState();
    expect(() => newGameState.processPlayerGuess(guess)).toThrow();
  });
}); 