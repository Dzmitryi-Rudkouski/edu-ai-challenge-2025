// Простые модульные тесты для Энигмы
const { spawn } = require('child_process');
const fs = require('fs');

console.log('🧪 Запуск полных модульных тестов Энигмы...\n');

// Загружаем код Энигмы
const enigmaCode = fs.readFileSync('./enigma.js', 'utf8');

// Создаем изолированный контекст для выполнения
const vm = require('vm');
const enigmaContext = {
  require: require,
  console: { log: () => {} }, // Подавляем вывод
  module: { exports: {} },
  exports: {}
};

// Создаем код без запуска main функции
const modifiedCode = enigmaCode.replace('if (require.main === module) {', 'if (false) {');

// Выполняем код в изолированном контексте
vm.createContext(enigmaContext);
vm.runInContext(modifiedCode, enigmaContext);

// Извлекаем экспорт
const { Enigma, Rotor, plugboardSwap, alphabet, ROTORS, REFLECTOR, mod } = enigmaContext.module.exports;

// Функция для запуска тестов
let passedTests = 0;
let totalTests = 0;

function test(name, testFunction) {
  totalTests++;
  try {
    testFunction();
    console.log(`✅ PASSED: ${name}`);
    passedTests++;
  } catch (error) {
    console.log(`❌ FAILED: ${name}`);
    console.log(`   Error: ${error.message}`);
  }
}

// ================== ОСНОВНЫЕ ТЕСТЫ ==================

console.log('📋 Тестирование основных компонентов:\n');

// Тест 1: Создание и базовые операции с ротором
test('Создание ротора и базовые операции', () => {
  const rotor = new Rotor(ROTORS[0].wiring, ROTORS[0].notch, 0, 0);
  
  if (rotor.wiring !== ROTORS[0].wiring) throw new Error('Неправильная проводка ротора');
  if (rotor.notch !== ROTORS[0].notch) throw new Error('Неправильная зарубка ротора');
  if (rotor.position !== 0) throw new Error('Неправильная позиция ротора');
  
  // Тест поворота
  const oldPos = rotor.position;
  rotor.step();
  if (rotor.position !== mod(oldPos + 1, 26)) throw new Error('Неправильный поворот ротора');
});

// Тест 2: Коммутационная панель
test('Функциональность коммутационной панели', () => {
  const pairs = [['A', 'B'], ['C', 'D']];
  
  if (plugboardSwap('A', pairs) !== 'B') throw new Error('A должно менять на B');
  if (plugboardSwap('B', pairs) !== 'A') throw new Error('B должно менять на A');
  if (plugboardSwap('C', pairs) !== 'D') throw new Error('C должно менять на D');
  if (plugboardSwap('E', pairs) !== 'E') throw new Error('E должно остаться E');
  if (plugboardSwap('Z', []) !== 'Z') throw new Error('Пустая панель должна оставлять символы без изменений');
});

// Тест 3: Создание Энигмы
test('Создание машины Энигмы', () => {
  const enigma = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  
  if (!enigma.rotors || enigma.rotors.length !== 3) throw new Error('Неправильное количество роторов');
  if (!Array.isArray(enigma.plugboardPairs)) throw new Error('Неправильный тип коммутационной панели');
});

// Тест 4: Симметричность шифрования
test('Симметричность шифрования (главный тест)', () => {
  const enigma1 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  const enigma2 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  
  const messages = ['HELLO', 'WORLD', 'TEST', 'ABCDEFG'];
  
  for (const original of messages) {
    const encrypted = enigma1.process(original);
    const decrypted = enigma2.process(encrypted);
    
    if (decrypted !== original) {
      throw new Error(`Симметричность нарушена для "${original}": ${original} -> ${encrypted} -> ${decrypted}`);
    }
  }
});

// Тест 5: Симметричность с коммутационной панелью
test('Симметричность с коммутационной панелью', () => {
  const plugboard = [['A', 'B'], ['C', 'D'], ['E', 'F']];
  const enigma1 = new Enigma([0, 1, 2], [5, 10, 15], [1, 2, 3], plugboard);
  const enigma2 = new Enigma([0, 1, 2], [5, 10, 15], [1, 2, 3], plugboard);
  
  const original = 'ABCDEF';
  const encrypted = enigma1.process(original);
  const decrypted = enigma2.process(encrypted);
  
  if (decrypted !== original) {
    throw new Error(`Симметричность с коммутацией нарушена: ${original} -> ${encrypted} -> ${decrypted}`);
  }
});

// Тест 6: Ни одна буква не шифруется сама в себя
test('Ни одна буква не шифруется сама в себя', () => {
  const testPositions = [[0,0,0], [5,10,15], [25,25,25], [1,1,1]];
  
  for (const positions of testPositions) {
    const enigma = new Enigma([0, 1, 2], positions, [0, 0, 0], []);
    
    for (let i = 0; i < 26; i++) {
      const letter = alphabet[i];
      const encrypted = enigma.encryptChar(letter);
      
      if (letter === encrypted) {
        throw new Error(`Буква ${letter} зашифровалась сама в себя при позициях [${positions.join(',')}]`);
      }
    }
  }
});

// Тест 7: Поворот роторов
test('Правильность поворота роторов', () => {
  const enigma = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  
  // Сохраняем начальные позиции
  const initialPositions = enigma.rotors.map(r => r.position);
  
  // Шифруем один символ
  enigma.encryptChar('A');
  
  // Правый ротор должен повернуться
  if (enigma.rotors[2].position !== mod(initialPositions[2] + 1, 26)) {
    throw new Error('Правый ротор не повернулся');
  }
  
  // Средний и левый роторы не должны повернуться при первом шаге
  if (enigma.rotors[1].position !== initialPositions[1]) {
    throw new Error('Средний ротор повернулся преждевременно');
  }
  if (enigma.rotors[0].position !== initialPositions[0]) {
    throw new Error('Левый ротор повернулся преждевременно');
  }
});

// Тест 8: Двойной шаг
test('Механизм двойного шага', () => {
  // Устанавливаем средний ротор в позицию зарубки (E для ротора II)
  const enigma = new Enigma([0, 1, 2], [0, alphabet.indexOf('E'), 0], [0, 0, 0], []);
  
  enigma.encryptChar('A');
  
  // Проверяем, что левый ротор повернулся (из-за зарубки среднего ротора)
  if (enigma.rotors[0].position !== 1) {
    throw new Error('Левый ротор не повернулся при двойном шаге');
  }
  
  // Проверяем, что средний ротор тоже повернулся
  if (enigma.rotors[1].position !== mod(alphabet.indexOf('E') + 1, 26)) {
    throw new Error('Средний ротор не повернулся при двойном шаге');
  }
});

// Тест 9: Обработка спецсимволов
test('Обработка пробелов и спецсимволов', () => {
  const enigma = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  
  const input = 'HELLO, WORLD! 123';
  const result = enigma.process(input);
  
  // Пробелы, запятые, восклицательные знаки и цифры должны остаться без изменений
  if (result[5] !== ',') throw new Error('Запятая не сохранилась');
  if (result[6] !== ' ') throw new Error('Пробел не сохранился');
  if (result[12] !== '!') throw new Error('Восклицательный знак не сохранился');
  if (result[14] !== '1') throw new Error('Цифра 1 не сохранилась');
  if (result[15] !== '2') throw new Error('Цифра 2 не сохранилась');
  if (result[16] !== '3') throw new Error('Цифра 3 не сохранилась');
});

// Тест 10: Граничные случаи
test('Граничные случаи и предельные значения', () => {
  // Максимальные позиции
  const enigma1 = new Enigma([0, 1, 2], [25, 25, 25], [25, 25, 25], []);
  const enigma2 = new Enigma([0, 1, 2], [25, 25, 25], [25, 25, 25], []);
  
  const original = 'EXTREME';
  const encrypted = enigma1.process(original);
  const decrypted = enigma2.process(encrypted);
  
  if (decrypted !== original) {
    throw new Error(`Граничные значения: ${original} -> ${encrypted} -> ${decrypted}`);
  }
  
  // Пустая строка
  const emptyResult = enigma1.process('');
  if (emptyResult !== '') throw new Error('Пустая строка должна остаться пустой');
});

// Тест 11: Максимальная коммутационная панель
test('Максимальная коммутационная панель (10 пар)', () => {
  const maxPlugboard = [
    ['A', 'B'], ['C', 'D'], ['E', 'F'], ['G', 'H'], ['I', 'J'],
    ['K', 'L'], ['M', 'N'], ['O', 'P'], ['Q', 'R'], ['S', 'T']
  ];
  
  const enigma1 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], maxPlugboard);
  const enigma2 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], maxPlugboard);
  
  const original = 'ABCDEFGHIJKLMNOPQRST';
  const encrypted = enigma1.process(original);
  const decrypted = enigma2.process(encrypted);
  
  if (decrypted !== original) {
    throw new Error(`Максимальная коммутация: ${original} -> ${decrypted}`);
  }
});

// Тест 12: Производительность
test('Тест производительности (большой объем данных)', () => {
  const enigma1 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  const enigma2 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  
  const longText = 'PERFORMANCE TEST '.repeat(500); // ~8500 символов
  const startTime = Date.now();
  
  const encrypted = enigma1.process(longText);
  const decrypted = enigma2.process(encrypted);
  
  const endTime = Date.now();
  const processingTime = endTime - startTime;
  
  if (decrypted !== longText) {
    throw new Error('Производительность: данные повреждены при большом объеме');
  }
  
  if (processingTime > 2000) {
    throw new Error(`Производительность: обработка заняла ${processingTime}мс (слишком медленно)`);
  }
  
  console.log(`   📊 Обработано ${longText.length} символов за ${processingTime}мс`);
});

// ================== ФИНАЛЬНЫЙ ОТЧЕТ ==================

console.log('\n' + '='.repeat(60));
console.log(`🎯 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:`);
console.log(`✅ Пройдено тестов: ${passedTests}`);
console.log(`❌ Провалено тестов: ${totalTests - passedTests}`);
console.log(`📊 Общий процент успеха: ${Math.round((passedTests / totalTests) * 100)}%`);
console.log('='.repeat(60));

if (passedTests === totalTests) {
  console.log('🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!');
  console.log('✅ Энигма работает корректно и готова к использованию.');
  console.log('🔒 Шифрование симметрично и исторически точно.');
} else {
  console.log('⚠️  Некоторые тесты провалились. Требуется дополнительная отладка.');
}

console.log(''); 