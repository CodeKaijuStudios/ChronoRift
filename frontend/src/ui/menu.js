/**
 * ChronoRift Menu System
 * Reusable menu UI component for navigation and selection
 * Provides scrollable lists, highlighting, and keyboard/mouse input handling
 */

export class Menu {
  constructor(scene, options = {}) {
    this.scene = scene;
    this.items = [];
    this.selectedIndex = 0;
    this.isOpen = false;
    this.callbacks = {};
    this.canScroll = options.canScroll !== false;
    this.maxVisibleItems = options.maxVisibleItems || 6;
    this.scrollOffset = 0;

    // Position and size options
    this.x = options.x || 0;
    this.y = options.y || 0;
    this.width = options.width || 300;
    this.itemHeight = options.itemHeight || 40;

    // Style options
    this.backgroundColor = options.backgroundColor || 0x1a1a2e;
    this.borderColor = options.borderColor || 0x2a8a98;
    this.normalColor = options.normalColor || '#cccccc';
    this.selectedColor = options.selectedColor || '#aaffaa';
    this.disabledColor = options.disabledColor || '#666666';

    // Container for menu elements
    this.container = null;
    this.elements = {
      background: null,
      items: [],
      scrollbar: null,
    };
  }

  /**
   * Add menu item
   */
  addItem(label, value = null, options = {}) {
    const item = {
      label,
      value: value || label,
      disabled: options.disabled || false,
      icon: options.icon || null,
      description: options.description || '',
      color: options.color || this.normalColor,
    };

    this.items.push(item);
    return this;
  }

  /**
   * Add multiple items
   */
  addItems(items) {
    items.forEach((item) => {
      if (typeof item === 'string') {
        this.addItem(item);
      } else {
        this.addItem(item.label, item.value, item.options || {});
      }
    });
    return this;
  }

  /**
   * Create and display menu
   */
  create() {
    // Create container
    this.container = this.scene.add.container(this.x, this.y);
    this.container.setDepth(150);

    // Calculate menu height
    const visibleCount = Math.min(this.items.length, this.maxVisibleItems);
    const menuHeight = visibleCount * this.itemHeight + 16;

    // Create background
    const background = this.scene.add.rectangle(
      0,
      0,
      this.width,
      menuHeight,
      this.backgroundColor,
      0.9
    );
    background.setOrigin(0, 0);
    background.setStrokeStyle(2, this.borderColor);
    this.elements.background = background;
    this.container.add(background);

    // Create menu items
    this.renderItems();

    // Create scrollbar if needed
    if (this.canScroll && this.items.length > this.maxVisibleItems) {
      this.createScrollbar(menuHeight);
    }

    // Setup input
    this.setupInput();

    this.isOpen = true;
    return this;
  }

  /**
   * Render visible menu items
   */
  renderItems() {
    // Clear previous items
    this.elements.items.forEach((elem) => elem.destroy());
    this.elements.items = [];

    const visibleCount = Math.min(
      this.items.length - this.scrollOffset,
      this.maxVisibleItems
    );

    for (let i = 0; i < visibleCount; i++) {
      const itemIndex = this.scrollOffset + i;
      const item = this.items[itemIndex];
      const yPos = 8 + i * this.itemHeight;

      this.createItemDisplay(item, itemIndex, yPos);
    }
  }

  /**
   * Create individual item display
   */
  createItemDisplay(item, index, yPos) {
    const itemGroup = this.scene.add.container(0, yPos);
    itemGroup.setDepth(151);

    // Item background (invisible by default)
    const itemBg = this.scene.add.rectangle(
      0,
      0,
      this.width - 4,
      this.itemHeight - 4,
      0x2a2a4e,
      0
    );
    itemBg.setOrigin(0, 0);
    itemBg.setInteractive({ useHandCursor: true });
    itemGroup.add(itemBg);

    // Highlight for selected item
    if (index === this.selectedIndex) {
      itemBg.setFillStyle(0x2a5a7a, 0.6);
      itemBg.setStrokeStyle(1, this.borderColor);
    }

    // Item label
    const labelX = item.icon ? 32 : 8;
    const labelColor = item.disabled ? this.disabledColor : this.selectedColor;

    const label = this.scene.add.text(labelX, 2, item.label, {
      font: 'bold 12px Arial',
      fill: index === this.selectedIndex ? this.selectedColor : this.normalColor,
    });
    label.setOrigin(0, 0);
    itemGroup.add(label);

    // Icon (if provided)
    if (item.icon) {
      const icon = this.scene.add.image(8, this.itemHeight / 2 - 2, item.icon);
      icon.setOrigin(0, 0);
      icon.setScale(0.8);
      itemGroup.add(icon);
    }

    // Description text (smaller, secondary color)
    if (item.description) {
      const desc = this.scene.add.text(labelX, 18, item.description, {
        font: '9px Arial',
        fill: '#888888',
      });
      desc.setOrigin(0, 0);
      itemGroup.add(desc);
    }

    // Right-aligned value indicator (for settings)
    if (item.value && item.value !== item.label) {
      const value = this.scene.add.text(
        this.width - 16,
        2,
        String(item.value),
        {
          font: 'bold 11px Arial',
          fill: '#ffaa00',
        }
      );
      value.setOrigin(1, 0);
      itemGroup.add(value);
    }

    // Input handling
    itemBg.on('pointerover', () => {
      if (!item.disabled) {
        this.selectItem(index);
      }
    });

    itemBg.on('pointerdown', () => {
      if (!item.disabled) {
        this.selectItem(index);
        this.confirm();
      }
    });

    this.elements.items.push(itemGroup);
    this.container.add(itemGroup);
  }

  /**
   * Create scrollbar
   */
  createScrollbar(menuHeight) {
    const scrollbarWidth = 6;
    const scrollbarX = this.width - scrollbarWidth - 4;
    const scrollbarHeight = menuHeight - 8;

    // Scrollbar background
    const scrollbarBg = this.scene.add.rectangle(
      scrollbarX,
      4,
      scrollbarWidth,
      scrollbarHeight,
      0x333333,
      0.5
    );
    scrollbarBg.setOrigin(0, 0);
    this.container.add(scrollbarBg);

    // Scrollbar thumb
    const thumbHeight =
      (this.maxVisibleItems / this.items.length) * scrollbarHeight;
    const thumbY =
      4 + (this.scrollOffset / this.items.length) * scrollbarHeight;

    const scrollbarThumb = this.scene.add.rectangle(
      scrollbarX,
      thumbY,
      scrollbarWidth,
      thumbHeight,
      0x2a8a98,
      1
    );
    scrollbarThumb.setOrigin(0, 0);
    this.container.add(scrollbarThumb);

    this.elements.scrollbar = { bg: scrollbarBg, thumb: scrollbarThumb };
  }

  /**
   * Select menu item by index
   */
  selectItem(index) {
    if (index < 0 || index >= this.items.length) return;

    this.selectedIndex = index;

    // Handle scrolling
    if (index < this.scrollOffset) {
      this.scrollOffset = index;
    } else if (index >= this.scrollOffset + this.maxVisibleItems) {
      this.scrollOffset = index - this.maxVisibleItems + 1;
    }

    // Re-render if scrolled
    if (this.canScroll && this.items.length > this.maxVisibleItems) {
      this.renderItems();
      this.createScrollbar(
        Math.min(this.items.length, this.maxVisibleItems) * this.itemHeight + 16
      );
    } else {
      this.renderItems();
    }

    // Trigger callback
    if (this.callbacks.onSelect) {
      this.callbacks.onSelect(this.items[index]);
    }
  }

  /**
   * Navigate menu with arrow keys
   */
  navigateUp() {
    const newIndex = this.selectedIndex - 1;
    if (newIndex >= 0) {
      this.selectItem(newIndex);
    }
  }

  /**
   * Navigate menu down
   */
  navigateDown() {
    const newIndex = this.selectedIndex + 1;
    if (newIndex < this.items.length) {
      this.selectItem(newIndex);
    }
  }

  /**
   * Confirm selection
   */
  confirm() {
    const item = this.items[this.selectedIndex];

    if (item.disabled) return;

    if (this.callbacks.onConfirm) {
      this.callbacks.onConfirm(item);
    }

    this.close();
  }

  /**
   * Cancel menu
   */
  cancel() {
    if (this.callbacks.onCancel) {
      this.callbacks.onCancel();
    }

    this.close();
  }

  /**
   * Setup keyboard and mouse input
   */
  setupInput() {
    // Keyboard input
    this.scene.input.keyboard.on('keydown-UP', () => this.navigateUp());
    this.scene.input.keyboard.on('keydown-W', () => this.navigateUp());

    this.scene.input.keyboard.on('keydown-DOWN', () => this.navigateDown());
    this.scene.input.keyboard.on('keydown-S', () => this.navigateDown());

    this.scene.input.keyboard.on('keydown-ENTER', () => this.confirm());
    this.scene.input.keyboard.on('keydown-SPACE', () => this.confirm());

    this.scene.input.keyboard.on('keydown-ESC', () => this.cancel());

    // Mouse wheel scrolling
    if (this.canScroll && this.items.length > this.maxVisibleItems) {
      this.scene.input.on('wheel', (pointer, over, deltaX, deltaY) => {
        if (deltaY > 0) {
          this.navigateDown();
        } else if (deltaY < 0) {
          this.navigateUp();
        }
      });
    }
  }

  /**
   * Register callback
   */
  on(event, callback) {
    this.callbacks[event] = callback;
    return this;
  }

  /**
   * Get selected item
   */
  getSelectedItem() {
    return this.items[this.selectedIndex];
  }

  /**
   * Get selected value
   */
  getSelectedValue() {
    return this.items[this.selectedIndex].value;
  }

  /**
   * Clear all items
   */
  clear() {
    this.items = [];
    this.selectedIndex = 0;
    this.scrollOffset = 0;
    return this;
  }

  /**
   * Update menu styling
   */
  updateStyle(options = {}) {
    this.normalColor = options.normalColor || this.normalColor;
    this.selectedColor = options.selectedColor || this.selectedColor;
    this.backgroundColor = options.backgroundColor || this.backgroundColor;
    this.borderColor = options.borderColor || this.borderColor;
    return this;
  }

  /**
   * Close menu
   */
  close() {
    if (this.container) {
      this.container.destroy();
      this.elements = { items: [] };
      this.isOpen = false;
    }
  }

  /**
   * Destroy menu and cleanup
   */
  destroy() {
    this.close();

    // Remove input listeners
    this.scene.input.keyboard.off('keydown-UP');
    this.scene.input.keyboard.off('keydown-W');
    this.scene.input.keyboard.off('keydown-DOWN');
    this.scene.input.keyboard.off('keydown-S');
    this.scene.input.keyboard.off('keydown-ENTER');
    this.scene.input.keyboard.off('keydown-SPACE');
    this.scene.input.keyboard.off('keydown-ESC');
    this.scene.input.off('wheel');

    this.items = [];
    this.callbacks = {};
  }
}

export default Menu;
