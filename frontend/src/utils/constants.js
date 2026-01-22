/**
 * ChronoRift Constants
 * Game-wide constants, enums, configurations, and lookup tables
 */

// ============================================================================
// GAME CONFIGURATION
// ============================================================================

export const GAME_CONFIG = {
  TITLE: 'ChronoRift',
  VERSION: '1.0.0',
  DEBUG: true,
  FPS: 60,
  RESOLUTION_WIDTH: 1280,
  RESOLUTION_HEIGHT: 720,
  SCALE_MODE: 'FIT',
};

// ============================================================================
// ECHO TYPES & ELEMENTS
// ============================================================================

export const ECHO_TYPES = {
  FIRE: 'fire',
  WATER: 'water',
  WIND: 'wind',
  EARTH: 'earth',
  ELECTRIC: 'electric',
  ICE: 'ice',
  GRASS: 'grass',
  PSYCHIC: 'psychic',
  DARK: 'dark',
  LIGHT: 'light',
  VOID: 'void',
  CHRONO: 'chrono',
};

export const ECHO_TYPE_COLORS = {
  [ECHO_TYPES.FIRE]: '#ff6b35',
  [ECHO_TYPES.WATER]: '#004e89',
  [ECHO_TYPES.WIND]: '#9dd4d4',
  [ECHO_TYPES.EARTH]: '#8b6f47',
  [ECHO_TYPES.ELECTRIC]: '#ffdd00',
  [ECHO_TYPES.ICE]: '#7dd3c0',
  [ECHO_TYPES.GRASS]: '#52b788',
  [ECHO_TYPES.PSYCHIC]: '#c77dff',
  [ECHO_TYPES.DARK]: '#2a2a2a',
  [ECHO_TYPES.LIGHT]: '#fff59d',
  [ECHO_TYPES.VOID]: '#6a0572',
  [ECHO_TYPES.CHRONO]: '#2a8a98',
};

export const TYPE_EFFECTIVENESS = {
  [ECHO_TYPES.FIRE]: {
    strong: [ECHO_TYPES.GRASS, ECHO_TYPES.ICE],
    weak: [ECHO_TYPES.WATER, ECHO_TYPES.EARTH],
  },
  [ECHO_TYPES.WATER]: {
    strong: [ECHO_TYPES.FIRE, ECHO_TYPES.EARTH],
    weak: [ECHO_TYPES.ELECTRIC, ECHO_TYPES.GRASS],
  },
  [ECHO_TYPES.WIND]: {
    strong: [ECHO_TYPES.GRASS, ECHO_TYPES.ELECTRIC],
    weak: [ECHO_TYPES.EARTH, ECHO_TYPES.WATER],
  },
  [ECHO_TYPES.EARTH]: {
    strong: [ECHO_TYPES.FIRE, ECHO_TYPES.ELECTRIC],
    weak: [ECHO_TYPES.WATER, ECHO_TYPES.GRASS],
  },
  [ECHO_TYPES.ELECTRIC]: {
    strong: [ECHO_TYPES.WATER, ECHO_TYPES.WIND],
    weak: [ECHO_TYPES.EARTH, ECHO_TYPES.GRASS],
  },
  [ECHO_TYPES.ICE]: {
    strong: [ECHO_TYPES.WIND, ECHO_TYPES.GRASS],
    weak: [ECHO_TYPES.FIRE, ECHO_TYPES.EARTH],
  },
  [ECHO_TYPES.GRASS]: {
    strong: [ECHO_TYPES.WATER, ECHO_TYPES.EARTH],
    weak: [ECHO_TYPES.FIRE, ECHO_TYPES.ICE],
  },
  [ECHO_TYPES.PSYCHIC]: {
    strong: [ECHO_TYPES.DARK],
    weak: [ECHO_TYPES.DARK],
  },
  [ECHO_TYPES.DARK]: {
    strong: [ECHO_TYPES.PSYCHIC, ECHO_TYPES.LIGHT],
    weak: [ECHO_TYPES.LIGHT],
  },
  [ECHO_TYPES.LIGHT]: {
    strong: [ECHO_TYPES.DARK],
    weak: [ECHO_TYPES.DARK],
  },
  [ECHO_TYPES.VOID]: {
    strong: [ECHO_TYPES.CHRONO],
    weak: [ECHO_TYPES.CHRONO],
  },
  [ECHO_TYPES.CHRONO]: {
    strong: [ECHO_TYPES.VOID],
    weak: [ECHO_TYPES.VOID],
  },
};

// ============================================================================
// MOVE CATEGORIES & EFFECTS
// ============================================================================

export const MOVE_CATEGORIES = {
  PHYSICAL: 'physical',
  SPECIAL: 'special',
  STATUS: 'status',
};

export const MOVE_TARGETS = {
  ENEMY: 'enemy',
  ALLY: 'ally',
  SELF: 'self',
  ALL_ENEMIES: 'all_enemies',
  ALL_ALLIES: 'all_allies',
};

export const STATUS_EFFECTS = {
  BURN: 'burn',
  FREEZE: 'freeze',
  PARALYSIS: 'paralysis',
  POISON: 'poison',
  CONFUSION: 'confusion',
  SLEEP: 'sleep',
  STUN: 'stun',
  PROTECT: 'protect',
  WEAKNESS: 'weakness',
  STRENGTH: 'strength',
  ACCURACY_DOWN: 'accuracy_down',
  EVASION_UP: 'evasion_up',
};

export const STATUS_DURATION = {
  [STATUS_EFFECTS.BURN]: -1,
  [STATUS_EFFECTS.FREEZE]: -1,
  [STATUS_EFFECTS.PARALYSIS]: -1,
  [STATUS_EFFECTS.POISON]: -1,
  [STATUS_EFFECTS.CONFUSION]: 4,
  [STATUS_EFFECTS.SLEEP]: Phaser.Math.Between(1, 3),
  [STATUS_EFFECTS.STUN]: 1,
  [STATUS_EFFECTS.PROTECT]: 1,
  [STATUS_EFFECTS.WEAKNESS]: 3,
  [STATUS_EFFECTS.STRENGTH]: 3,
  [STATUS_EFFECTS.ACCURACY_DOWN]: 2,
  [STATUS_EFFECTS.EVASION_UP]: 2,
};

// ============================================================================
// PLAYER & EXPERIENCE
// ============================================================================

export const PLAYER_CONFIG = {
  MAX_LEVEL: 100,
  STARTING_LEVEL: 1,
  BASE_EXP: 1000,
  EXP_MULTIPLIER: 1.1,
  MAX_TEAM_SIZE: 6,
  INITIAL_CURRENCY: 1000,
};

export const EXPERIENCE_TABLE = Array.from(
  { length: PLAYER_CONFIG.MAX_LEVEL },
  (_, i) => {
    const level = i + 1;
    const baseExp = PLAYER_CONFIG.BASE_EXP;
    const multiplier = Math.pow(PLAYER_CONFIG.EXP_MULTIPLIER, level - 1);
    return Math.floor(baseExp * multiplier);
  }
);

export function getLevelFromExperience(totalExp) {
  let cumulativeExp = 0;
  for (let level = 0; level < EXPERIENCE_TABLE.length; level++) {
    cumulativeExp += EXPERIENCE_TABLE[level];
    if (totalExp < cumulativeExp) {
      return level + 1;
    }
  }
  return PLAYER_CONFIG.MAX_LEVEL;
}

// ============================================================================
// ZONES & WORLD
// ============================================================================

export const ZONES = {
  STARTING_FOREST: 'zone_1',
  CRYSTAL_CAVERNS: 'zone_2',
  STORM_PEAKS: 'zone_3',
  ABYSS_DEPTHS: 'zone_4',
  VOID_NEXUS: 'zone_5',
  CHRONO_SANCTUARY: 'zone_6',
};

export const ZONE_DATA = {
  [ZONES.STARTING_FOREST]: {
    name: 'Starting Forest',
    minLevel: 1,
    maxLevel: 15,
    baseStability: 0.8,
    rarityBoost: 1.0,
  },
  [ZONES.CRYSTAL_CAVERNS]: {
    name: 'Crystal Caverns',
    minLevel: 15,
    maxLevel: 30,
    baseStability: 0.6,
    rarityBoost: 1.2,
  },
  [ZONES.STORM_PEAKS]: {
    name: 'Storm Peaks',
    minLevel: 30,
    maxLevel: 50,
    baseStability: 0.4,
    rarityBoost: 1.4,
  },
  [ZONES.ABYSS_DEPTHS]: {
    name: 'Abyss Depths',
    minLevel: 50,
    maxLevel: 75,
    baseStability: 0.2,
    rarityBoost: 1.6,
  },
  [ZONES.VOID_NEXUS]: {
    name: 'Void Nexus',
    minLevel: 75,
    maxLevel: 100,
    baseStability: 0.0,
    rarityBoost: 2.0,
  },
  [ZONES.CHRONO_SANCTUARY]: {
    name: 'Chrono Sanctuary',
    minLevel: 1,
    maxLevel: 100,
    baseStability: 1.0,
    rarityBoost: 0.5,
  },
};

export const ANOMALY_TYPES = {
  VOID_CORRUPTION: 'void_corruption',
  TIME_DISTORTION: 'time_distortion',
  DIMENSIONAL_RIFT: 'dimensional_rift',
  QUANTUM_FLUX: 'quantum_flux',
};

export const ANOMALY_SEVERITY = {
  MINOR: 'minor',
  MODERATE: 'moderate',
  MAJOR: 'major',
  CRITICAL: 'critical',
};

// ============================================================================
// BATTLE CONFIGURATION
// ============================================================================

export const BATTLE_CONFIG = {
  TURN_TIMEOUT: 30000,
  ANIMATION_SPEED: 400,
  DAMAGE_TEXT_DURATION: 1000,
  MIN_DAMAGE: 1,
  STAB_MULTIPLIER: 1.5,
  TYPE_SUPER_EFFECTIVE: 1.5,
  TYPE_NOT_VERY_EFFECTIVE: 0.75,
  CRITICAL_CHANCE: 0.125,
  CRITICAL_MULTIPLIER: 1.5,
};

export const BATTLE_REWARDS = {
  EXPERIENCE_MULTIPLIER: 1.0,
  CURRENCY_BASE: 100,
  ITEM_DROP_RATE: 0.3,
};

// ============================================================================
// UI & DISPLAY
// ============================================================================

export const UI_COLORS = {
  PRIMARY: '#2a8a98',
  SECONDARY: '#1a1a2e',
  TEXT_PRIMARY: '#aaffaa',
  TEXT_SECONDARY: '#cccccc',
  ACCENT: '#ffff99',
  SUCCESS: '#00ff00',
  WARNING: '#ffff00',
  ERROR: '#ff6666',
  DISABLED: '#666666',
};

export const UI_SIZES = {
  PANEL_WIDTH: 300,
  PANEL_HEIGHT: 200,
  BUTTON_WIDTH: 100,
  BUTTON_HEIGHT: 32,
  MINIMAP_SIZE: 120,
  STAT_PANEL_WIDTH: 200,
};

export const FONT_SIZES = {
  TITLE: '28px',
  HEADING: '18px',
  LARGE: '14px',
  NORMAL: '12px',
  SMALL: '10px',
  TINY: '8px',
};

// ============================================================================
// ITEMS & EQUIPMENT
// ============================================================================

export const ITEM_TYPES = {
  POTION: 'potion',
  REVIVE: 'revive',
  BATTLE_ITEM: 'battle_item',
  POKÉBALL: 'pokeball',
  KEY_ITEM: 'key_item',
  EQUIPMENT: 'equipment',
  MATERIAL: 'material',
};

export const ITEM_RARITY = {
  COMMON: 'common',
  UNCOMMON: 'uncommon',
  RARE: 'rare',
  EPIC: 'epic',
  LEGENDARY: 'legendary',
};

export const ITEM_RARITY_COLORS = {
  [ITEM_RARITY.COMMON]: '#aaaaaa',
  [ITEM_RARITY.UNCOMMON]: '#00ff00',
  [ITEM_RARITY.RARE]: '#0099ff',
  [ITEM_RARITY.EPIC]: '#ff00ff',
  [ITEM_RARITY.LEGENDARY]: '#ffaa00',
};

// ============================================================================
// ANIMATIONS & TIMING
// ============================================================================

export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 250,
  SLOW: 400,
  VERY_SLOW: 800,
  TURN_DURATION: 5000,
  FADE_IN: 300,
  FADE_OUT: 300,
  MOVE_IN: 400,
  MOVE_OUT: 300,
};

export const EASING = {
  STANDARD: 'Cubic.easeInOut',
  EASE_OUT: 'Back.easeOut',
  EASE_IN: 'Back.easeIn',
  LINEAR: 'Linear.easeNone',
  BOUNCE: 'Bounce.easeOut',
};

// ============================================================================
// BONDING & MECHANICS
// ============================================================================

export const BONDING_CONFIG = {
  MAX_LEVEL: 10,
  STAT_BOOST_PER_LEVEL: {
    attack: 1,
    defense: 0.5,
    spAtk: 1,
    spDef: 0.5,
    speed: 0.5,
    hp: 2,
  },
  UNLOCKED_MOVES_AT: {
    3: 'move_name_1',
    6: 'move_name_2',
    9: 'move_name_3',
  },
};

// ============================================================================
// DIFFICULTY LEVELS
// ============================================================================

export const DIFFICULTY_LEVELS = {
  EASY: 'easy',
  NORMAL: 'normal',
  HARD: 'hard',
  EXPERT: 'expert',
  INSANE: 'insane',
};

export const DIFFICULTY_MULTIPLIERS = {
  [DIFFICULTY_LEVELS.EASY]: {
    damageDealt: 1.2,
    damageTaken: 0.8,
    expReward: 0.75,
    currencyReward: 0.75,
  },
  [DIFFICULTY_LEVELS.NORMAL]: {
    damageDealt: 1.0,
    damageTaken: 1.0,
    expReward: 1.0,
    currencyReward: 1.0,
  },
  [DIFFICULTY_LEVELS.HARD]: {
    damageDealt: 0.8,
    damageTaken: 1.2,
    expReward: 1.5,
    currencyReward: 1.5,
  },
  [DIFFICULTY_LEVELS.EXPERT]: {
    damageDealt: 0.6,
    damageTaken: 1.5,
    expReward: 2.0,
    currencyReward: 2.0,
  },
  [DIFFICULTY_LEVELS.INSANE]: {
    damageDealt: 0.4,
    damageTaken: 2.0,
    expReward: 3.0,
    currencyReward: 3.0,
  },
};

// ============================================================================
// API ENDPOINTS
// ============================================================================

export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
  },
  PLAYER: {
    GET: '/player',
    UPDATE: '/player',
    TEAM_GET: '/player/team',
    TEAM_ADD: '/player/team',
    TEAM_REMOVE: '/player/team/:echoId',
    INVENTORY_GET: '/player/inventory',
  },
  ECHOES: {
    LIST: '/echoes',
    GET: '/echoes/:id',
  },
  BATTLES: {
    START: '/battles',
    ACTION: '/battles/:id/action',
    RESULTS: '/battles/:id/results',
  },
  WORLD: {
    ZONES: '/world/zones',
    ZONE_GET: '/world/zones/:id',
    ANOMALIES: '/world/anomalies',
  },
  LEADERBOARD: {
    GET: '/leaderboard',
  },
};

// ============================================================================
// LOCAL STORAGE KEYS
// ============================================================================

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken',
  USER_ID: 'userId',
  PLAYER_DATA: 'playerData',
  TEAM: 'playerTeam',
  INVENTORY: 'playerInventory',
  SETTINGS: 'gameSettings',
  BONDING: 'ecoBonding',
  ACHIEVEMENTS: 'achievements',
  PLAYTIME: 'totalPlaytime',
};

export default {
  GAME_CONFIG,
  ECHO_TYPES,
  ECHO_TYPE_COLORS,
  TYPE_EFFECTIVENESS,
  MOVE_CATEGORIES,
  MOVE_TARGETS,
  STATUS_EFFECTS,
  PLAYER_CONFIG,
  ZONES,
  ZONE_DATA,
  ANOMALY_TYPES,
  BATTLE_CONFIG,
  UI_COLORS,
  ITEM_TYPES,
  ITEM_RARITY,
  ANIMATION_DURATIONS,
  BONDING_CONFIG,
  DIFFICULTY_LEVELS,
  API_ENDPOINTS,
  STORAGE_KEYS,
};
