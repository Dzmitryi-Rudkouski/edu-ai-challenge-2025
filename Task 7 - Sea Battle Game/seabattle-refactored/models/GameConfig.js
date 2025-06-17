/**
 * Конфигурация игры "Морской бой"
 * Содержит все настройки и константы игры
 */
export class GameConfig {
  static BOARD_SIZE = 10;
  static SHIPS = [
    { type: 'battleship', size: 3, count: 3 }
  ];
  static TOTAL_SHIPS = 3;

  /** Символы для отображения состояния клетки */
  static SYMBOLS = {
    EMPTY: '·',   // Пустая клетка
    SHIP: '■',    // Корабль
    HIT: 'X',     // Попадание
    MISS: '○',    // Промах
    HIDDEN: '□'   // Скрытая клетка
  };

  /** Максимальное количество попыток размещения корабля */
  static MAX_PLACEMENT_ATTEMPTS = 100;

  /** Сообщения об ошибках */
  static ERROR_MESSAGES = {
    INVALID_COORDINATES: 'Недопустимые координаты',
    INVALID_SHIP_PLACEMENT: 'Недопустимое размещение корабля',
    GAME_NOT_INITIALIZED: 'Игра не инициализирована',
    INVALID_MOVE: 'Недопустимый ход',
    GAME_OVER: 'Игра окончена'
  };
} 