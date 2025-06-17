import { GameController } from '../../controllers/GameController.js';

// Мокаем все зависимости
jest.mock('../../views/GameView.js');
jest.mock('../../models/GameState.js');
jest.mock('../../models/GameAI.js');

describe('GameController', () => {
  let gameController;
  let mockGameState;
  let mockGameView;
  let mockGameAI;

  beforeEach(() => {
    // Очищаем моки перед каждым тестом
    jest.clearAllMocks();
    
    // Создаем моки
    mockGameState = {
      initialize: jest.fn(),
      isGameOver: jest.fn(),
      getPlayerShips: jest.fn(),
      getCPUShips: jest.fn(),
      processPlayerGuess: jest.fn(),
      processCPUGuess: jest.fn()
    };

    mockGameView = {
      showWelcome: jest.fn(),
      showError: jest.fn(),
      showGameOver: jest.fn(),
      getPlayerGuess: jest.fn(),
      showGuessResult: jest.fn(),
      waitForEnter: jest.fn()
    };

    mockGameAI = {
      makeGuess: jest.fn(),
      updateState: jest.fn()
    };

    // Мокаем конструкторы
    const { GameState } = require('../../models/GameState.js');
    const { GameView } = require('../../views/GameView.js');
    const { GameAI } = require('../../models/GameAI.js');

    GameState.mockImplementation(() => mockGameState);
    GameView.mockImplementation(() => mockGameView);
    GameAI.mockImplementation(() => mockGameAI);

    gameController = new GameController();
  });

  test('должен создаваться с правильными компонентами', () => {
    expect(gameController).toBeDefined();
    expect(typeof gameController.start).toBe('function');
  });

  test('должен правильно обрабатывать ошибки инициализации', async () => {
    // Настраиваем моки
    mockGameState.initialize.mockImplementation(() => {
      throw new Error('Тестовая ошибка');
    });

    await expect(gameController.start()).rejects.toThrow('Тестовая ошибка');
    expect(mockGameView.showError).toHaveBeenCalledWith('Тестовая ошибка');
  });

  test('должен правильно обрабатывать победу игрока', async () => {
    // Настраиваем моки
    mockGameState.initialize.mockResolvedValue();
    mockGameState.isGameOver.mockReturnValue(true);
    mockGameState.getPlayerShips.mockReturnValue([{ isSunk: () => false }]);
    mockGameState.getCPUShips.mockReturnValue([{ isSunk: () => true }]);

    await gameController.start();
    expect(mockGameView.showGameOver).toHaveBeenCalledWith('player');
  });

  test('должен правильно обрабатывать победу CPU', async () => {
    // Настраиваем моки
    mockGameState.initialize.mockResolvedValue();
    mockGameState.isGameOver.mockReturnValue(true);
    mockGameState.getPlayerShips.mockReturnValue([{ isSunk: () => true }]);
    mockGameState.getCPUShips.mockReturnValue([{ isSunk: () => false }]);

    await gameController.start();
    expect(mockGameView.showGameOver).toHaveBeenCalledWith('cpu');
  });

  test('должен правильно обрабатывать успешную инициализацию', async () => {
    // Настраиваем моки
    mockGameState.initialize.mockResolvedValue();
    mockGameState.isGameOver.mockReturnValue(true);
    mockGameState.getPlayerShips.mockReturnValue([{ isSunk: () => false }]);
    mockGameState.getCPUShips.mockReturnValue([{ isSunk: () => false }]);

    await gameController.start();
    
    expect(mockGameState.initialize).toHaveBeenCalled();
    expect(mockGameView.showWelcome).toHaveBeenCalled();
  });

  test('должен правильно обрабатывать ничью', async () => {
    // Настраиваем моки
    mockGameState.initialize.mockResolvedValue();
    mockGameState.isGameOver.mockReturnValue(true);
    mockGameState.getPlayerShips.mockReturnValue([{ isSunk: () => true }]);
    mockGameState.getCPUShips.mockReturnValue([{ isSunk: () => true }]);

    await gameController.start();
    // В случае ничьей должен быть вызван showGameOver с 'cpu' (первый проверяемый)
    expect(mockGameView.showGameOver).toHaveBeenCalledWith('cpu');
  });
}); 