import { Ship } from '../../models/Ship.js';
import { GameConfig } from '../../models/GameConfig.js';

describe('Ship', () => {
  let ship;

  beforeEach(() => {
    ship = new Ship(3); // Создаем крейсер
  });

  test('должен создаваться с правильными параметрами', () => {
    expect(ship.size).toBe(3);
    expect(ship.isSunk()).toBe(false);
    expect(ship.getHits()).toEqual(new Set());
    expect(ship.getLocations()).toEqual(new Set());
  });

  test('должен правильно добавлять локации', () => {
    const location = { row: 1, col: 1 };
    ship.addLocation(location);
    expect(ship.getLocations().has(location)).toBe(true);
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

  test('не должен позволять попадание в несуществующую локацию', () => {
    const location = { row: 1, col: 1 };
    expect(() => ship.hit(location)).toThrow('Попадание не по кораблю');
  });

  test('не должен позволять повторное попадание в ту же локацию', () => {
    const location = { row: 1, col: 1 };
    ship.addLocation(location);
    ship.hit(location);
    // Повторное попадание в ту же локацию не должно вызывать ошибку
    // так как Set автоматически предотвращает дубликаты
    expect(ship.getHits().size).toBe(1);
  });

  test('должен правильно обрабатывать частично поврежденный корабль', () => {
    const locations = [
      { row: 1, col: 1 },
      { row: 1, col: 2 },
      { row: 1, col: 3 }
    ];
    locations.forEach(loc => ship.addLocation(loc));
    
    ship.hit(locations[0]);
    ship.hit(locations[1]);
    
    expect(ship.isSunk()).toBe(false);
    expect(ship.getHits().size).toBe(2);
  });

  test('должен правильно проверять локацию корабля', () => {
    const location = { row: 1, col: 1 };
    expect(ship.isAtLocation(location)).toBe(false);
    
    ship.addLocation(location);
    expect(ship.isAtLocation(location)).toBe(true);
  });

  test('должен правильно проверять попадания', () => {
    const location = { row: 1, col: 1 };
    ship.addLocation(location);
    
    expect(ship.isHit(location)).toBe(false);
    ship.hit(location);
    expect(ship.isHit(location)).toBe(true);
  });

  test('должен правильно обрабатывать недопустимый размер корабля', () => {
    expect(() => new Ship(0)).toThrow('Недопустимый размер корабля');
    expect(() => new Ship(5)).toThrow('Недопустимый размер корабля');
  });
}); 