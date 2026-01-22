/**
 * ChronoRift Boot Scene
 * Initial game loading and initialization scene
 * Handles asset preloading, game state setup, and transition to main menu
 */

import Phaser from 'phaser';

export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
    this.loadProgress = 0;
    this.assetsToLoad = [];
  }

  /**
   * Scene preload - Load essential assets
   */
  preload() {
    // Set up load event listeners
    this.load.on('progress', (value) => {
      this.loadProgress = value;
      this.updateLoadingBar();
    });

    this.load.on('complete', () => {
      this.handleLoadComplete();
    });

    this.load.on('loaderror', (file) => {
      console.error(`Failed to load: ${file.key}`);
      this.handleLoadError(file);
    });

    // Load critical assets
    this.loadCriticalAssets();
  }

  /**
   * Scene create - Initialize game state
   */
  create() {
    // Create loading bar UI
    this.createLoadingUI();

    // Initialize game state management
    this.initializeGameState();

    // Setup event listeners
    this.setupEventListeners();
  }

  /**
   * Scene update
   */
  update() {
    // Update loading bar animation
    if (this.loadingBar) {
      const targetWidth = this.cameras.main.width * this.loadProgress;
      this.loadingBar.width = Phaser.Math.Linear(
        this.loadingBar.width,
        targetWidth,
        0.2
      );
    }
  }

  /**
   * Load critical game assets
   */
  loadCriticalAssets() {
    // Load fonts
    this.load.bitmapFont(
      'pixelFont',
      'assets/fonts/pixel_font.png',
      'assets/fonts/pixel_font.xml'
    );

    // Load UI assets
    this.load.image('ui-button', 'assets/ui/button.png');
    this.load.image('ui-panel', 'assets/ui/panel.png');
    this.load.image('ui-icons', 'assets/ui/icons.png');

    // Load background images
    this.load.image('bg-main-menu', 'assets/backgrounds/main_menu.jpg');
    this.load.image('bg-world', 'assets/backgrounds/world.jpg');

    // Load sound assets
    this.load.audio('sfx-click', 'assets/audio/sfx/click.wav');
    this.load.audio('sfx-confirm', 'assets/audio/sfx/confirm.wav');
    this.load.audio('music-menu', 'assets/audio/music/menu.mp3');
    this.load.audio('music-battle', 'assets/audio/music/battle.mp3');

    // Load particle emitter assets
    this.load.image('particle-spark', 'assets/particles/spark.png');
    this.load.image('particle-dust', 'assets/particles/dust.png');
    this.load.image('particle-energy', 'assets/particles/energy.png');

    // Load Echo sprites (placeholder - will be loaded dynamically)
    this.load.spritesheet('echo-idle', 'assets/echoes/idle-spritesheet.png', {
      frameWidth: 64,
      frameHeight: 64,
    });

    this.assetsToLoad = [
      'pixelFont',
      'ui-button',
      'ui-panel',
      'ui-icons',
      'bg-main-menu',
      'bg-world',
      'sfx-click',
      'sfx-confirm',
      'music-menu',
      'music-battle',
      'particle-spark',
      'particle-dust',
      'particle-energy',
      'echo-idle',
    ];
  }

  /**
   * Handle load completion
   */
  handleLoadComplete() {
    console.log('All critical assets loaded');

    // Create sprite animations
    this.createAnimations();

    // Wait briefly then transition
    this.time.delayedCall(500, () => {
      this.scene.start('MainMenuScene');
    });
  }

  /**
   * Handle load error
   */
  handleLoadError(file) {
    console.warn(`Asset load failed: ${file.key}`);
    // Continue anyway - use fallback or placeholder
  }

  /**
   * Create loading bar UI
   */
  createLoadingUI() {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Loading bar background
    const barBg = this.add.rectangle(
      centerX,
      centerY + 40,
      300,
      30,
      0x333333,
      0.8
    );
    barBg.setOrigin(0.5);

    // Loading bar fill
    this.loadingBar = this.add.rectangle(
      centerX - 150,
      centerY + 40,
      0,
      30,
      0x2a8a98,
      1
    );
    this.loadingBar.setOrigin(0, 0.5);

    // Loading text
    this.loadingText = this.add.text(
      centerX,
      centerY - 40,
      'Loading ChronoRift...',
      {
        font: '20px Arial',
        fill: '#ffffff',
      }
    );
    this.loadingText.setOrigin(0.5);

    // Percentage text
    this.percentText = this.add.text(
      centerX,
      centerY + 80,
      '0%',
      {
        font: '16px Arial',
        fill: '#cccccc',
      }
    );
    this.percentText.setOrigin(0.5);
  }

  /**
   * Update loading bar display
   */
  updateLoadingBar() {
    if (this.percentText) {
      this.percentText.setText(Math.round(this.loadProgress * 100) + '%');
    }
  }

  /**
   * Create sprite animations
   */
  createAnimations() {
    // Echo idle animation
    if (!this.anims.exists('echo-idle')) {
      this.anims.create({
        key: 'echo-idle',
        frames: this.anims.generateFrameNumbers('echo-idle', {
          start: 0,
          end: 3,
        }),
        frameRate: 8,
        repeat: -1,
      });
    }

    // UI button animations
    if (!this.anims.exists('btn-hover')) {
      this.anims.create({
        key: 'btn-hover',
        frames: this.anims.generateFrameNumbers('ui-button', {
          start: 0,
          end: 1,
        }),
        frameRate: 4,
        repeat: -1,
      });
    }
  }

  /**
   * Initialize game state
   */
  initializeGameState() {
    // Initialize registry for game state
    this.registry.set('player', {
      id: null,
      username: '',
      level: 1,
      experience: 0,
      currency: 0,
    });

    this.registry.set('team', []);
    this.registry.set('inventory', []);
    this.registry.set('settings', {
      musicVolume: 0.7,
      sfxVolume: 0.8,
      difficulty: 'normal',
    });

    // Set default game state
    this.registry.set('isLoggedIn', false);
    this.registry.set('currentZone', null);
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Listen for game events
    this.events.on('shutdown', () => {
      this.cleanup();
    });

    this.events.on('sleep', () => {
      // Pause music/sfx if scene is paused
    });
  }

  /**
   * Cleanup on scene shutdown
   */
  cleanup() {
    this.load.off('progress');
    this.load.off('complete');
    this.load.off('loaderror');
  }
}

export default BootScene;
