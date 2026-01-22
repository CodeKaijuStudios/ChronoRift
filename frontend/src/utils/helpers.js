/**
 * ChronoRift Helper Utilities
 * Reusable utility functions for calculations, conversions, and common operations
 */

import {
  TYPE_EFFECTIVENESS,
  BATTLE_CONFIG,
  ECHO_TYPE_COLORS,
  STATUS_EFFECTS,
  EXPERIENCE_TABLE,
  PLAYER_CONFIG,
} from './constants';

// ============================================================================
// DAMAGE CALCULATION
// ============================================================================

/**
 * Calculate base damage between two Echoes
 */
export function calculateDamage(attacker, defender, move) {
  let damage = move.power || 50;

  // Base stats calculation
  const attackStat =
    move.category === 'special' ? attacker.spAtk : attacker.attack;
  const defenseStat =
    move.category === 'special' ? defender.spDef : defender.defense;

  // Damage formula: ((2/5 * Level + 2) * Power * Att/Def) / 50) + 2
  const level = attacker.level || 50;
  damage = Math.floor(
    (((2 * level) / 5 + 2) * move.power * attackStat) / (defenseStat * 50) + 2
  );

  // Apply type effectiveness
  const effectiveness = getTypeEffectiveness(move.type, defender.types);
  damage = Math.floor(damage * effectiveness);

  // Apply STAB (Same Type Attack Bonus)
  if (attacker.types.includes(move.type)) {
    damage = Math.floor(damage * BATTLE_CONFIG.STAB_MULTIPLIER);
  }

  // Critical hit
  if (Math.random() < BATTLE_CONFIG.CRITICAL_CHANCE) {
    damage = Math.floor(damage * BATTLE_CONFIG.CRITICAL_MULTIPLIER);
  }

  // Random variance (85-100%)
  const variance = 0.85 + Math.random() * 0.15;
  damage = Math.floor(damage * variance);

  // Ensure minimum damage
  return Math.max(BATTLE_CONFIG.MIN_DAMAGE, damage);
}

/**
 * Get type effectiveness multiplier
 */
export function getTypeEffectiveness(attackType, defenderTypes) {
  if (!TYPE_EFFECTIVENESS[attackType]) {
    return 1.0;
  }

  const effectiveness = TYPE_EFFECTIVENESS[attackType];
  let multiplier = 1.0;

  defenderTypes.forEach((defType) => {
    if (effectiveness.strong.includes(defType)) {
      multiplier *= BATTLE_CONFIG.TYPE_SUPER_EFFECTIVE;
    } else if (effectiveness.weak.includes(defType)) {
      multiplier *= BATTLE_CONFIG.TYPE_NOT_VERY_EFFECTIVE;
    }
  });

  return multiplier;
}

/**
 * Calculate type advantage text (e.g., "Super Effective!", "Not very effective...")
 */
export function getTypeAdvantageText(multiplier) {
  if (multiplier > 1.5) return 'Super Effective!';
  if (multiplier > 1.0) return 'Effective';
  if (multiplier < 0.5) return 'Not very effective...';
  if (multiplier < 1.0) return 'Resisted';
  return '';
}

// ============================================================================
// EXPERIENCE & LEVELING
// ============================================================================

/**
 * Calculate experience reward
 */
export function calculateExpReward(enemyLevel, playerLevel) {
  const baseExp = 100;
  const levelDifference = enemyLevel - playerLevel;
  let multiplier = 1.0;

  if (levelDifference > 0) {
    multiplier = 1.0 + levelDifference * 0.1;
  } else if (levelDifference < -5) {
    multiplier = Math.max(0.25, 1.0 + levelDifference * 0.05);
  }

  return Math.floor(baseExp * multiplier);
}

/**
 * Calculate currency reward
 */
export function calculateCurrencyReward(enemyLevel) {
  const baseReward = 50;
  const levelBonus = enemyLevel * 3;
  const variance = Math.random() * 20 - 10;
  return Math.max(10, Math.floor(baseReward + levelBonus + variance));
}

/**
 * Get next level experience threshold
 */
export function getNextLevelExp(currentLevel) {
  if (currentLevel >= PLAYER_CONFIG.MAX_LEVEL) {
    return EXPERIENCE_TABLE[PLAYER_CONFIG.MAX_LEVEL - 1];
  }
  return EXPERIENCE_TABLE[currentLevel] || 0;
}

/**
 * Calculate total experience needed to reach level
 */
export function getTotalExpForLevel(level) {
  let total = 0;
  for (let i = 0; i < Math.min(level - 1, EXPERIENCE_TABLE.length); i++) {
    total += EXPERIENCE_TABLE[i];
  }
  return total;
}

/**
 * Get current level progression percentage
 */
export function getLevelProgressionPercent(currentExp, nextLevelExp) {
  return Math.min(100, Math.floor((currentExp / nextLevelExp) * 100));
}

// ============================================================================
// STAT CALCULATIONS
// ============================================================================

/**
 * Calculate HP stat
 */
export function calculateHP(baseHP, level, iv = 31, ev = 0) {
  if (baseHP === 1) return 1; // Shedinja
  return Math.floor(((2 * baseHP + iv + ev / 4) * level) / 100 + level + 5);
}

/**
 * Calculate other stats
 */
export function calculateStat(baseStat, level, iv = 31, ev = 0, nature = 1.0) {
  return Math.floor(
    (((2 * baseStat + iv + ev / 4) * level) / 100 + 5) * nature
  );
}

/**
 * Calculate all stats for an Echo
 */
export function calculateEchoStats(echo, level) {
  return {
    hp: calculateHP(echo.baseHP, level),
    attack: calculateStat(echo.baseAttack, level),
    defense: calculateStat(echo.baseDefense, level),
    spAtk: calculateStat(echo.baseSpAtk, level),
    spDef: calculateStat(echo.baseSpDef, level),
    speed: calculateStat(echo.baseSpeed, level),
  };
}

/**
 * Calculate bonding stat boost
 */
export function calculateBondingBoost(baseStat, bondingLevel, boostPerLevel) {
  return baseStat + bondingLevel * boostPerLevel;
}

// ============================================================================
// STATUS EFFECT UTILITIES
// ============================================================================

/**
 * Check if status effect is permanent
 */
export function isPermanentStatus(status) {
  return [
    STATUS_EFFECTS.BURN,
    STATUS_EFFECTS.FREEZE,
    STATUS_EFFECTS.PARALYSIS,
    STATUS_EFFECTS.POISON,
  ].includes(status);
}

/**
 * Check if status effect blocks moves
 */
export function isBlockingStatus(status) {
  return [
    STATUS_EFFECTS.SLEEP,
    STATUS_EFFECTS.FREEZE,
    STATUS_EFFECTS.PARALYSIS,
  ].includes(status);
}

/**
 * Get status effect color
 */
export function getStatusEffectColor(status) {
  const colorMap = {
    [STATUS_EFFECTS.BURN]: '#ff6b35',
    [STATUS_EFFECTS.FREEZE]: '#7dd3c0',
    [STATUS_EFFECTS.PARALYSIS]: '#ffdd00',
    [STATUS_EFFECTS.POISON]: '#c77dff',
    [STATUS_EFFECTS.CONFUSION]: '#ff9999',
    [STATUS_EFFECTS.SLEEP]: '#888888',
    [STATUS_EFFECTS.STUN]: '#ffff00',
    [STATUS_EFFECTS.PROTECT]: '#00ff00',
    [STATUS_EFFECTS.WEAKNESS]: '#ff6666',
    [STATUS_EFFECTS.STRENGTH]: '#00ff00',
    [STATUS_EFFECTS.ACCURACY_DOWN]: '#ff99ff',
    [STATUS_EFFECTS.EVASION_UP]: '#99ff99',
  };
  return colorMap[status] || '#ffffff';
}

// ============================================================================
// TYPE UTILITIES
// ============================================================================

/**
 * Get color for Echo type
 */
export function getTypeColor(type) {
  return ECHO_TYPE_COLORS[type] || '#cccccc';
}

/**
 * Get all types as array
 */
export function getAllTypes() {
  return Object.values(ECHO_TYPES);
}

/**
 * Check type advantage (for UI indicators)
 */
export function getTypeAdvantage(offensiveType, defensiveTypes) {
  const effectiveness = TYPE_EFFECTIVENESS[offensiveType];
  if (!effectiveness) return 0;

  let strongCount = 0;
  let weakCount = 0;

  defensiveTypes.forEach((type) => {
    if (effectiveness.strong.includes(type)) strongCount++;
    if (effectiveness.weak.includes(type)) weakCount++;
  });

  return strongCount - weakCount;
}

// ============================================================================
// RANDOM UTILITIES
// ============================================================================

/**
 * Generate random integer in range
 */
export function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Randomly select item from array
 */
export function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Shuffle array (Fisher-Yates)
 */
export function shuffleArray(array) {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

/**
 * Weighted random choice
 */
export function weightedRandom(choices) {
  // choices = [{ value: x, weight: w }, ...]
  const totalWeight = choices.reduce((sum, choice) => sum + choice.weight, 0);
  let random = Math.random() * totalWeight;

  for (const choice of choices) {
    random -= choice.weight;
    if (random <= 0) {
      return choice.value;
    }
  }

  return choices[choices.length - 1].value;
}

// ============================================================================
// STRING & FORMATTING UTILITIES
// ============================================================================

/**
 * Format large numbers with commas
 */
export function formatNumber(num) {
  return num.toLocaleString('en-US');
}

/**
 * Format time in MM:SS
 */
export function formatTime(milliseconds) {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Capitalize first letter
 */
export function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Format Echo name (add spaces between words)
 */
export function formatName(name) {
  return name
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .replace(/\b\w/g, (l) => l.toUpperCase());
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str, maxLength) {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + '...';
}

// ============================================================================
// VALIDATION UTILITIES
// ============================================================================

/**
 * Validate email format
 */
export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate username (alphanumeric + underscore, 3-20 chars)
 */
export function isValidUsername(username) {
  return /^[a-zA-Z0-9_]{3,20}$/.test(username);
}

/**
 * Validate password strength
 */
export function isStrongPassword(password) {
  return (
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /[0-9]/.test(password)
  );
}

/**
 * Clamp value between min and max
 */
export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

// ============================================================================
// ARRAY UTILITIES
// ============================================================================

/**
 * Remove duplicates from array
 */
export function removeDuplicates(array) {
  return [...new Set(array)];
}

/**
 * Group array by property
 */
export function groupBy(array, property) {
  return array.reduce((groups, item) => {
    const key = item[property];
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {});
}

/**
 * Sort array by property
 */
export function sortBy(array, property, ascending = true) {
  return [...array].sort((a, b) => {
    if (a[property] < b[property]) return ascending ? -1 : 1;
    if (a[property] > b[property]) return ascending ? 1 : -1;
    return 0;
  });
}

/**
 * Find index of maximum value
 */
export function indexOfMax(array) {
  return array.reduce((maxIndex, val, i, arr) =>
    val > arr[maxIndex] ? i : maxIndex
  );
}

/**
 * Find index of minimum value
 */
export function indexOfMin(array) {
  return array.reduce((minIndex, val, i, arr) =>
    val < arr[minIndex] ? i : minIndex
  );
}

export default {
  calculateDamage,
  getTypeEffectiveness,
  calculateExpReward,
  calculateCurrencyReward,
  calculateEchoStats,
  randomBetween,
  randomChoice,
  formatNumber,
  formatTime,
  capitalize,
  isValidEmail,
  isValidUsername,
  isStrongPassword,
  clamp,
  removeDuplicates,
  groupBy,
  sortBy,
};
