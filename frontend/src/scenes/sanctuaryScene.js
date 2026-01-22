/**
 * ChronoRift Sanctuary Scene
 * Safe haven where players manage Echo team, heal, bond, and prepare for adventures
 * Features team management, bonding system, healing, and upgrades
 */

import Phaser from 'phaser';

export class SanctuaryScene extends Phaser.Scene {
  constructor() {
    super({ key: 'SanctuaryScene' });
    this.playerTeam = [];
    this.selectedEcho = null;
    this.currentView = 'main';
    this.bondingProgression = {};
  }

  /**
   * Scene init
   */
  init(data) {
    this.playerTeam = data.playerTeam || this.registry.get('team') || [];
    this.bondingProgression = this.registry.get('bonding') || {};
  }

  /**
   * Scene create - Initialize sanctuary
   */
  create() {
    // Create sanctuary environment
    this.createSanctuaryEnvironment();

    // Create main UI
    this.createMainUI();

    // Create team roster display
    this.createTeamRoster();

    // Create action panels
    this.createActionPanels();

    // Setup input handling
    this.setupInputHandling();

    // Setup event listeners
    this.setupEventListeners();
  }

  /**
   * Scene update
   */
  update() {
    // Update animations
    this.updateAnimations();

    // Update bonding effects
    this.updateBondingEffects();
  }

  /**
   * Create sanctuary environment
   */
  createSanctuaryEnvironment() {
    // Sanctuary background
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const bg = this.add.rectangle(0, 0, width, height, 0x1a2a1a, 1);
    bg.setOrigin(0, 0);
    bg.setDepth(-100);

    // Gradient overlay
    const gradient = this.make.graphics({ x: 0, y: 0, add: false });
    gradient.fillStyle(0x2a4a2a, 0.3);
    gradient.fillRect(0, 0, width, height);
    gradient.generateTexture('sanctuaryGradient', width, height);
    gradient.destroy();

    const gradientSprite = this.add.image(0, 0, 'sanctuaryGradient');
    gradientSprite.setOrigin(0, 0);
    gradientSprite.setDepth(-95);

    // Ambient particles (healing aura)
    this.createAmbientParticles();

    // Sanctuary title
    this.add.text(width / 2, 20, 'Echo Sanctuary', {
      font: 'bold 28px Arial',
      fill: '#aaffaa',
      align: 'center',
    }).setOrigin(0.5, 0).setDepth(10);
  }

  /**
   * Create ambient particle effects
   */
  createAmbientParticles() {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Floating healing particles
    for (let i = 0; i < 8; i++) {
      const x = Phaser.Math.Between(100, width - 100);
      const y = Phaser.Math.Between(100, height - 100);

      const particle = this.add.circle(x, y, 3, 0x2a8a98, 0.6);
      particle.setDepth(0);

      this.tweens.add({
        targets: particle,
        y: particle.y - 50,
        alpha: 0,
        duration: 3000,
        delay: i * 200,
        repeat: -1,
        repeatDelay: 2000,
      });
    }
  }

  /**
   * Create main UI layout
   */
  createMainUI() {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;
    const padding = 16;

    // Left panel - Team roster
    const leftPanelX = padding;
    const leftPanelY = 70;
    const leftPanelWidth = 250;
    const leftPanelHeight = height - 120;

    const leftPanel = this.add.rectangle(
      leftPanelX,
      leftPanelY,
      leftPanelWidth,
      leftPanelHeight,
      0x1a1a2e,
      0.85
    );
    leftPanel.setOrigin(0, 0);
    leftPanel.setDepth(5);
    leftPanel.setStrokeStyle(2, 0x2a8a98);
    this.leftPanel = leftPanel;

    // Right panel - Action panel
    const rightPanelX = width - 350 - padding;
    const rightPanelY = 70;
    const rightPanelWidth = 350;
    const rightPanelHeight = height - 120;

    const rightPanel = this.add.rectangle(
      rightPanelX,
      rightPanelY,
      rightPanelWidth,
      rightPanelHeight,
      0x1a1a2e,
      0.85
    );
    rightPanel.setOrigin(0, 0);
    rightPanel.setDepth(5);
    rightPanel.setStrokeStyle(2, 0x2a8a98);
    this.rightPanel = rightPanel;

    // Bottom info panel
    const infoPanelY = height - 50;
    const infoPanel = this.add.rectangle(
      width / 2,
      infoPanelY,
      width - 32,
      50,
      0x1a1a2e,
      0.85
    );
    infoPanel.setOrigin(0.5, 0);
    infoPanel.setDepth(5);
    infoPanel.setStrokeStyle(2, 0x2a8a98);

    // Help text
    this.add.text(
      padding + 8,
      infoPanelY + 10,
      'M: Menu | E: Exit | Arrow Keys: Navigate',
      {
        font: '11px Arial',
        fill: '#888888',
      }
    ).setDepth(6);
  }

  /**
   * Create team roster display
   */
  createTeamRoster() {
    const padding = 16;
    const startX = padding + 12;
    const startY = 100;
    const spacing = 70;

    this.rosterContainer = this.add.container(startX, startY);
    this.rosterContainer.setDepth(10);

    this.playerTeam.forEach((echo, index) => {
      this.createTeamMember(echo, index, spacing);
    });

    // Add empty slots
    const emptySlots = 6 - this.playerTeam.length;
    for (let i = 0; i < emptySlots; i++) {
      this.createEmptySlot(this.playerTeam.length + i, spacing);
    }
  }

  /**
   * Create team member card
   */
  createTeamMember(echo, index, spacing) {
    const yOffset = index * spacing;
    const container = this.add.container(0, yOffset);

    // Background
    const bg = this.add.rectangle(0, 0, 220, 60, 0x2a2a4e, 0.8);
    bg.setOrigin(0, 0);
    container.add(bg);

    // Border
    bg.setStrokeStyle(2, 0x2a8a98);

    // Echo name
    const nameText = this.add.text(8, 4, echo.name || 'Echo', {
      font: 'bold 12px Arial',
      fill: '#aaffaa',
    });
    container.add(nameText);

    // Level
    const levelText = this.add.text(140, 4, `Lv.${echo.level || 1}`, {
      font: 'bold 11px Arial',
      fill: '#ffff99',
    });
    container.add(levelText);

    // HP bar
    const hpBarBg = this.add.rectangle(8, 22, 100, 8, 0x333333, 0.8);
    hpBarBg.setOrigin(0, 0);
    container.add(hpBarBg);

    const hpPercent = (echo.stats?.hp || 100) / (echo.stats?.hp || 100);
    const hpBar = this.add.rectangle(
      8,
      22,
      100 * hpPercent,
      8,
      0x00aa00,
      1
    );
    hpBar.setOrigin(0, 0);
    container.add(hpBar);

    // HP text
    this.add.text(120, 20, `HP: ${echo.stats?.hp || 100}`, {
      font: '9px Arial',
      fill: '#cccccc',
    }).setOrigin(0, 0);

    // Bonding level indicator
    const bondingLevel = this.bondingProgression[echo.id] || 1;
    const bondText = this.add.text(8, 38, `Bond: ${bondingLevel}/10`, {
      font: '10px Arial',
      fill: '#ffaaff',
    });
    container.add(bondText);

    // Status indicator
    const statusText = this.add.text(120, 38, 'Healthy', {
      font: '10px Arial',
      fill: '#aaffaa',
    });
    container.add(statusText);

    // Interactive button
    bg.setInteractive({ useHandCursor: true });
    bg.on('pointerover', () => {
      bg.setFillStyle(0x3a3a5e, 0.9);
    });
    bg.on('pointerout', () => {
      bg.setFillStyle(0x2a2a4e, 0.8);
    });
    bg.on('pointerdown', () => {
      this.selectEcho(echo, index, container);
    });

    echo.rosterCard = container;
    this.rosterContainer.add(container);
  }

  /**
   * Create empty team slot
   */
  createEmptySlot(index, spacing) {
    const yOffset = index * spacing;
    const container = this.add.container(0, yOffset);

    // Background
    const bg = this.add.rectangle(0, 0, 220, 60, 0x1a1a3e, 0.5);
    bg.setOrigin(0, 0);
    bg.setStrokeStyle(2, 0x555555);
    container.add(bg);

    // Empty text
    this.add.text(80, 20, 'Empty Slot', {
      font: '11px Arial',
      fill: '#555555',
    }).setOrigin(0.5, 0.5);

    this.rosterContainer.add(container);
  }

  /**
   * Select Echo for action
   */
  selectEcho(echo, index, card) {
    this.selectedEcho = echo;
    this.currentEchoIndex = index;

    // Highlight selected card
    if (this.lastSelectedCard) {
      this.lastSelectedCard.getByName('bg')?.setStrokeStyle(2, 0x2a8a98);
    }

    // Update action panel
    this.updateActionPanel(echo);

    // Visual feedback
    this.tweens.add({
      targets: card,
      scaleX: 1.05,
      scaleY: 1.05,
      duration: 150,
      yoyo: true,
    });

    this.lastSelectedCard = card;
  }

  /**
   * Update action panel with echo details
   */
  updateActionPanel(echo) {
    const width = this.cameras.main.width;
    const padding = 16;
    const panelX = width - 350 - padding + 12;
    const panelY = 100;

    // Clear previous panel content
    if (this.actionPanelContent) {
      this.actionPanelContent.destroy(true);
    }

    this.actionPanelContent = this.add.container(panelX, panelY);
    this.actionPanelContent.setDepth(11);

    // Echo stats header
    this.add.text(0, 0, `${echo.name} - Details`, {
      font: 'bold 14px Arial',
      fill: '#aaffaa',
    });

    // Stats display
    const stats = echo.stats || {};
    let yOffset = 30;

    const statEntries = [
      { label: 'HP:', value: stats.hp || 100 },
      { label: 'ATK:', value: stats.attack || 10 },
      { label: 'DEF:', value: stats.defense || 10 },
      { label: 'SP.ATK:', value: stats.spAtk || 10 },
      { label: 'SP.DEF:', value: stats.spDef || 10 },
      { label: 'SPD:', value: stats.speed || 10 },
    ];

    statEntries.forEach((entry) => {
      this.add.text(0, yOffset, `${entry.label}`, {
        font: '11px Arial',
        fill: '#cccccc',
      });

      this.add.text(60, yOffset, `${entry.value}`, {
        font: 'bold 11px Arial',
        fill: '#ffff99',
      });

      yOffset += 25;
    });

    // Action buttons
    yOffset += 10;

    // Heal button
    this.createActionButton('HEAL', 0, yOffset, () => {
      this.healEcho(echo);
    });

    // Bond button
    this.createActionButton('BOND', 100, yOffset, () => {
      this.bondWithEcho(echo);
    });

    // Release button
    this.createActionButton('RELEASE', 200, yOffset, () => {
      this.releaseEcho(echo);
    });

    this.actionPanelContent.add(this.add.container());
  }

  /**
   * Create action button
   */
  createActionButton(label, x, y, callback) {
    const btn = this.add.rectangle(x, y, 90, 30, 0x2a8a98, 1);
    btn.setOrigin(0, 0);
    btn.setStrokeStyle(1, 0x1a5a68);
    btn.setInteractive({ useHandCursor: true });

    btn.on('pointerover', () => btn.setFillStyle(0x3aaa98, 1));
    btn.on('pointerout', () => btn.setFillStyle(0x2a8a98, 1));
    btn.on('pointerdown', callback);

    const text = this.add.text(x + 45, y + 15, label, {
      font: 'bold 10px Arial',
      fill: '#ffffff',
    });
    text.setOrigin(0.5, 0.5);

    this.actionPanelContent.add([btn, text]);
  }

  /**
   * Heal Echo
   */
  healEcho(echo) {
    const cost = 50; // Currency cost
    const playerCurrency = this.registry.get('player').currency || 0;

    if (playerCurrency < cost) {
      this.showNotification('Insufficient currency!', '#ff6666');
      return;
    }

    // Heal echo
    echo.stats.hp = echo.stats.maxHP || 100;

    // Deduct currency
    const player = this.registry.get('player');
    player.currency -= cost;
    this.registry.set('player', player);

    this.showNotification(`${echo.name} has been healed!`, '#aaffaa');

    // Update display
    this.createTeamRoster();
  }

  /**
   * Bond with Echo
   */
  bondWithEcho(echo) {
    const bondingLevel = this.bondingProgression[echo.id] || 1;

    if (bondingLevel >= 10) {
      this.showNotification('Bond is already maxed!', '#ffff99');
      return;
    }

    // Increase bonding
    this.bondingProgression[echo.id] = bondingLevel + 1;
    this.registry.set('bonding', this.bondingProgression);

    // Stat boost (small increase)
    echo.stats.attack = (echo.stats.attack || 10) + 1;
    echo.stats.defense = (echo.stats.defense || 10) + 0.5;

    this.showNotification(`Bond increased! (${bondingLevel + 1}/10)`, '#ffaaff');

    // Update display
    this.createTeamRoster();
  }

  /**
   * Release Echo from team
   */
  releaseEcho(echo) {
    // Confirm dialog
    const confirmDelete = confirm(
      `Are you sure you want to release ${echo.name}? This cannot be undone.`
    );

    if (!confirmDelete) return;

    // Remove from team
    this.playerTeam = this.playerTeam.filter((e) => e.id !== echo.id);
    this.registry.set('team', this.playerTeam);

    this.showNotification(`${echo.name} has been released.`, '#ffaaaa');

    // Update display
    this.createTeamRoster();
  }

  /**
   * Show notification message
   */
  showNotification(message, color = '#aaffaa') {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const text = this.add.text(width / 2, height / 2, message, {
      font: 'bold 18px Arial',
      fill: color,
      align: 'center',
    });
    text.setOrigin(0.5, 0.5);
    text.setDepth(100);

    this.tweens.add({
      targets: text,
      alpha: 0,
      duration: 2000,
      delay: 500,
      onComplete: () => text.destroy(),
    });
  }

  /**
   * Create action panels (static buttons)
   */
  createActionPanels() {
    // Exit button
    this.add.text(
      this.cameras.main.width - 50,
      20,
      '[E] Exit',
      {
        font: 'bold 12px Arial',
        fill: '#ffaaaa',
      }
    ).setOrigin(1, 0);
  }

  /**
   * Update animations
   */
  updateAnimations() {
    // Ambient effects
  }

  /**
   * Update bonding effects
   */
  updateBondingEffects() {
    // Visual indicators for bonding
  }

  /**
   * Setup input handling
   */
  setupInputHandling() {
    this.input.keyboard.on('keydown-E', () => {
      this.exitSanctuary();
    });

    this.input.keyboard.on('keydown-M', () => {
      this.scene.pause();
      this.scene.launch('MenuScene');
    });

    // Arrow key navigation (for roster scrolling if needed)
    this.cursors = this.input.keyboard.createCursorKeys();
  }

  /**
   * Exit sanctuary
   */
  exitSanctuary() {
    // Save team state
    this.registry.set('team', this.playerTeam);

    // Return to world
    this.scene.stop();
    this.scene.resume('WorldScene');
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
    this.input.keyboard.off('keydown-E');
    this.input.keyboard.off('keydown-M');
  }
}

export default SanctuaryScene;
