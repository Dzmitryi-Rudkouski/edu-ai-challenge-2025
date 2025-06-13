import { GameController } from './controllers/GameController.js';

/**
 * Точка входа в игру
 */
async function main() {
  try {
    const game = new GameController();
    await game.start();
  } catch (error) {
    console.error('Критическая ошибка:', error.message);
    process.exit(1);
  }
}

// Запуск игры
main(); 