/**
 * ChronoRift HUD (Heads-Up Display)
 * In-game UI system for displaying player stats, minimap, notifications, and quick actions
 * Manages overlay interface elements during gameplay
 */

export class HUD {
  constructor(scene) {
    this.scene = scene;
    this.elements = {};
    this.isVisible = true;
    this.notifications = [];
    this.maxNotifications = 3;
  }

  /**
   * Initialize HUD elements
   */
  initialize() {
    this.createPlayerStatsPanel();
    this.createMinimap();
    this.createNotificationQueue();
    this.createQuickActionBar();
    this.createStatusEffectPanel();
    this.createCurrencyDisplay();
  }

  /**
   * Create player stats panel (top-left)
   */
  createPlayerStatsPanel() {
    const padding = 16;
    const panelWidth = 200;
    const panelHeight = 120;

    // Panel background
    const statsPanel = this.scene.add.rectangle(
      padding,
      padding,
      panelWidth,
      panelHeight,
      0x1a1a2e,
      0.8
    );
    statsPanel.setOrigin(0, 0);
    statsPanel.setDepth(100);
    statsPanel.setStrokeStyle(2, 0x2a8a98);

    // Player name
    const playerName = this.scene.add.text(
      padding + 8,
      padding + 8,
      'Player Name',
      {
        font: 'bold 12px Arial',
        fill: '#aaffaa',
      }
    );
    playerName.setDepth(101);

    // Level display
    const levelText = this.scene.add.text(
      padding + 8,
      padding + 28,
      'Level: 1',
      {
        font: '11px Arial',
        fill: '#ffff99',
      }
    );
    levelText.setDepth(101);

    // Experience bar background
    const expBgWidth = panelWidth - 16;
    const expBarBg = this.scene.add.rectangle(
      padding + 8,
      padding + 50,
      expBgWidth,
      10,
      0x333333,
      0.8
    );
    expBarBg.setOrigin(0, 0);
    expBarBg.setDepth(100);

    // Experience bar fill
    const expBar = this.scene.add.rectangle(
      padding + 8,
      padding + 50,
      expBgWidth * 0.65,
      10,
      0xffaa00,
      1
    );
    expBar.setOrigin(0, 0);
    expBar.setDepth(101);

    // Experience text
    const expText = this.scene.add.text(
      padding + 8,
      padding + 65,
      'EXP: 650 / 1000',
      {
        font: '9px Arial',
        fill: '#cccccc',
      }
    );
    expText.setDepth(101);

    // Store references
    this.elements.statsPanel = {
      bg: statsPanel,
      playerName,
      levelText,
      expBar,
      expText,
    };
  }

  /**
   * Create minimap display (top-right)
   */
  createMinimap() {
    const padding = 16;
    const minimapSize = 120;

    // Minimap background
    const minimapBg = this.scene.add.rectangle(
      this.scene.cameras.main.width - padding - minimapSize,
      padding,
      minimapSize,
      minimapSize,
      0x1a1a2e,
      0.8
    );
    minimapBg.setOrigin(0, 0);
    minimapBg.setDepth(100);
    minimapBg.setStrokeStyle(2, 0x2a8a98);

    // Minimap content area (darker background)
    const minimapContent = this.scene.add.rectangle(
      this.scene.cameras.main.width - padding - minimapSize + 4,
      padding + 20,
      minimapSize - 8,
      minimapSize - 24,
      0x0a0a1e,
      0.9
    );
    minimapContent.setOrigin(0, 0);
    minimapContent.setDepth(101);

    // Minimap title
    const minimapTitle = this.scene.add.text(
      this.scene.cameras.main.width - padding - minimapSize + 4,
      padding + 4,
      'Zone Map',
      {
        font: 'bold 10px Arial',
        fill: '#2a8a98',
      }
    );
    minimapTitle.setDepth(102);

    // Player indicator (white dot)
    const playerIndicator = this.scene.add.circle(
      this.scene.cameras.main.width - padding - minimapSize / 2,
      padding + minimapSize / 2,
      3,
      0xffffff,
      1
    );
    playerIndicator.setDepth(102);

    // Enemy indicators (red dots)
    for (let i = 0; i < 3; i++) {
      const enemyX = Phaser.Math.Between(
        this.scene.cameras.main.width - padding - minimapSize + 8,
        this.scene.cameras.main.width - padding - 12
      );
      const enemyY = Phaser.Math.Between(padding + 24, padding + minimapSize - 8);

      const enemy = this.scene.add.circle(enemyX, enemyY, 2, 0xff6666, 1);
      enemy.setDepth(102);
    }

    this.elements.minimap = {
      bg: minimapBg,
      content: minimapContent,
      title: minimapTitle,
      playerIndicator,
    };
  }

  /**
   * Create notification queue display (top-center)
   */
  createNotificationQueue() {
    const centerX = this.scene.cameras.main.width / 2;
    const notifyStartY = 16;

    this.elements.notificationContainer = this.scene.add.container(
      centerX,
      notifyStartY
    );
    this.elements.notificationContainer.setDepth(200);
  }

  /**
   * Create quick action bar (bottom center)
   */
  createQuickActionBar() {
    const width = this.scene.cameras.main.width;
    const height = this.scene.cameras.main.height;
    const padding = 16;

    // Quick action bar background
    const quickActionBg = this.scene.add.rectangle(
      width / 2,
      height - padding - 30,
      300,
      60,
      0x1a1a2e,
      0.85
    );
    quickActionBg.setOrigin(0.5, 0);
    quickActionBg.setDepth(100);
    quickActionBg.setStrokeStyle(2, 0x2a8a98);

    // Quick action buttons
    const buttons = [
      { label: 'Team (T)', key: 'T', x: -120 },
      { label: 'Inventory (I)', key: 'I', x: -40 },
      { label: 'Menu (M)', key: 'M', x: 40 },
      { label: 'Map (K)', key: 'K', x: 120 },
    ];

    buttons.forEach((btn) => {
      const btnX = width / 2 + btn.x;
      const btnY = height - padding - 10;

      const button = this.scene.add.rectangle(
        btnX,
        btnY,
        70,
        30,
        0x2a5a6a,
        1
      );
      button.setOrigin(0.5, 0.5);
      button.setStrokeStyle(1, 0x1a8a98);
      button.setInteractive({ useHandCursor: true });
      button.setDepth(101);

      const text = this.scene.add.text(btnX, btnY, btn.label, {
        font: 'bold 9px Arial',
        fill: '#ffffff',
      });
      text.setOrigin(0.5, 0.5);
      text.setDepth(102);

      button.on('pointerover', () => {
        button.setFillStyle(0x3a7a8a, 1);
      });

      button.on('pointerout', () => {
        button.setFillStyle(0x2a5a6a, 1);
      });

      button.on('pointerdown', () => {
        this.handleQuickAction(btn.key);
      });
    });

    this.elements.quickActionBar = { bg: quickActionBg, buttons };
  }

  /**
   * Create status effect panel (below player stats)
   */
  createStatusEffectPanel() {
    const padding = 16;
    const panelX = padding;
    const panelY = padding + 130;
    const panelWidth = 200;
    const panelHeight = 60;

    // Status panel background
    const statusPanel = this.scene.add.rectangle(
      panelX,
      panelY,
      panelWidth,
      panelHeight,
      0x1a1a2e,
      0.8
    );
    statusPanel.setOrigin(0, 0);
    statusPanel.setDepth(100);
    statusPanel.setStrokeStyle(2, 0x2a8a98);

    // Status title
    const statusTitle = this.scene.add.text(panelX + 8, panelY + 8, 'Status', {
      font: 'bold 10px Arial',
      fill: '#aaffaa',
    });
    statusTitle.setDepth(101);

    // Status effects container
    const statusContainer = this.scene.add.container(panelX + 8, panelY + 24);
    statusContainer.setDepth(101);

    // Example status effects (will be updated dynamically)
    const statuses = ['Healthy', 'Focused'];
    let xOffset = 0;

    statuses.forEach((status) => {
      const statusBg = this.scene.add.rectangle(xOffset, 0, 80, 18, 0x2a5a5a, 1);
      statusBg.setOrigin(0, 0);
      statusBg.setStrokeStyle(1, 0x2a8a98);

      const statusText = this.scene.add.text(xOffset + 4, 2, status, {
        font: '9px Arial',
        fill: '#aaffaa',
      });

      statusContainer.add([statusBg, statusText]);
      xOffset += 85;
    });

    this.elements.statusPanel = {
      bg: statusPanel,
      title: statusTitle,
      container: statusContainer,
    };
  }

  /**
   * Create currency display (top-right below minimap)
   */
  createCurrencyDisplay() {
    const padding = 16;
    const minimapSize = 120;
    const startX = this.scene.cameras.main.width - padding - minimapSize;
    const startY = padding + minimapSize + 20;

    // Currency background
    const currencyBg = this.scene.add.rectangle(
      startX,
      startY,
      minimapSize,
      80,
      0x1a1a2e,
      0.8
    );
    currencyBg.setOrigin(0, 0);
    currencyBg.setDepth(100);
    currencyBg.setStrokeStyle(2, 0x2a8a98);

    // Currency title
    const currencyTitle = this.scene.add.text(
      startX + 8,
      startY + 4,
      'Resources',
      {
        font: 'bold 10px Arial',
        fill: '#ffff99',
      }
    );
    currencyTitle.setDepth(101);

    // Currency types
    const currencies = [
      { label: 'Gold:', value: '2500', color: '#ffff99' },
      { label: 'Gems:', value: '150', color: '#ff99ff' },
      { label: 'Tickets:', value: '8', color: '#99ffff' },
    ];

    let yOffset = 24;
    currencies.forEach((curr) => {
      const label = this.scene.add.text(startX + 8, startY + yOffset, curr.label, {
        font: '9px Arial',
        fill: '#cccccc',
      });
      label.setDepth(101);

      const value = this.scene.add.text(
        startX + minimapSize - 16,
        startY + yOffset,
        curr.value,
        {
          font: 'bold 9px Arial',
          fill: curr.color,
        }
      );
      value.setOrigin(1, 0);
      value.setDepth(101);

      yOffset += 18;
    });

    this.elements.currency = { bg: currencyBg, title: currencyTitle };
  }

  /**
   * Add notification to queue
   */
  addNotification(message, type = 'info', duration = 3000) {
    if (this.notifications.length >= this.maxNotifications) {
      const oldest = this.notifications.shift();
      oldest.destroy();
    }

    const centerX = this.scene.cameras.main.width / 2;
    const yPos = 50 + this.notifications.length * 50;

    // Determine color based on type
    const colorMap = {
      info: '#aaffaa',
      success: '#00ff00',
      warning: '#ffff00',
      error: '#ff6666',
    };
    const color = colorMap[type] || '#aaffaa';

    // Notification background
    const notifyBg = this.scene.add.rectangle(
      centerX,
      yPos,
      300,
      40,
      0x1a1a2e,
      0.9
    );
    notifyBg.setOrigin(0.5, 0);
    notifyBg.setDepth(200);
    notifyBg.setStrokeStyle(2, color);

    // Notification text
    const notifyText = this.scene.add.text(centerX, yPos + 10, message, {
      font: '12px Arial',
      fill: color,
      align: 'center',
      wordWrap: { width: 280, useAdvancedWrap: true },
    });
    notifyText.setOrigin(0.5, 0);
    notifyText.setDepth(201);

    // Notification container
    const container = this.scene.add.container(0, 0, [notifyBg, notifyText]);
    container.setDepth(200);

    // Auto-fade after duration
    this.scene.tweens.add({
      targets: [notifyBg, notifyText],
      alpha: 0,
      duration: 1000,
      delay: duration - 1000,
      onComplete: () => {
        container.destroy();
        this.notifications = this.notifications.filter((n) => n !== container);
      },
    });

    this.notifications.push(container);
  }

  /**
   * Update player stats display
   */
  updatePlayerStats(playerData) {
    if (!this.elements.statsPanel) return;

    this.elements.statsPanel.playerName.setText(playerData.username || 'Player');
    this.elements.statsPanel.levelText.setText(`Level: ${playerData.level || 1}`);

    const expPercent = (playerData.experience || 0) / (playerData.nextLevelExp || 1000);
    this.elements.statsPanel.expBar.width = (200 - 16) * Math.min(1, expPercent);
    this.elements.statsPanel.expText.setText(
      `EXP: ${playerData.experience || 0} / ${playerData.nextLevelExp || 1000}`
    );
  }

  /**
   * Update currency display
   */
  updateCurrency(gold, gems, tickets) {
    // Update currency values in display
    // Implementation depends on storing text references
  }

  /**
   * Update status effects
   */
  updateStatusEffects(effects) {
    if (!this.elements.statusPanel) return;

    // Clear current effects
    this.elements.statusPanel.container.removeAll();

    // Add new effects
    let xOffset = 0;
    effects.forEach((effect) => {
      const statusBg = this.scene.add.rectangle(
        xOffset,
        0,
        80,
        18,
        0x2a5a5a,
        1
      );
      statusBg.setOrigin(0, 0);
      statusBg.setStrokeStyle(1, 0x2a8a98);

      const statusText = this.scene.add.text(xOffset + 4, 2, effect, {
        font: '9px Arial',
        fill: '#aaffaa',
      });

      this.elements.statusPanel.container.add([statusBg, statusText]);
      xOffset += 85;
    });
  }

  /**
   * Update minimap display
   */
  updateMinimap(playerPos, enemies, objectives) {
    if (!this.elements.minimap) return;

    // Update player position indicator
    if (playerPos) {
      // Scale world coords to minimap
      this.elements.minimap.playerIndicator.x = playerPos.x;
      this.elements.minimap.playerIndicator.y = playerPos.y;
    }
  }

  /**
   * Toggle HUD visibility
   */
  toggleVisibility() {
    this.isVisible = !this.isVisible;

    Object.values(this.elements).forEach((element) => {
      if (element && element.bg) {
        element.bg.setVisible(this.isVisible);
      }
    });
  }

  /**
   * Handle quick action button press
   */
  handleQuickAction(key) {
    switch (key) {
      case 'T':
        this.scene.scene.pause();
        this.scene.scene.launch('TeamMenuScene');
        break;
      case 'I':
        this.scene.scene.pause();
        this.scene.scene.launch('InventoryScene');
        break;
      case 'M':
        this.scene.scene.pause();
        this.scene.scene.launch('MenuScene');
        break;
      case 'K':
        this.scene.scene.pause();
        this.scene.scene.launch('MapScene');
        break;
    }
  }

  /**
   * Update HUD each frame
   */
  update() {
    // Update animations or real-time elements
    // Called from scene's update method
  }

  /**
   * Destroy HUD and cleanup
   */
  destroy() {
    Object.values(this.elements).forEach((element) => {
      if (element && element.bg) {
        element.bg.destroy();
      }
    });

    this.notifications.forEach((notification) => {
      notification.destroy();
    });

    this.elements = {};
    this.notifications = [];
  }
}

export default HUD;
