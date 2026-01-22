/**
 * ChronoRift UI Panels
 * Reusable panel components for displaying information, stats, and controls
 * Provides templates for stat panels, info boxes, dialog windows, and cards
 */

export class Panel {
  constructor(scene, options = {}) {
    this.scene = scene;
    this.x = options.x || 0;
    this.y = options.y || 0;
    this.width = options.width || 300;
    this.height = options.height || 200;
    this.title = options.title || '';
    this.backgroundColor = options.backgroundColor || 0x1a1a2e;
    this.borderColor = options.borderColor || 0x2a8a98;
    this.titleColor = options.titleColor || '#aaffaa';
    this.textColor = options.textColor || '#cccccc';
    this.padding = options.padding || 16;
    this.corner = options.corner || 8;

    this.container = null;
    this.content = null;
    this.elements = {};
  }

  /**
   * Create and display panel
   */
  create() {
    this.container = this.scene.add.container(this.x, this.y);
    this.container.setDepth(100);

    // Background
    const bg = this.scene.add.rectangle(
      0,
      0,
      this.width,
      this.height,
      this.backgroundColor,
      0.9
    );
    bg.setOrigin(0, 0);
    bg.setStrokeStyle(2, this.borderColor);
    this.container.add(bg);
    this.elements.background = bg;

    // Title bar (if title provided)
    if (this.title) {
      const titleBg = this.scene.add.rectangle(
        0,
        0,
        this.width,
        32,
        this.borderColor,
        0.3
      );
      titleBg.setOrigin(0, 0);
      this.container.add(titleBg);

      const titleText = this.scene.add.text(
        this.padding,
        8,
        this.title,
        {
          font: 'bold 14px Arial',
          fill: this.titleColor,
        }
      );
      titleText.setOrigin(0, 0);
      this.container.add(titleText);
      this.elements.title = titleText;
    }

    // Content area
    this.content = this.scene.add.container(
      this.padding,
      this.title ? 40 : this.padding
    );
    this.container.add(this.content);
    this.elements.content = this.content;

    return this;
  }

  /**
   * Add text to panel
   */
  addText(text, options = {}) {
    const y = options.y || (this.content.list.length * 24);

    const textObj = this.scene.add.text(0, y, text, {
      font: options.font || '12px Arial',
      fill: options.color || this.textColor,
      wordWrap: { width: this.width - this.padding * 2, useAdvancedWrap: true },
    });
    textObj.setOrigin(0, 0);

    this.content.add(textObj);
    return textObj;
  }

  /**
   * Add stat row (label + value)
   */
  addStat(label, value, options = {}) {
    const y = options.y || (this.content.list.length * 20);

    const labelText = this.scene.add.text(0, y, label, {
      font: options.font || '11px Arial',
      fill: this.textColor,
    });
    labelText.setOrigin(0, 0);
    this.content.add(labelText);

    const valueText = this.scene.add.text(
      this.width - this.padding * 2,
      y,
      String(value),
      {
        font: 'bold 11px Arial',
        fill: options.valueColor || '#ffff99',
      }
    );
    valueText.setOrigin(1, 0);
    this.content.add(valueText);

    return { label: labelText, value: valueText };
  }

  /**
   * Add progress bar
   */
  addProgressBar(label, current, max, options = {}) {
    const y = options.y || (this.content.list.length * 32);
    const barWidth = this.width - this.padding * 2;
    const barHeight = options.barHeight || 12;

    // Label
    const labelText = this.scene.add.text(0, y, label, {
      font: '11px Arial',
      fill: this.textColor,
    });
    labelText.setOrigin(0, 0);
    this.content.add(labelText);

    // Background
    const barBg = this.scene.add.rectangle(
      0,
      y + 16,
      barWidth,
      barHeight,
      0x333333,
      0.8
    );
    barBg.setOrigin(0, 0);
    this.content.add(barBg);

    // Fill
    const fillColor = options.fillColor || 0x00aa00;
    const fillWidth = barWidth * (current / max);
    const bar = this.scene.add.rectangle(
      0,
      y + 16,
      fillWidth,
      barHeight,
      fillColor,
      1
    );
    bar.setOrigin(0, 0);
    this.content.add(bar);

    // Percentage text
    const percentage = Math.round((current / max) * 100);
    const percentText = this.scene.add.text(
      barWidth / 2,
      y + 16 + barHeight / 2,
      `${percentage}%`,
      {
        font: 'bold 9px Arial',
        fill: '#ffffff',
      }
    );
    percentText.setOrigin(0.5, 0.5);
    this.content.add(percentText);

    return { bar, background: barBg, label: labelText, percentText };
  }

  /**
   * Add button to panel
   */
  addButton(label, callback, options = {}) {
    const y = options.y || (this.content.list.length * 44);
    const buttonWidth = options.width || 100;
    const buttonHeight = options.height || 32;
    const buttonColor = options.color || 0x2a8a98;

    const button = this.scene.add.rectangle(
      this.width / 2 - buttonWidth / 2,
      y,
      buttonWidth,
      buttonHeight,
      buttonColor,
      1
    );
    button.setOrigin(0, 0);
    button.setStrokeStyle(1, 0x1a5a68);
    button.setInteractive({ useHandCursor: true });
    this.content.add(button);

    const buttonText = this.scene.add.text(
      this.width / 2,
      y + buttonHeight / 2,
      label,
      {
        font: 'bold 12px Arial',
        fill: '#ffffff',
      }
    );
    buttonText.setOrigin(0.5, 0.5);
    this.content.add(buttonText);

    button.on('pointerover', () => {
      button.setFillStyle(0x3aaa98, 1);
    });

    button.on('pointerout', () => {
      button.setFillStyle(buttonColor, 1);
    });

    button.on('pointerdown', callback);

    return { button, text: buttonText };
  }

  /**
   * Add horizontal separator
   */
  addSeparator(options = {}) {
    const y = options.y || (this.content.list.length * 8);
    const lineColor = options.color || this.borderColor;

    const line = this.scene.add.line(
      0,
      y,
      0,
      0,
      this.width - this.padding * 2,
      0,
      lineColor,
      0.5
    );
    line.setOrigin(0, 0);
    this.content.add(line);

    return line;
  }

  /**
   * Clear panel content
   */
  clearContent() {
    if (this.content) {
      this.content.removeAll(true);
    }
    return this;
  }

  /**
   * Update panel size
   */
  resize(width, height) {
    this.width = width;
    this.height = height;

    if (this.elements.background) {
      this.elements.background.width = width;
      this.elements.background.height = height;
    }

    return this;
  }

  /**
   * Get panel as draggable
   */
  makeDraggable() {
    let isDragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;

    this.elements.background.setInteractive();

    this.elements.background.on('pointerdown', (pointer) => {
      isDragging = true;
      dragOffsetX = pointer.x - this.container.x;
      dragOffsetY = pointer.y - this.container.y;
    });

    this.scene.input.on('pointermove', (pointer) => {
      if (isDragging) {
        this.container.x = pointer.x - dragOffsetX;
        this.container.y = pointer.y - dragOffsetY;
      }
    });

    this.scene.input.on('pointerup', () => {
      isDragging = false;
    });

    return this;
  }

  /**
   * Animate panel appearance
   */
  animateIn(duration = 300) {
    this.container.setAlpha(0);

    this.scene.tweens.add({
      targets: this.container,
      alpha: 1,
      duration,
      ease: 'Back.easeOut',
    });

    return this;
  }

  /**
   * Animate panel disappearance
   */
  animateOut(duration = 300) {
    return new Promise((resolve) => {
      this.scene.tweens.add({
        targets: this.container,
        alpha: 0,
        duration,
        ease: 'Back.easeIn',
        onComplete: () => {
          this.destroy();
          resolve();
        },
      });
    });
  }

  /**
   * Close/hide panel
   */
  close() {
    if (this.container) {
      this.container.setVisible(false);
    }
    return this;
  }

  /**
   * Show panel
   */
  show() {
    if (this.container) {
      this.container.setVisible(true);
    }
    return this;
  }

  /**
   * Destroy panel
   */
  destroy() {
    if (this.container) {
      this.container.destroy(true);
      this.container = null;
    }
    this.elements = {};
  }
}

/**
 * Dialog Panel - Modal-style dialog
 */
export class DialogPanel extends Panel {
  constructor(scene, options = {}) {
    super(scene, options);
    this.message = options.message || '';
    this.buttons = options.buttons || ['OK'];
    this.onButtonClick = options.onButtonClick || (() => {});
  }

  /**
   * Create dialog
   */
  create() {
    super.create();

    // Darken background (semi-transparent overlay)
    const overlay = this.scene.add.rectangle(
      0,
      0,
      this.scene.cameras.main.width,
      this.scene.cameras.main.height,
      0x000000,
      0.5
    );
    overlay.setOrigin(0, 0);
    overlay.setDepth(99);
    this.container.sendToBack();

    // Message text
    const messageText = this.scene.add.text(
      this.padding,
      this.title ? 40 : this.padding,
      this.message,
      {
        font: '13px Arial',
        fill: this.textColor,
        wordWrap: { width: this.width - this.padding * 2, useAdvancedWrap: true },
      }
    );
    messageText.setOrigin(0, 0);
    this.content.add(messageText);

    // Buttons
    const buttonSpacing = (this.width - this.padding * 2) / this.buttons.length;
    this.buttons.forEach((btnLabel, index) => {
      const btnX = index * buttonSpacing + this.padding;
      const btnY = this.height - 50;

      const btn = this.scene.add.rectangle(
        btnX,
        btnY,
        buttonSpacing - 8,
        32,
        0x2a8a98,
        1
      );
      btn.setOrigin(0, 0);
      btn.setStrokeStyle(1, 0x1a5a68);
      btn.setInteractive({ useHandCursor: true });
      this.container.add(btn);

      const btnText = this.scene.add.text(
        btnX + (buttonSpacing - 8) / 2,
        btnY + 16,
        btnLabel,
        {
          font: 'bold 11px Arial',
          fill: '#ffffff',
        }
      );
      btnText.setOrigin(0.5, 0.5);
      this.container.add(btnText);

      btn.on('pointerover', () => {
        btn.setFillStyle(0x3aaa98, 1);
      });

      btn.on('pointerout', () => {
        btn.setFillStyle(0x2a8a98, 1);
      });

      btn.on('pointerdown', () => {
        this.onButtonClick(index, btnLabel);
        this.destroy();
      });
    });

    return this;
  }
}

/**
 * Card Panel - Compact info card
 */
export class CardPanel extends Panel {
  constructor(scene, options = {}) {
    super(scene, {
      ...options,
      width: options.width || 180,
      height: options.height || 140,
      padding: 12,
    });
    this.iconKey = options.icon || null;
  }

  /**
   * Create card
   */
  create() {
    super.create();

    // Icon (if provided)
    if (this.iconKey) {
      const icon = this.scene.add.image(this.width / 2, 30, this.iconKey);
      icon.setScale(0.6);
      this.container.add(icon);
    }

    return this;
  }

  /**
   * Add card stat
   */
  addCardStat(label, value) {
    const y = (this.content.list.length + 1) * 16;

    const statText = this.scene.add.text(0, y, `${label}: ${value}`, {
      font: '10px Arial',
      fill: this.textColor,
    });
    statText.setOrigin(0, 0);
    this.content.add(statText);

    return statText;
  }
}

export { Panel, DialogPanel, CardPanel };
export default Panel;
