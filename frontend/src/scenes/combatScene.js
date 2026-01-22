/**
 * ChronoRift Combat Scene
 * Turn-based battle system featuring player team vs opponents
 * Handles initiative, turn order, move selection, and battle resolution
 */

import Phaser from 'phaser';

export class CombatScene extends Phaser.Scene {
  constructor() {
    super({ key: 'CombatScene' });
    this.battleState = null;
    this.playerTeam = [];
    this.opponentTeam = [];
    this.currentTurn = null;
    this.turnOrder = [];
    this.battleLog = [];
    this.selectedMove = null;
    this.selectedTarget = null;
    this.isAnimating = false;
  }

  /**
   * Scene init
   */
  init(data) {
    this.battleType = data.battleType || 'wild'; // wild, trainer, boss
    this.playerTeam = data.playerTeam || [];
    this.opponentTeam = data.opponentTeam || [data.wildEcho];
    this.battleState = 'setup';
  }

  /**
   * Scene create - Initialize battle
   */
  create() {
    // Create battle background
    this.createBattleBackground();

    // Initialize battle state
    this.initializeBattle();

    // Create UI elements
    this.createBattleUI();

    // Create team displays
    this.createTeamDisplays();

    // Calculate turn order
    this.calculateTurnOrder();

    // Start battle
    this.startBattle();

    // Setup event listeners
    this.setupEventListeners();
  }

  /**
   * Scene update
   */
  update() {
    // Update health bars
    this.updateHealthBars();

    // Update status effects
    this.updateStatusEffects();

    // Display current turn info
    this.updateTurnDisplay();
  }

  /**
   * Create battle background
   */
  createBattleBackground() {
    // Battle arena background
    const bg = this.add.rectangle(
      0,
      0,
      this.cameras.main.width,
      this.cameras.main.height,
      0x1a1a2e
    );
    bg.setOrigin(0, 0);
    bg.setDepth(-10);

    // Background effects
    const topGradient = this.add.rectangle(
      0,
      0,
      this.cameras.main.width,
      100,
      0x2a2a4e,
      0.5
    );
    topGradient.setOrigin(0, 0);
    topGradient.setDepth(-8);

    // Grid pattern
    this.createGridPattern();
  }

  /**
   * Create grid pattern effect
   */
  createGridPattern() {
    const graphics = this.make.graphics({ x: 0, y: 0, add: false });
    graphics.lineStyle(1, 0x333355, 0.3);

    const gridSize = 40;
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Vertical lines
    for (let x = 0; x < width; x += gridSize) {
      graphics.lineBetween(x, 0, x, height);
    }

    // Horizontal lines
    for (let y = 0; y < height; y += gridSize) {
      graphics.lineBetween(0, y, width, y);
    }

    graphics.generateTexture('gridTexture', width, height);
    graphics.destroy();

    const gridSprite = this.add.image(0, 0, 'gridTexture');
    gridSprite.setOrigin(0, 0);
    gridSprite.setDepth(-5);
    gridSprite.setAlpha(0.3);
  }

  /**
   * Initialize battle state
   */
  initializeBattle() {
    this.battleState = {
      round: 1,
      battleActive: true,
      battleLog: [],
      weather: null,
      terrain: null,
    };

    // Initialize participant data
    this.playerTeam.forEach((echo, index) => {
      echo.battleData = {
        currentHP: echo.stats.hp,
        maxHP: echo.stats.hp,
        statusEffects: [],
        usedMove: null,
        priority: 0,
      };
    });

    this.opponentTeam.forEach((echo, index) => {
      echo.battleData = {
        currentHP: echo.stats?.hp || echo.health || 100,
        maxHP: echo.stats?.hp || echo.health || 100,
        statusEffects: [],
        usedMove: null,
        priority: 0,
      };
    });
  }

  /**
   * Create battle UI
   */
  createBattleUI() {
    const padding = 16;
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Battle log panel
    this.battleLogPanel = this.add.rectangle(
      padding,
      height - 120,
      300,
      100,
      0x1a1a2e,
      0.9
    );
    this.battleLogPanel.setOrigin(0, 0);
    this.battleLogPanel.setDepth(50);
    this.battleLogPanel.setStrokeStyle(2, 0x2a8a98);

    // Battle log text
    this.battleLogText = this.add.text(
      padding + 8,
      height - 110,
      'Battle started!',
      {
        font: '12px Arial',
        fill: '#aaffaa',
        wordWrap: { width: 280, useAdvancedWrap: true },
      }
    );
    this.battleLogText.setDepth(51);
    this.battleLogText.setMaxLines(4);

    // Move panel background
    this.movePanel = this.add.rectangle(
      width - 320 - padding,
      height - 200,
      320,
      180,
      0x1a1a2e,
      0.95
    );
    this.movePanel.setOrigin(0, 0);
    this.movePanel.setDepth(50);
    this.movePanel.setStrokeStyle(2, 0x2a8a98);

    // Move title
    this.add.text(
      width - 312 - padding,
      height - 190,
      'Select Move:',
      {
        font: 'bold 14px Arial',
        fill: '#ffffff',
      }
    );
  }

  /**
   * Create team displays
   */
  createTeamDisplays() {
    const padding = 16;

    // Player team display (left side)
    this.playerTeamDisplay = this.add.container(padding, padding);
    this.playerTeamDisplay.setDepth(40);

    this.playerTeam.forEach((echo, index) => {
      this.createEchoDisplay(echo, index, true);
    });

    // Opponent team display (right side)
    this.opponentTeamDisplay = this.add.container(
      this.cameras.main.width - padding - 150,
      padding
    );
    this.opponentTeamDisplay.setDepth(40);

    this.opponentTeam.forEach((echo, index) => {
      this.createEchoDisplay(echo, index, false);
    });
  }

  /**
   * Create individual echo display
   */
  createEchoDisplay(echo, index, isPlayer) {
    const yOffset = index * 140;
    const container = this.add.container(0, yOffset);

    // Echo name
    const nameText = this.add.text(0, 0, echo.name || `Echo ${index + 1}`, {
      font: 'bold 12px Arial',
      fill: isPlayer ? '#aaffaa' : '#ffaaaa',
    });
    container.add(nameText);

    // Health bar background
    const hpBgWidth = 120;
    const hpBg = this.add.rectangle(0, 16, hpBgWidth, 12, 0x333333, 0.8);
    hpBg.setOrigin(0, 0);
    container.add(hpBg);

    // Health bar fill
    const hpBar = this.add.rectangle(0, 16, hpBgWidth, 12, 0x00ff00, 1);
    hpBar.setOrigin(0, 0);
    container.add(hpBar);
    echo.battleUI = { hpBar, nameText, container };

    // HP text
    const hpText = this.add.text(
      0,
      32,
      `HP: ${echo.battleData.currentHP}/${echo.battleData.maxHP}`,
      {
        font: '10px Arial',
        fill: '#cccccc',
      }
    );
    container.add(hpText);
    echo.battleUI.hpText = hpText;

    // Level display
    const levelText = this.add.text(130, 0, `Lv.${echo.level || 1}`, {
      font: '10px Arial',
      fill: '#cccccc',
    });
    container.add(levelText);

    if (isPlayer) {
      this.playerTeamDisplay.add(container);
    } else {
      this.opponentTeamDisplay.add(container);
    }
  }

  /**
   * Calculate turn order based on speed stats
   */
  calculateTurnOrder() {
    const allCombatants = [
      ...this.playerTeam.map((e) => ({ echo: e, isPlayer: true })),
      ...this.opponentTeam.map((e) => ({ echo: e, isPlayer: false })),
    ];

    // Sort by speed stat (highest first)
    this.turnOrder = allCombatants.sort(
      (a, b) => (b.echo.stats?.speed || 10) - (a.echo.stats?.speed || 10)
    );

    console.log('Turn order calculated:', this.turnOrder.map((t) => t.echo.name));
  }

  /**
   * Start battle sequence
   */
  startBattle() {
    this.addBattleLog('Battle started!');
    this.time.delayedCall(1000, () => {
      this.nextTurn();
    });
  }

  /**
   * Process next turn
   */
  nextTurn() {
    if (!this.battleState.battleActive) return;

    // Get next combatant
    const combatant = this.turnOrder[0];
    this.currentTurn = combatant;

    if (combatant.isPlayer) {
      // Player turn - wait for input
      this.displayPlayerTurnUI(combatant.echo);
    } else {
      // AI turn
      this.time.delayedCall(800, () => {
        this.executeAITurn(combatant.echo);
      });
    }
  }

  /**
   * Display player turn UI
   */
  displayPlayerTurnUI(playerEcho) {
    this.addBattleLog(`${playerEcho.name}'s turn!`);

    // Show available moves
    const moves = playerEcho.moves || [];
    const movePanel = this.movePanel;

    // Clear previous move buttons
    this.input.keyboard.off('keydown-1');
    this.input.keyboard.off('keydown-2');
    this.input.keyboard.off('keydown-3');
    this.input.keyboard.off('keydown-4');

    // Create move buttons (1-4 keys)
    moves.forEach((move, index) => {
      const keyNumber = index + 1;
      this.input.keyboard.on(`keydown-${keyNumber}`, () => {
        this.selectMove(move, playerEcho);
      });
    });
  }

  /**
   * Select move and target
   */
  selectMove(move, caster) {
    this.selectedMove = move;

    // Determine target
    if (move.targetType === 'enemy') {
      const target = this.opponentTeam[0];
      this.executeMove(caster, move, target);
    } else if (move.targetType === 'ally') {
      const target = caster;
      this.executeMove(caster, move, target);
    }
  }

  /**
   * Execute move and calculate damage
   */
  executeMove(caster, move, target) {
    if (this.isAnimating) return;
    this.isAnimating = true;

    // Create animation
    this.createMoveAnimation(caster, move, target);

    // Calculate damage
    const damage = this.calculateDamage(caster, move, target);
    const accuracy = move.accuracy || 100;
    const hit = Math.random() * 100 < accuracy;

    if (hit) {
      target.battleData.currentHP = Math.max(0, target.battleData.currentHP - damage);
      this.addBattleLog(`${caster.name} used ${move.name}! Dealt ${damage} damage!`);
      this.showDamageNumber(target, damage);
    } else {
      this.addBattleLog(`${caster.name}'s ${move.name} missed!`);
    }

    // Check for battle end
    this.time.delayedCall(800, () => {
      this.isAnimating = false;
      this.checkBattleEnd();

      if (this.battleState.battleActive) {
        // Rotate turn order
        this.turnOrder.push(this.turnOrder.shift());
        this.time.delayedCall(500, () => this.nextTurn());
      }
    });
  }

  /**
   * Execute AI turn
   */
  executeAITurn(aiEcho) {
    // Select random move
    const moves = aiEcho.moves || [];
    const move = moves[Math.floor(Math.random() * moves.length)];
    const target = this.playerTeam[0];

    this.executeMove(aiEcho, move, target);
  }

  /**
   * Calculate damage
   */
  calculateDamage(attacker, move, defender) {
    const baseAttack = attacker.stats?.attack || 10;
    const baseDefense = defender.stats?.defense || 10;
    const power = move.power || 10;

    // Simple damage formula
    const damage = Math.round(
      ((baseAttack / baseDefense) * power + Math.random() * 5 - 2.5)
    );

    return Math.max(1, damage);
  }

  /**
   * Create move animation
   */
  createMoveAnimation(caster, move, target) {
    // Simple tween animation
    this.tweens.add({
      targets: caster.battleUI.container,
      x: target.battleUI.container.x,
      duration: 400,
      yoyo: true,
    });
  }

  /**
   * Show damage number floating text
   */
  showDamageNumber(target, damage) {
    const container = target.battleUI.container;
    const damageText = this.add.text(
      container.x + 50,
      container.y - 30,
      `-${damage}`,
      {
        font: 'bold 20px Arial',
        fill: '#ff6666',
      }
    );
    damageText.setOrigin(0.5);
    damageText.setDepth(100);

    this.tweens.add({
      targets: damageText,
      y: damageText.y - 40,
      alpha: 0,
      duration: 1000,
      onComplete: () => damageText.destroy(),
    });
  }

  /**
   * Update health bars
   */
  updateHealthBars() {
    this.playerTeam.forEach((echo) => {
      if (echo.battleUI) {
        const percentage =
          echo.battleData.currentHP / echo.battleData.maxHP;
        echo.battleUI.hpBar.width = 120 * Math.max(0, percentage);
        echo.battleUI.hpText.setText(
          `HP: ${echo.battleData.currentHP}/${echo.battleData.maxHP}`
        );
      }
    });

    this.opponentTeam.forEach((echo) => {
      if (echo.battleUI) {
        const percentage =
          echo.battleData.currentHP / echo.battleData.maxHP;
        echo.battleUI.hpBar.width = 120 * Math.max(0, percentage);
        echo.battleUI.hpText.setText(
          `HP: ${echo.battleData.currentHP}/${echo.battleData.maxHP}`
        );
      }
    });
  }

  /**
   * Update status effects display
   */
  updateStatusEffects() {
    [...this.playerTeam, ...this.opponentTeam].forEach((echo) => {
      if (echo.battleData.statusEffects.length > 0) {
        // Display status effect indicators
      }
    });
  }

  /**
   * Update turn display
   */
  updateTurnDisplay() {
    if (this.currentTurn) {
      const info = `Round: ${this.battleState.round} | ${this.currentTurn.echo.name}'s Turn`;
      // Update turn display UI
    }
  }

  /**
   * Check battle end condition
   */
  checkBattleEnd() {
    const playerDefeated = this.playerTeam.every(
      (e) => e.battleData.currentHP <= 0
    );
    const opponentDefeated = this.opponentTeam.every(
      (e) => e.battleData.currentHP <= 0
    );

    if (playerDefeated) {
      this.endBattle('loss');
    } else if (opponentDefeated) {
      this.endBattle('victory');
    }
  }

  /**
   * End battle
   */
  endBattle(result) {
    this.battleState.battleActive = false;

    if (result === 'victory') {
      this.addBattleLog('Victory! Battle won!');
      this.time.delayedCall(2000, () => {
        this.scene.stop();
        this.scene.resume('WorldScene');
      });
    } else {
      this.addBattleLog('Defeat! Battle lost!');
      this.time.delayedCall(2000, () => {
        this.scene.stop();
        this.scene.resume('WorldScene');
      });
    }
  }

  /**
   * Add message to battle log
   */
  addBattleLog(message) {
    this.battleLog.push(message);
    if (this.battleLog.length > 4) {
      this.battleLog.shift();
    }

    if (this.battleLogText) {
      this.battleLogText.setText(this.battleLog.join('\n'));
    }
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    this.events.on('shutdown', () => {
      this.cleanup();
    });
  }

  /**
   * Cleanup on scene shutdown
   */
  cleanup() {
    this.input.keyboard.off('keydown-1');
    this.input.keyboard.off('keydown-2');
    this.input.keyboard.off('keydown-3');
    this.input.keyboard.off('keydown-4');
  }
}

export default CombatScene;
