const readline = require('readline');

const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
function mod(n, m) {
  return ((n % m) + m) % m;
}

const ROTORS = [
  { wiring: 'EKMFLGDQVZNTOWYHXUSPAIBRCJ', notch: 'Q' }, // Rotor I
  { wiring: 'AJDKSIRUXBLHWTMCQGZNPYFVOE', notch: 'E' }, // Rotor II
  { wiring: 'BDFHJLCPRTXVZNYEIWGAKMUSQO', notch: 'V' }, // Rotor III
];
const REFLECTOR = 'YRUHQSLDPXNGOKMIEBFZCWVJAT';

function plugboardSwap(c, pairs) {
  for (const [a, b] of pairs) {
    if (c === a) return b;
    if (c === b) return a;
  }
  return c;
}

class Rotor {
  constructor(wiring, notch, ringSetting = 0, position = 0) {
    this.wiring = wiring;
    this.notch = notch;
    this.ringSetting = ringSetting;
    this.position = position;
  }
  step() {
    this.position = mod(this.position + 1, 26);
  }
  atNotch() {
    return alphabet[this.position] === this.notch;
  }
  forward(c) {
    const charIndex = alphabet.indexOf(c);
    if (charIndex === -1) return c; // Возвращаем символ без изменений, если он не в алфавите
    const idx = mod(charIndex + this.position - this.ringSetting, 26);
    return this.wiring[idx];
  }
  backward(c) {
    const idx = this.wiring.indexOf(c);
    if (idx === -1) return c; // Возвращаем символ без изменений, если он не найден в проводке
    return alphabet[mod(idx - this.position + this.ringSetting, 26)];
  }
}

class Enigma {
  constructor(rotorIDs, rotorPositions, ringSettings, plugboardPairs) {
    this.rotors = rotorIDs.map(
      (id, i) =>
        new Rotor(
          ROTORS[id].wiring,
          ROTORS[id].notch,
          ringSettings[i],
          rotorPositions[i],
        ),
    );
    this.plugboardPairs = plugboardPairs;
  }
  stepRotors() {
    // Двойной шаг: если средний ротор на зарубке, он повернется дважды
    const middleAtNotch = this.rotors[1].atNotch();
    const rightAtNotch = this.rotors[2].atNotch();

    // Левый ротор поворачивается, если средний на зарубке
    if (middleAtNotch) {
      this.rotors[0].step();
    }

    // Средний ротор поворачивается, если правый на зарубке ИЛИ он сам на зарубке
    if (rightAtNotch || middleAtNotch) {
      this.rotors[1].step();
    }

    // Правый ротор всегда поворачивается
    this.rotors[2].step();
  }
  encryptChar(c) {
    if (!alphabet.includes(c)) return c;
    this.stepRotors();
    c = plugboardSwap(c, this.plugboardPairs);
    for (let i = this.rotors.length - 1; i >= 0; i--) {
      c = this.rotors[i].forward(c);
    }

    // Безопасное обращение к рефлектору
    const reflectorIndex = alphabet.indexOf(c);
    if (reflectorIndex === -1) return c; // Защита от некорректных символов
    c = REFLECTOR[reflectorIndex];

    for (let i = 0; i < this.rotors.length; i++) {
      c = this.rotors[i].backward(c);
    }

    c = plugboardSwap(c, this.plugboardPairs);
    return c;
  }
  process(text) {
    return text
      .toUpperCase()
      .split('')
      .map((c) => this.encryptChar(c))
      .join('');
  }
}

function promptEnigma() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  rl.question('Enter message: ', (message) => {
    rl.question('Rotor positions (e.g. 0 0 0 or A A A): ', (posStr) => {
      const posStrArray = posStr.split(' ');
      let rotorPositions;
      
      // Попытка парсинга как чисел
      const numPositions = posStrArray.map(Number);
      if (posStrArray.length === 3 && !numPositions.some(isNaN) && 
          numPositions.every(pos => pos >= 0 && pos <= 25)) {
        rotorPositions = numPositions;
      }
      // Попытка парсинга как букв
      else if (posStrArray.length === 3 && 
               posStrArray.every(pos => pos.length === 1 && alphabet.includes(pos.toUpperCase()))) {
        rotorPositions = posStrArray.map(pos => alphabet.indexOf(pos.toUpperCase()));
      }
      else {
        console.log('Error: Please enter exactly 3 numbers (0-25) or letters (A-Z)');
        rl.close();
        return;
      }
      
      rl.question('Ring settings (e.g. 0 0 0 or A A A): ', (ringStr) => {
        const ringStrArray = ringStr.split(' ');
        let ringSettings;
        
        // Попытка парсинга как чисел
        const numSettings = ringStrArray.map(Number);
        if (ringStrArray.length === 3 && !numSettings.some(isNaN) && 
            numSettings.every(ring => ring >= 0 && ring <= 25)) {
          ringSettings = numSettings;
        }
        // Попытка парсинга как букв
        else if (ringStrArray.length === 3 && 
                 ringStrArray.every(ring => ring.length === 1 && alphabet.includes(ring.toUpperCase()))) {
          ringSettings = ringStrArray.map(ring => alphabet.indexOf(ring.toUpperCase()));
        }
        else {
          console.log('Error: Please enter exactly 3 numbers (0-25) or letters (A-Z)');
          rl.close();
          return;
        }
        
        rl.question('Plugboard pairs (e.g. AB CD): ', (plugStr) => {
          const plugPairs =
            plugStr
              .toUpperCase()
              .match(/([A-Z]{2})/g)
              ?.map((pair) => [pair[0], pair[1]]) || [];

          // Валидация коммутационной панели
          if (plugPairs.length > 10) {
            console.log('Error: Maximum 10 plugboard pairs allowed');
            rl.close();
            return;
          }

          const usedLetters = new Set();
          for (const [a, b] of plugPairs) {
            // Проверка на самозамкнутые пары
            if (a === b) {
              console.log('Error: A letter cannot be paired with itself (e.g., AA is invalid)');
              rl.close();
              return;
            }
            
            if (usedLetters.has(a) || usedLetters.has(b)) {
              console.log('Error: Each letter can only be used once in plugboard pairs');
              rl.close();
              return;
            }
            usedLetters.add(a);
            usedLetters.add(b);
          }

          const enigma = new Enigma(
            [0, 1, 2],
            rotorPositions,
            ringSettings,
            plugPairs,
          );
          const result = enigma.process(message);
          console.log('Output:', result);
          rl.close();
        });
      });
    });
  });
}

// Функция для тестирования корректности работы Энигмы
function testEnigma() {
  console.log('Testing Enigma machine...');
  
  // Тест симметричности: шифрование = дешифрование
  const enigma1 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], [['A', 'B']]);
  const enigma2 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], [['A', 'B']]);
  
  const original = "HELLO WORLD";
  const encrypted = enigma1.process(original);
  const decrypted = enigma2.process(encrypted);
  
  console.log(`Original:  ${original}`);
  console.log(`Encrypted: ${encrypted}`);
  console.log(`Decrypted: ${decrypted}`);
  console.log(`Test ${original === decrypted ? 'PASSED' : 'FAILED'}: Symmetry test`);
  
  // Тест, что буква никогда не шифруется сама в себя
  const enigma3 = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
  let selfEncryptionFound = false;
  
  for (let i = 0; i < 26; i++) {
    const letter = alphabet[i];
    const enigmaTest = new Enigma([0, 1, 2], [0, 0, 0], [0, 0, 0], []);
    const encrypted = enigmaTest.encryptChar(letter);
    if (letter === encrypted) {
      selfEncryptionFound = true;
      break;
    }
  }
  
  console.log(`Test ${!selfEncryptionFound ? 'PASSED' : 'FAILED'}: No letter encrypts to itself`);
  console.log('Enigma testing completed.\n');
}

// Экспорт для модульных тестов
module.exports = {
  Enigma,
  Rotor,
  plugboardSwap,
  alphabet,
  ROTORS,
  REFLECTOR,
  mod,
  testEnigma
};

if (require.main === module) {
  // Запуск тестов перед основной программой
  testEnigma();
  promptEnigma();
}
