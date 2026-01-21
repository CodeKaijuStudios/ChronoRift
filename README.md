# Chronorift

**A Dimensional Echo Collection RPG by Code Kaiju Studios**

Bond with creatures from collapsing timelines. Reshape reality itself.

![Chronorift Logo](https://i.postimg.cc/jDxwsS94/chronorift.png)

---

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Chronorift** is a free-to-play dimensional creature-bonding RPG that blends deep character progression, open-world exploration, and real-time multiplayer events. Players take on the role of **Riftwalkers**—rare individuals capable of bonding with **Echoes**, dimensional creatures leaking through from collapsed alternate timelines.

The game world is fractured by unstable rifts that spawn rare Echoes and reshape the landscape. Player actions directly influence global events: stabilizing rifts, healing corrupted areas, or embracing forbidden power. Faction warfare, guild territory control, and seasonal events create an emergent, ever-changing experience.

**Target Platforms:** Web (primary), Mobile (React Native), Console (future)

**Status:** Early Development | Python/Flask Backend | Production-Ready Architecture

---

## Core Features

### 🎮 Echo Collection & Bonding
- **16 Distinct Echoes** with unique silhouettes, abilities, and dimensional affinities
- **Dynamic Bonding System:** Emotional depth drives mechanical power unlocks
- **Dimensional Abilities:** High-bond Echoes enable reality-warping combat and exploration powers

### 🌍 Open-World Exploration
- **Procedurally-Generated Rifts:** Unstable tears spawn rare Echoes and temporal anomalies
- **Reality Manipulation:** Stabilize/open rifts, plant temporal seeds, construct dimensional anchors
- **Environmental Storytelling:** Discover Echo origins and timeline fragments throughout the world

### ⚔️ Strategic Combat
- **Turn-Based & Real-Time Modes:** Flexible battle systems for different playstyles
- **Team Composition Matters:** Echo synergies reward strategic planning
- **PvP & PvE:** Battle other Riftwalkers or tackle dimensional raids

### 👥 Social & Faction Systems
- **Rift Guilds:** Player-created organizations controlling territory and Echo populations
- **Faction Warfare:** Three competing factions (Harmonists, Singularists, Voidseers) reshape global power dynamics
- **Dynamic Events:** Rare Echo migrations, rift destabilization, and timeline collapses trigger coordinated responses

### 🏠 Sanctuary Management
- **Personal Headquarters:** Customizable sanctuary with Echo storage, training, and passive resource generation
- **World Impact:** Player actions directly alter environmental state and affect other players

### 💰 Emergent Economy
- **NPC-Driven Markets:** Dynamic pricing based on Echo rarity, faction demand, and temporal instability
- **Echo Trading:** Player-to-player trading with faction-specific restrictions
- **Seasonal Currency:** Temporal fragments earned through gameplay unlock exclusive content

---

## Tech Stack

### Backend
- **Framework:** Python 3.11+ with Flask
- **Real-Time Communication:** Flask-SocketIO (WebSockets)
- **Database:** PostgreSQL (primary), Redis (caching, session management)
- **ORM:** SQLAlchemy
- **Authentication:** JWT (JSON Web Tokens)
- **API:** RESTful architecture with WebSocket extensions

### Frontend
- **Rendering Engine:** Phaser.js or Babylon.js (isometric tile-based)
- **UI Framework:** HTML5, CSS3, vanilla JavaScript
- **Real-Time Updates:** Socket.IO client
- **Build Tool:** Webpack

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Web Server:** Nginx (reverse proxy, static serving)
- **Deployment:** AWS EC2, Heroku, or self-hosted VPS
- **CDN:** CloudFlare or similar for asset delivery
- **Monitoring:** New Relic, DataDog, or ELK Stack

### Development Tools
- **Version Control:** Git / GitHub
- **Package Manager:** pip (Python), npm (JavaScript)
- **Testing:** pytest (backend), Jest (frontend)
- **Code Quality:** flake8, black, ESLint
- **CI/CD:** GitHub Actions or GitLab CI

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (recommended)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/CodeKaijuStudios/chronorift.git
cd chronorift
```

#### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys

# Initialize database
flask db upgrade

# Seed initial data (Echoes, Factions, NPCs)
python seed_db.py
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
```

#### 4. Run Locally

**With Docker Compose (Recommended):**

```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`

**Manual Setup:**

Terminal 1 (Backend):
```bash
source venv/bin/activate
flask run --host=0.0.0.0 --port=5000
```

Terminal 2 (Frontend - Development Server):
```bash
cd frontend
npm run dev
```

Terminal 3 (Redis):
```bash
redis-server
```

### First Run

1. Navigate to `http://localhost:5000`
2. Create a new Riftwalker account
3. Complete the onboarding tutorial
4. Begin your dimensional journey

---

## Project Structure

```
chronorift/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration settings
│   ├── models/
│   │   ├── riftwalker.py       # Player character model
│   │   ├── echo.py             # Echo creature model
│   │   ├── world.py            # World state & rifts
│   │   ├── faction.py          # Faction system
│   │   └── transaction.py      # Trading & economy
│   ├── routes/
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── riftwalker.py       # Character management
│   │   ├── echoes.py           # Echo collection & bonding
│   │   ├── world.py            # World state & exploration
│   │   ├── combat.py           # Battle system
│   │   ├── rifts.py            # Rift mechanics
│   │   ├── economy.py          # Trading & currency
│   │   ├── social.py           # Guilds, factions, chat
│   │   └── ws.py               # WebSocket events
│   ├── utils/
│   │   ├── echo_generator.py   # Procedural Echo generation
│   │   ├── rift_generator.py   # Rift spawning logic
│   │   ├── battle_engine.py    # Combat resolution
│   │   ├── bonding_engine.py   # Bonding progression
│   │   └── world_mutator.py    # Environmental changes
│   ├── services/
│   │   ├── auth_service.py     # JWT token management
│   │   ├── event_service.py    # Global event broadcasting
│   │   └── cache_service.py    # Redis caching
│   └── migrations/             # Alembic database migrations
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── main.js             # Entry point
│   │   ├── scenes/
│   │   │   ├── bootScene.js
│   │   │   ├── worldScene.js
│   │   │   ├── combatScene.js
│   │   │   └── sanctuaryScene.js
│   │   ├── ui/
│   │   │   ├── hud.js
│   │   │   ├── menu.js
│   │   │   └── panels.js
│   │   ├── api/
│   │   │   └── client.js       # API & WebSocket client
│   │   └── utils/
│   │       ├── constants.js
│   │       └── helpers.js
│   ├── package.json
│   └── webpack.config.js
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── seed_db.py                   # Database seeding script
```

---

## Development

### Running Tests

```bash
# Backend tests
pytest tests/ -v --cov=app

# Frontend tests
cd frontend && npm test
```

### Code Style

```bash
# Backend formatting
black app/
flake8 app/

# Frontend linting
cd frontend && npm run lint
```

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Add new feature"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

### Adding New Echoes

1. Define Echo properties in `app/utils/echo_generator.py`
2. Create corresponding sprite assets
3. Update `seed_db.py` to include new Echo in database
4. Test Echo spawning and bonding mechanics
5. Deploy and monitor for balance issues

### WebSocket Events

Key real-time events:

```python
# Rift Spawn
emit('rift_spawn', {'location': coords, 'echo_type': 'Vulkrath'})

# Echo Migration
emit('echo_migration', {'from_zone': 'Northern Wastes', 'to_zone': 'Temporal Caverns'})

# Faction Control Change
emit('faction_update', {'zone': 'Metropolis', 'faction': 'Harmonists'})

# Leaderboard Update
emit('leaderboard_update', {'riftwalker_id': 123, 'new_rank': 5})
```

---

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t chronorift:latest .

# Run container
docker run -d \
  -p 5000:80 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/chronorift" \
  -e REDIS_URL="redis://redis:6379/0" \
  chronorift:latest
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chronorift

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# Flask
FLASK_ENV=production
FLASK_DEBUG=False

# CDN & Assets
CDN_URL=https://cdn.example.com
ASSET_BUCKET=s3://chronorift-assets

# Analytics
SENTRY_DSN=your-sentry-dsn
```

### AWS Deployment (Recommended)

```bash
# 1. Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag chronorift:latest <account>.dkr.ecr.us-east-1.amazonaws.com/chronorift:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/chronorift:latest

# 2. Deploy with ECS or EKS
# 3. Configure RDS PostgreSQL and ElastiCache Redis
# 4. Use CloudFront for CDN
# 5. Set up Route53 for DNS
```

### Scaling Considerations

- **Database:** Use read replicas for scaling queries; connection pooling with pgBouncer
- **Cache:** Redis cluster for distributed session management
- **WebSockets:** Multiple Flask instances behind load balancer with sticky sessions
- **Static Assets:** Serve via CDN; optimize image sizes for global distribution
- **Background Jobs:** Use Celery + Redis for async tasks (Echo spawn events, economy calculations)

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature`
3. **Commit changes:** `git commit -m "Add your feature"`
4. **Push to branch:** `git push origin feature/your-feature`
5. **Open a Pull Request**

### Code Guidelines

- Follow PEP 8 for Python; use Black formatter
- Write descriptive commit messages
- Include tests for new features
- Update README and documentation as needed
- Reference issues in commit messages: `Fixes #123`

### Reporting Issues

Found a bug? Please create an issue with:

- Description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Screenshots/logs if applicable
- Your system information (OS, browser, Python version)

---

## Roadmap

### Phase 1 (Q1 2026) – Soft Launch
- Core gameplay loop (Echo collection, bonding, exploration)
- Basic combat system
- Single-player + guild system
- Initial 16 Echo roster

### Phase 2 (Q2 2026) – Expansion
- Faction warfare system
- Seasonal events & battle pass
- Advanced bonding mechanics
- Echo trading marketplace

### Phase 3 (Q3 2026) – Mobile Port
- React Native iOS/Android app
- Cross-platform progression sync
- Mobile-optimized UI

### Phase 4 (Q4 2026) – Console Beta
- Nintendo Switch / PS5 / Xbox port
- Local multiplayer (rifts with friends)
- Console-exclusive cosmetics

---

## License

Chronorift is proprietary software © 2026 Code Kaiju Studios. All rights reserved.

For licensing inquiries or partnerships, contact: [business@codekaiju.com](mailto:business@codekaiju.com)

---

## Support

### Documentation

- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Echo Design Guidelines](docs/echo-design.md)
- [Bonding System Guide](docs/bonding-system.md)

### Community

- **Discord:** [Join our community](https://discord.gg/codekaiju)
- **Twitter:** [@CodeKaijuStudios](https://twitter.com/CodeKaijuStudios)
- **Website:** [codekaiju.com](https://codekaiju.com)

### Contact

- **Support Email:** support@codekaiju.com
- **Business Email:** business@codekaiju.com
- **Bug Reports:** [GitHub Issues](https://github.com/CodeKaijuStudios/chronorift/issues)

---

## Acknowledgments

- **DullNata** – Game Design & Creative Direction
- **Code Kaiju Studios Team** – Development, Art, and Community

---

**Made with 🦖 by Code Kaiju Studios**

*Bond with Echoes. Reshape reality.*
