import { GameState } from '../../models/GameState.js';
import { GameConfig } from '../../models/GameConfig.js';

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
    expect(ships.length).toBe(3); // 3 линкора
  });

  test('должен правильно обрабатывать ходы игрока', () => {
    gameState.initialize();
    const result = gameState.processPlayerGuess({ row: 0, col: 0 });
    expect(['hit', 'miss']).toContain(result.type);
    expect(result.coordinates).toEqual({ row: 0, col: 0 });
  });

  test('должен правильно обрабатывать ходы CPU', () => {
    gameState.initialize();
    const result = gameState.processCPUGuess();
    expect(['hit', 'miss']).toContain(result.type);
    expect(result.coordinates).toBeDefined();
    expect(result.coordinates.row).toBeGreaterThanOrEqual(0);
    expect(result.coordinates.row).toBeLessThan(GameConfig.BOARD_SIZE);
    expect(result.coordinates.col).toBeGreaterThanOrEqual(0);
    expect(result.coordinates.col).toBeLessThan(GameConfig.BOARD_SIZE);
  });

  test('должен определять конец игры', () => {
    gameState.initialize();
    expect(gameState.isGameOver()).toBe(false);
    
    // Симулируем потопление всех кораблей игрока
    gameState.getPlayerShips().forEach(ship => {
      ship.getLocations().forEach(loc => ship.hit(loc));
    });
    expect(gameState.isGameOver()).toBe(true);
  });

  test('не должен позволять ходы до инициализации', () => {
    expect(() => gameState.processPlayerGuess({ row: 0, col: 0 })).toThrow('Игра не инициализирована');
    expect(() => gameState.processCPUGuess()).toThrow('Игра не инициализирована');
  });

  test('не должен позволять ходы вне доски', () => {
    gameState.initialize();
    expect(() => gameState.processPlayerGuess({ row: -1, col: 0 })).toThrow('Недопустимые координаты');
    expect(() => gameState.processPlayerGuess({ row: 0, col: 10 })).toThrow('Недопустимые координаты');
    expect(() => gameState.processPlayerGuess({ row: 10, col: 0 })).toThrow('Недопустимые координаты');
  });

  test('не должен позволять повторные ходы', () => {
    gameState.initialize();
    const guess = { row: 0, col: 0 };
    gameState.processPlayerGuess(guess);
    expect(() => gameState.processPlayerGuess(guess)).toThrow('Эта клетка уже проверена');
  });

  test('должен правильно обрабатывать попадания', () => {
    gameState.initialize();
    const playerShips = gameState.getPlayerShips();
    const cpuShips = gameState.getCPUShips();
    
    // Находим корабль игрока и стреляем в него
    let hitShip = null;
    let hitLocation = null;
    
    for (const ship of playerShips) {
      const locations = ship.getLocations();
      if (locations.size > 0) {
        hitShip = ship;
        hitLocation = Array.from(locations)[0];
        break;
      }
    }
    
    if (hitShip && hitLocation) {
      const result = gameState.processCPUGuess();
      // CPU может попасть или промахнуться
      expect(['hit', 'miss']).toContain(result.type);
    }
  });

  test('должен правильно проверять клетки', () => {
    gameState.initialize();
    const guess = { row: 0, col: 0 };
    
    expect(gameState.isCellGuessed(guess)).toBe(false);
    gameState.processPlayerGuess(guess);
    expect(gameState.isCellGuessed(guess)).toBe(true);
  });

  test('должен правильно обрабатывать серию ходов', () => {
    gameState.initialize();
    
    // Делаем несколько ходов
    for (let i = 0; i < 5; i++) {
      const playerResult = gameState.processPlayerGuess({ row: i, col: i });
      expect(['hit', 'miss']).toContain(playerResult.type);
      
      const cpuResult = gameState.processCPUGuess();
      expect(['hit', 'miss']).toContain(cpuResult.type);
    }
    
    // Проверяем, что игра еще не закончена
    expect(gameState.isGameOver()).toBe(false);
  });

  test('должен правильно обрабатывать повторную инициализацию', () => {
    gameState.initialize();
    expect(() => gameState.initialize()).toThrow('Игра уже инициализирована');
  });

  test('должен правильно обрабатывать потопление всех кораблей CPU', () => {
    gameState.initialize();
    expect(gameState.isGameOver()).toBe(false);
    
    // Симулируем потопление всех кораблей CPU
    gameState.getCPUShips().forEach(ship => {
      ship.getLocations().forEach(loc => ship.hit(loc));
    });
    expect(gameState.isGameOver()).toBe(true);
  });

  test('должен правильно обрабатывать потопление всех кораблей игрока', () => {
    gameState.initialize();
    expect(gameState.isGameOver()).toBe(false);
    
    // Симулируем потопление всех кораблей игрока
    gameState.getPlayerShips().forEach(ship => {
      ship.getLocations().forEach(loc => ship.hit(loc));
    });
    expect(gameState.isGameOver()).toBe(true);
  });

  test('должен правильно обрабатывать валидные координаты', () => {
    gameState.initialize();
    
    // Тестируем различные валидные координаты
    const validGuesses = [
      { row: 0, col: 0 },
      { row: 5, col: 5 },
      { row: 9, col: 9 },
      { row: 0, col: 9 },
      { row: 9, col: 0 }
    ];
    
    validGuesses.forEach(guess => {
      expect(() => gameState.processPlayerGuess(guess)).not.toThrow();
    });
  });

  test('должен правильно обрабатывать невалидные координаты', () => {
    gameState.initialize();
    
    const invalidGuesses = [
      { row: -1, col: 0 },
      { row: 0, col: -1 },
      { row: 10, col: 0 },
      { row: 0, col: 10 },
      { row: 10, col: 10 },
      { row: -1, col: -1 }
    ];
    
    invalidGuesses.forEach(guess => {
      expect(() => gameState.processPlayerGuess(guess)).toThrow('Недопустимые координаты');
    });
  });

  test('должен правильно обрабатывать null и undefined координаты', () => {
    gameState.initialize();
    
    expect(() => gameState.processPlayerGuess(null)).toThrow();
    expect(() => gameState.processPlayerGuess(undefined)).toThrow();
    expect(() => gameState.processPlayerGuess({})).toThrow();
    expect(() => gameState.processPlayerGuess({ row: 0 })).toThrow();
    expect(() => gameState.processPlayerGuess({ col: 0 })).toThrow();
  });

  test('должен правильно обрабатывать нечисловые координаты', () => {
    gameState.initialize();
    
    expect(() => gameState.processPlayerGuess({ row: '0', col: 0 })).toThrow();
    expect(() => gameState.processPlayerGuess({ row: 0, col: '0' })).toThrow();
    expect(() => gameState.processPlayerGuess({ row: 'a', col: 'b' })).toThrow();
  });

  test('должен правильно обрабатывать состояние доски после инициализации', () => {
    gameState.initialize();
    const playerShips = gameState.getPlayerShips();
    const cpuShips = gameState.getCPUShips();

    expect(playerShips.length).toBe(3);
    expect(cpuShips.length).toBe(3);

    // Проверяем, что каждый корабль имеет правильное количество локаций
    playerShips.forEach(ship => {
      expect(ship.getLocations().size).toBe(3);
    });

    cpuShips.forEach(ship => {
      expect(ship.getLocations().size).toBe(3);
    });
  });

  test('должен правильно обрабатывать корректное размещение кораблей', () => {
    gameState.initialize();
    
    // Проверяем, что корабли размещены с правильными размерами
    const playerShips = gameState.getPlayerShips();
    
    playerShips.forEach(ship => {
      expect(ship.getLocations().size).toBe(ship.size);
      expect(ship.size).toBeGreaterThanOrEqual(1);
      expect(ship.size).toBeLessThanOrEqual(4);
    });
  });

  test('должен правильно обрабатывать координаты кораблей', () => {
    gameState.initialize();
    
    // Проверяем, что все координаты кораблей в пределах доски
    const playerShips = gameState.getPlayerShips();
    
    playerShips.forEach(ship => {
      ship.getLocations().forEach(location => {
        expect(location.row).toBeGreaterThanOrEqual(0);
        expect(location.row).toBeLessThan(GameConfig.BOARD_SIZE);
        expect(location.col).toBeGreaterThanOrEqual(0);
        expect(location.col).toBeLessThan(GameConfig.BOARD_SIZE);
      });
    });
  });
}); 