import { GameConfig } from '../../models/GameConfig.js';

describe('GameConfig', () => {
  test('должен иметь правильные настройки игры', () => {
    expect(GameConfig.BOARD_SIZE).toBe(10);
    expect(GameConfig.SHIPS).toEqual([
      { type: 'battleship', size: 3, count: 3 }
    ]);
  });

  test('должен иметь правильное общее количество кораблей', () => {
    const totalShips = GameConfig.SHIPS.reduce((sum, ship) => sum + ship.count, 0);
    expect(totalShips).toBe(3);
  });

  test('должен иметь правильные размеры кораблей', () => {
    const sizes = GameConfig.SHIPS.map(ship => ship.size);
    expect(sizes).toEqual([3]);
  });

  test('должен иметь правильные символы', () => {
    expect(GameConfig.SYMBOLS.EMPTY).toBe('·');
    expect(GameConfig.SYMBOLS.SHIP).toBe('■');
    expect(GameConfig.SYMBOLS.HIT).toBe('X');
    expect(GameConfig.SYMBOLS.MISS).toBe('○');
    expect(GameConfig.SYMBOLS.HIDDEN).toBe('□');
  });

  test('должен иметь правильные сообщения об ошибках', () => {
    expect(GameConfig.ERROR_MESSAGES.INVALID_COORDINATES).toBe('Недопустимые координаты');
    expect(GameConfig.ERROR_MESSAGES.INVALID_SHIP_PLACEMENT).toBe('Недопустимое размещение корабля');
    expect(GameConfig.ERROR_MESSAGES.GAME_NOT_INITIALIZED).toBe('Игра не инициализирована');
    expect(GameConfig.ERROR_MESSAGES.INVALID_MOVE).toBe('Недопустимый ход');
    expect(GameConfig.ERROR_MESSAGES.GAME_OVER).toBe('Игра окончена');
  });

  test('должен иметь правильное максимальное количество попыток размещения', () => {
    expect(GameConfig.MAX_PLACEMENT_ATTEMPTS).toBe(100);
  });
}); 