/**
 * ChronoRift World Scene
 * Main game world scene handling exploration, encounters, and dynamic world state
 * Features zone-based exploration, wild Echo encounters, environmental anomalies
 */

import Phaser from 'phaser';

export class WorldScene extends Phaser.Scene {
  constructor() {
    super({ key: 'WorldScene' });
    this.currentZone = null;
    this.worldState = null;
    this.playerCharacter = null;
    this.encounters = [];
    this.anomalies = [];
    this.cameraFollow = true;
  }

  /**
   * Scene init
   */
  init(data) {
    // Get world state from previous scene
    this.currentZone = data.zoneId || 'zone_1';
    this.worldState = data.worldState || this.createDefaultWorldState();
  }

  /**
   * Scene create - Initialize world
   */
  create() {
    // Create world background and tilemap
    this.createWorldEnvironment();

    // Initialize player character
    this.createPlayerCharacter();

    // Spawn wild Echoes
    this.spawnWildEchoes();

    // Spawn environmental anomalies
    this.spawnAnomalies();

    // Create UI overlay
    this.createWorldUI();

    // Setup camera
    this.setupCamera();

    // Setup input handling
    this.setupInputHandling();

    // Setup physics
    this.physics.world.setBounds(0, 0, 1920, 1200);

    // Start event listeners
    this.setupEventListeners();
  }

  /**
   * Scene update
   */
  update() {
    // Update player movement
    this.updatePlayerMovement();

    // Update entity animations
    this.updateEntityAnimations();

    // Update anomaly effects
    this.updateAnomalies();

    // Check for encounters
    this.checkEncounters();

    // Update world state
    this.updateWorldState();
  }

  /**
   * Create world environment
   */
  createWorldEnvironment() {
    // Create background
    const bg = this.add.image(960, 600, 'bg-world');
    bg.setOrigin(0.5);
    bg.setScale(1.2);
    bg.setDepth(-100);

    // Create tilemap
    const map = this.make.tilemap({ key: `tilemap-${this.currentZone}` });
    
    // Create tile layers
    const groundLayer = map.createLayer('Ground', 'tiles');
    const decorLayer = map.createLayer('Decorations', 'tiles');
    const obstacleLayer = map.createLayer('Obstacles', 'tiles');

    // Set collisions for obstacles
    if (obstacleLayer) {
      obstacleLayer.setCollisionByProperty({ collides: true });
      this.physics.add.collider(this, obstacleLayer);
    }

    // Set world bounds to tilemap size
    this.physics.world.setBounds(0, 0, map.widthInPixels, map.heightInPixels);

    // Store map reference
    this.worldMap = map;
  }

  /**
   * Create player character
   */
  createPlayerCharacter() {
    // Create player sprite
    this.playerCharacter = this.add.sprite(400, 400, 'player-idle');
    this.playerCharacter.setScale(2);
    this.playerCharacter.setDepth(10);

    // Add physics to player
    this.physics.add.existing(this.playerCharacter);
    this.playerCharacter.body.setCollideWorldBounds(true);
    this.playerCharacter.body.setBounce(0);

    // Create idle animation
    if (!this.anims.exists('player-idle')) {
      this.anims.create({
        key: 'player-idle',
        frames: this.anims.generateFrameNumbers('player-idle', {
          start: 0,
          end: 3,
        }),
        frameRate: 8,
        repeat: -1,
      });
    }

    // Play idle animation
    this.playerCharacter.play('player-idle');

    // Store player reference
    this.registry.set('playerSprite', this.playerCharacter);
  }

  /**
   * Update player movement based on input
   */
  updatePlayerMovement() {
    if (!this.playerCharacter) return;

    const speed = 150;
    const velocity = this.playerCharacter.body.velocity;

    velocity.x = 0;
    velocity.y = 0;

    // Handle keyboard input
    if (this.cursors.up.isDown) {
      velocity.y = -speed;
    } else if (this.cursors.down.isDown) {
      velocity.y = speed;
    }

    if (this.cursors.left.isDown) {
      velocity.x = -speed;
      this.playerCharacter.setFlipX(true);
    } else if (this.cursors.right.isDown) {
      velocity.x = speed;
      this.playerCharacter.setFlipX(false);
    }
  }

  /**
   * Spawn wild Echo encounters
   */
  spawnWildEchoes() {
    const echoCount = 5 + Math.floor(Math.random() * 3);

    for (let i = 0; i < echoCount; i++) {
      const x = Phaser.Math.Between(200, 1700);
      const y = Phaser.Math.Between(200, 1000);

      const echo = this.add.sprite(x, y, 'echo-idle');
      echo.setScale(1.5);
      echo.setDepth(5);

      // Add physics
      this.physics.add.existing(echo);
      echo.body.setCollideWorldBounds(true);
      echo.body.setBounce(0.5);

      // Random movement
      const vx = Phaser.Math.Between(-50, 50);
      const vy = Phaser.Math.Between(-50, 50);
      echo.body.setVelocity(vx, vy);

      // Store echo data
      echo.echoData = {
        id: `echo_${i}`,
        level: Phaser.Math.Between(1, 10),
        health: Phaser.Math.Between(20, 100),
        type: ['fire', 'water', 'wind', 'earth'][Math.floor(Math.random() * 4)],
      };

      echo.play('echo-idle');
      this.encounters.push(echo);
    }
  }

  /**
   * Spawn environmental anomalies
   */
  spawnAnomalies() {
    // Check world stability
    if (this.worldState.globalStability < 0.6) {
      const anomalyCount = 1 + Math.floor(Math.random() * 2);

      for (let i = 0; i < anomalyCount; i++) {
        const x = Phaser.Math.Between(300, 1600);
        const y = Phaser.Math.Between(300, 900);

        const anomaly = this.add.circle(x, y, 40, 0x8b4789, 0.6);
        anomaly.setDepth(1);

        anomaly.anomalyData = {
          id: `anomaly_${i}`,
          type: 'void_corruption',
          severity: 'major',
          intensity: this.worldState.globalStability,
          radius: 80,
        };

        // Add pulse animation
        this.tweens.add({
          targets: anomaly,
          radius: 50,
          duration: 1000,
          yoyo: true,
          repeat: -1,
        });

        this.anomalies.push(anomaly);
      }
    }
  }

  /**
   * Check for wild Echo encounters
   */
  checkEncounters() {
    if (!this.playerCharacter) return;

    this.encounters.forEach((echo) => {
      const distance = Phaser.Math.Distance.Between(
        this.playerCharacter.x,
        this.playerCharacter.y,
        echo.x,
        echo.y
      );

      // Encounter range
      if (distance < 60) {
        this.initiateWildBattle(echo);
      }
    });
  }

  /**
   * Initiate wild Echo battle
   */
  initiateWildBattle(wildEcho) {
    // Pause world
    this.scene.pause();

    // Transition to battle scene
    this.scene.launch('BattleScene', {
      battleType: 'wild',
      wildEcho: wildEcho.echoData,
      playerTeam: this.registry.get('team'),
    });

    // Listen for battle end
    this.events.once('resume', () => {
      this.handleBattleEnd();
    });
  }

  /**
   * Handle battle end
   */
  handleBattleEnd() {
    console.log('Battle ended, resuming world exploration');
    // Remove defeated echo
    // Grant experience
    // Update registry
  }

  /**
   * Update anomalies
   */
  updateAnomalies() {
    this.anomalies.forEach((anomaly) => {
      const data = anomaly.anomalyData;

      // Apply damage to nearby entities
      this.encounters.forEach((echo) => {
        const distance = Phaser.Math.Distance.Between(
          anomaly.x,
          anomaly.y,
          echo.x,
          echo.y
        );

        if (distance < data.radius) {
          // Apply anomaly damage/effects
          echo.echoData.health -= 0.5; // Small damage per frame

          if (echo.echoData.health <= 0) {
            echo.destroy();
          }
        }
      });

      // Player in anomaly field
      const playerDistance = Phaser.Math.Distance.Between(
        anomaly.x,
        anomaly.y,
        this.playerCharacter.x,
        this.playerCharacter.y
      );

      if (playerDistance < data.radius) {
        // Visual effect
        this.playerCharacter.setTint(0xff6666);
      } else {
        this.playerCharacter.clearTint();
      }
    });
  }

  /**
   * Update entity animations
   */
  updateEntityAnimations() {
    this.encounters.forEach((echo) => {
      // Update based on velocity
      if (echo.body.velocity.x !== 0 || echo.body.velocity.y !== 0) {
        // Could play movement animation
      }
    });
  }

  /**
   * Update world state
   */
  updateWorldState() {
    // Simulate world time passing
    this.worldState.timePassed += 0.016; // ~60fps

    // Update anomaly decay
    if (this.worldState.globalStability < 1.0) {
      this.worldState.globalStability += 0.00005; // Recover slowly
    }

    // Update registry
    this.registry.set('worldState', this.worldState);
  }

  /**
   * Create world UI overlay
   */
  createWorldUI() {
    // Zone name
    this.zoneText = this.add.text(16, 16, `Zone: ${this.currentZone}`, {
      font: '16px Arial',
      fill: '#ffffff',
    });
    this.zoneText.setDepth(100);
    this.zoneText.setScrollFactor(0);

    // Player team quick info
    this.teamText = this.add.text(16, 50, 'Team: ', {
      font: '12px Arial',
      fill: '#cccccc',
    });
    this.teamText.setDepth(100);
    this.teamText.setScrollFactor(0);

    // World stability indicator
    this.stabilityText = this.add.text(16, 80, 'Stability: ', {
      font: '12px Arial',
      fill: '#aaffaa',
    });
    this.stabilityText.setDepth(100);
    this.stabilityText.setScrollFactor(0);

    // Coordinates display
    this.coordsText = this.add.text(16, 110, 'Pos: (0, 0)', {
      font: '10px Arial',
      fill: '#888888',
    });
    this.coordsText.setDepth(100);
    this.coordsText.setScrollFactor(0);
  }

  /**
   * Setup camera following player
   */
  setupCamera() {
    const camera = this.cameras.main;
    camera.setBounds(0, 0, 1920, 1200);
    camera.startFollow(this.playerCharacter);
    camera.setZoom(1.5);
  }

  /**
   * Setup input handling
   */
  setupInputHandling() {
    // Arrow keys or WASD
    this.cursors = this.input.keyboard.createCursorKeys();

    // Additional keys
    this.input.keyboard.on('keydown-E', () => {
      this.handleInteraction();
    });

    this.input.keyboard.on('keydown-M', () => {
      this.openMenu();
    });

    this.input.keyboard.on('keydown-T', () => {
      this.openTeamMenu();
    });
  }

  /**
   * Handle player interaction
   */
  handleInteraction() {
    // Check for nearby NPCs or items
    console.log('Interaction triggered');
  }

  /**
   * Open pause menu
   */
  openMenu() {
    this.scene.pause();
    this.scene.launch('MenuScene');
  }

  /**
   * Open team menu
   */
  openTeamMenu() {
    this.scene.pause();
    this.scene.launch('TeamMenuScene');
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Listen for world mutations
    this.events.on('worldMutation', (mutation) => {
      this.handleWorldMutation(mutation);
    });

    // Listen for player level up
    this.events.on('playerLevelUp', (level) => {
      this.showLevelUpNotification(level);
    });
  }

  /**
   * Handle world mutation event
   */
  handleWorldMutation(mutation) {
    console.log('World mutation:', mutation);
    // Trigger visual effect
    this.cameras.main.shake(300, 0.01);
  }

  /**
   * Show level up notification
   */
  showLevelUpNotification(level) {
    const text = this.add.text(
      this.playerCharacter.x,
      this.playerCharacter.y - 50,
      `Level Up! ${level}`,
      {
        font: 'bold 24px Arial',
        fill: '#ffff00',
      }
    );
    text.setOrigin(0.5);
    text.setDepth(50);

    this.tweens.add({
      targets: text,
      y: text.y - 50,
      alpha: 0,
      duration: 2000,
      onComplete: () => text.destroy(),
    });
  }

  /**
   * Create default world state
   */
  createDefaultWorldState() {
    return {
      globalStability: 0.6,
      anomalies: [],
      timePassed: 0,
      corruption: 0,
    };
  }
}

export default WorldScene;
