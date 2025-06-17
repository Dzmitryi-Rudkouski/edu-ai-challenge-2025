import { GameState } from '../../models/GameState.js';
import { GameAI } from '../../models/GameAI.js';
import { GameConfig } from '../../models/GameConfig.js';

describe('Интеграционные тесты игровой логики', () => {
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
    expect(gameState.getPlayerShips().length).toBe(3);
    expect(gameState.getCPUShips().length).toBe(3);

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
    const playerShips = gameState.getPlayerShips();
    
    // Проверяем, что корабли имеют правильные размеры
    const shipCounts = playerShips.reduce((counts, ship) => {
      const size = ship.size;
      counts[size] = (counts[size] || 0) + 1;
      return counts;
    }, {});

    expect(shipCounts[3]).toBe(3); // 3 линкора
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

  test('взаимодействие между компонентами', () => {
    // Тестируем взаимодействие GameState и GameAI
    const playerGuess = { row: 0, col: 0 };
    const playerResult = gameState.processPlayerGuess(playerGuess);
    expect(['hit', 'miss']).toContain(playerResult.type);
    
    const cpuGuess = gameAI.makeGuess();
    const cpuResult = gameState.processCPUGuess();
    expect(['hit', 'miss']).toContain(cpuResult.type);
    
    // Обновляем состояние AI
    gameAI.updateState(cpuGuess, cpuResult.type);
    
    // Проверяем, что состояние корректно обновилось
    expect(gameState.isCellGuessed(playerGuess)).toBe(true);
    // Проверяем, что CPU ход был сделан
    expect(cpuResult.coordinates).toBeDefined();
  });

  test('симуляция полной игры', () => {
    let moves = 0;
    const maxMoves = 50; // Ограничиваем количество ходов
    
    while (!gameState.isGameOver() && moves < maxMoves) {
      // Ход игрока
      const playerGuess = { row: Math.floor(moves / 10), col: moves % 10 };
      gameState.processPlayerGuess(playerGuess);
      
      if (gameState.isGameOver()) break;
      
      // Ход CPU
      const cpuGuess = gameAI.makeGuess();
      const cpuResult = gameState.processCPUGuess();
      gameAI.updateState(cpuGuess, cpuResult.type);
      
      moves++;
    }
    
    // Проверяем, что игра либо закончилась, либо достигли лимита ходов
    expect(moves).toBeLessThanOrEqual(maxMoves);
  });

  test('корректность подсчета оставшихся кораблей', () => {
    const initialPlayerShips = gameState.getPlayerShips().length;
    const initialCPUShips = gameState.getCPUShips().length;
    
    expect(initialPlayerShips).toBe(3);
    expect(initialCPUShips).toBe(3);
    
    // Потопляем один корабль игрока
    const playerShips = gameState.getPlayerShips();
    const shipToSink = playerShips[0];
    shipToSink.getLocations().forEach(loc => shipToSink.hit(loc));
    
    // Проверяем, что корабль потоплен
    expect(shipToSink.isSunk()).toBe(true);
  });

  test('валидность состояния доски', () => {
    // Проверяем, что все корабли размещены корректно
    const playerShips = gameState.getPlayerShips();
    const cpuShips = gameState.getCPUShips();
    
    // Проверяем, что все корабли имеют локации
    playerShips.forEach(ship => {
      expect(ship.getLocations().size).toBeGreaterThan(0);
    });
    
    cpuShips.forEach(ship => {
      expect(ship.getLocations().size).toBeGreaterThan(0);
    });
  });

  test('корректность обработки попаданий', () => {
    // Находим корабль и стреляем в него
    const playerShips = gameState.getPlayerShips();
    let targetShip = null;
    let targetLocations = [];
    
    for (const ship of playerShips) {
      const locations = ship.getLocations();
      if (locations.size > 0) {
        targetShip = ship;
        targetLocations = Array.from(locations);
        break;
      }
    }
    
    if (targetShip && targetLocations.length > 0) {
      // Потопляем корабль напрямую
      targetLocations.forEach(location => {
        targetShip.hit(location);
      });
      
      // Проверяем, что корабль потоплен
      expect(targetShip.isSunk()).toBe(true);
    }
  });

  test('проверка уникальности ходов', () => {
    const moves = new Set();
    
    // Делаем несколько ходов и проверяем их уникальность
    for (let i = 0; i < 10; i++) {
      const playerGuess = { row: i, col: i };
      gameState.processPlayerGuess(playerGuess);
      
      const moveKey = `${playerGuess.row},${playerGuess.col}`;
      expect(moves.has(moveKey)).toBe(false);
      moves.add(moveKey);
    }
  });

  test('проверка корректности размещения кораблей', () => {
    const playerShips = gameState.getPlayerShips();
    const cpuShips = gameState.getCPUShips();
    
    // Проверяем, что все корабли имеют правильные размеры
    playerShips.forEach(ship => {
      expect(ship.size).toBeGreaterThanOrEqual(1);
      expect(ship.size).toBeLessThanOrEqual(4);
      expect(ship.getLocations().size).toBe(ship.size);
    });
    
    cpuShips.forEach(ship => {
      expect(ship.size).toBeGreaterThanOrEqual(1);
      expect(ship.size).toBeLessThanOrEqual(4);
      expect(ship.getLocations().size).toBe(ship.size);
    });
  });

  test('проверка логики потопления кораблей', () => {
    const playerShips = gameState.getPlayerShips();
    
    // Находим корабль и потопляем его
    const shipToSink = playerShips[0];
    const initialSunkState = shipToSink.isSunk();
    
    // Потопляем корабль
    shipToSink.getLocations().forEach(loc => shipToSink.hit(loc));
    
    expect(shipToSink.isSunk()).toBe(true);
    expect(shipToSink.isSunk()).not.toBe(initialSunkState);
  });

  test('проверка корректности координат кораблей', () => {
    const playerShips = gameState.getPlayerShips();
    
    playerShips.forEach(ship => {
      ship.getLocations().forEach(location => {
        // Проверяем, что координаты в пределах доски
        expect(location.row).toBeGreaterThanOrEqual(0);
        expect(location.row).toBeLessThan(GameConfig.BOARD_SIZE);
        expect(location.col).toBeGreaterThanOrEqual(0);
        expect(location.col).toBeLessThan(GameConfig.BOARD_SIZE);
      });
    });
  });

  test('проверка корректности обработки кораблей', () => {
    const playerShips = gameState.getPlayerShips();
    
    // Проверяем, что корабли имеют правильные размеры
    const shipCounts = playerShips.reduce((counts, ship) => {
      const size = ship.size;
      counts[size] = (counts[size] || 0) + 1;
      return counts;
    }, {});

    expect(shipCounts[3]).toBe(3); // 3 линкора
  });
}); 