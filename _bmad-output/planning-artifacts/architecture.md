---
stepsCompleted: [step-01-init, step-02-context, step-03-starter, step-04-decisions, step-05-patterns, step-06-structure, step-07-validation, step-08-complete]
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-03-05'
inputDocuments: [_bmad-output/planning-artifacts/prd.md]
workflowType: 'architecture'
project_name: 'Geo-Dash'
user_name: 'Milan'
date: '2026-03-04'
---

# Architecture Decision Document

_Ce document se construit collaborativement étape par étape. Les sections sont ajoutées au fil des décisions architecturales._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Phase 1 (10 FRs) couvre le jeu jouable complet : rendu tuilé, caméra scrolling,
éditeur persistant, parser .gmd, physique cube-mode, et VFX polished.
Phase 2 (9 FRs) couvre le système évolutionnaire : neurones/réseaux/cerveaux,
simulation 1 000 agents, sélection top-10, mutation gaussienne, stats + replay.

**Non-Functional Requirements:**
- Performance critique : 1 000 agents ≥ 60 sim-steps/s (NFR-01)
- Rendu 60 FPS stable (NFR-02)
- Physics déterministe à 240 Hz timestep fixe (NFR-05)
- Persistance JSON niveaux + cerveaux (NFR-03/04)
- Zero dépendance externe hors pygame (NFR-06)
- Séparation modulaire engine/editor/ai/renderer (NFR-07)
- Portabilité Python 3.10+ macOS/Windows/Linux (NFR-08)

**Scale & Complexity:**
- Primary domain: Desktop Python application, mono-machine
- Complexity level: Medium
- Composants architecturaux estimés: 7 modules

### Technical Constraints & Dependencies

- Python 3.10+ / Pygame 2.x (stack non négociable)
- Format .gmd : gzip-compressed, base64url-encoded — parser custom requis
- Deux espaces de coordonnées coexistants : blocs flottants (physique) et pixels (rendu)
- Pas de réseau, pas de multiprocessing requis, pas d'audio

### Cross-Cutting Concerns Identified

1. Conversion de coordonnées blocs ↔ pixels — doit être centralisée
2. Boucle temporelle à timestep fixe — partagée entre jeu humain et sim IA
3. Sérialisation JSON — deux schémas séparés (niveaux / cerveaux)
4. Toggle rendu IA — couche visuelle découplable de la simulation

---

## Starter Template Evaluation

### Primary Technology Domain

Application desktop Python (Pygame) — greenfield, mono-machine, pas de cloud.
Aucun starter CLI standardisé n'existe pour ce domaine.
Structure de projet définie manuellement selon les contraintes NFR-07.

### Starter Options Considered

| Option | Verdict |
|---|---|
| `pygame-ce` template | Non standardisé, trop minimal |
| Cookiecutter pygame | Abandonné, non maintenu |
| Structure manuelle | ✅ Retenu — contrôle total, complexité maîtrisée |

### Structure Projet Retenue

**Initialization Command:**
```bash
mkdir geo-dash && cd geo-dash
python -m venv .venv && source .venv/bin/activate
pip install pygame==2.6.*
```

**Arborescence cible :**
```
geo-dash/
├── main.py                  # Point d'entrée, game loop
├── engine/
│   ├── physics.py           # Constantes physique, timestep 240 Hz
│   ├── world.py             # Grille, Level, tile types
│   ├── player.py            # État joueur, collision
│   ├── gd_objects.py        # SOLID_IDS, SPIKE_IDS, parser .gmd
│   └── camera.py            # Scrolling camera
├── renderer/
│   ├── game_renderer.py     # Rendu jeu (tiles, joueur, VFX)
│   ├── editor_renderer.py   # Rendu éditeur
│   └── vfx.py               # Glow, particules, traînée
├── editor/
│   ├── editor.py            # Logique éditeur, placement tiles
│   └── level_io.py          # Save/load JSON
├── ai/
│   ├── neuron.py            # Neurone (position, type, polarity)
│   ├── network.py           # Réseau de neurones
│   ├── brain.py             # Cerveau = liste de réseaux
│   ├── evolution.py         # Sélection top-10, mutation gaussienne
│   └── simulation.py        # Boucle simulation 1 000 agents
├── ui/
│   ├── hud.py               # Stats génération, overlay
│   └── menu.py              # Menus principaux
├── data/
│   ├── levels/              # .gmd sources + .json internes
│   └── brains/              # gen_001.json … gen_100.json
└── tests/
    └── test_physics.py      # Tests déterminisme, constantes
```

**Architectural Decisions Provided by Structure:**

- **Language & Runtime:** Python 3.10+, annotations de type recommandées
- **Séparation simulation/rendu:** `simulation.py` n'importe jamais `pygame` — testable sans GPU
- **Persistance:** JSON pur pour niveaux et cerveaux — zéro dépendance DB
- **Testing:** `pytest` sur la couche `engine/` et `ai/` uniquement (headless)
- **Dev workflow:** `python main.py` — pas de build step

---

## Core Architectural Decisions

### Decision Priority Analysis

**Décisions critiques (bloquent l'implémentation) :**
- Système de coordonnées : conversion centralisée dans `World`
- Gestion des scènes : pattern State
- Schémas JSON figés : niveaux + cerveaux
- Simulation IA : NumPy vectorisé

**Décisions importantes (façonnent l'architecture) :**
- Game loop 240 Hz / 60 FPS avec interpolation (RD-02 PRD)
- VFX découplé dans `renderer/vfx.py`

**Décisions différées (post-MVP) :**
- Multiprocessing (hors scope NFR-01 atteint via NumPy)
- Profiling détaillé de la boucle rendu

---

### Catégorie 1 — Game Loop & Timestep

**Décision :** Timestep physique fixe 240 Hz + rendu 60 FPS avec interpolation.

**Rationale :** Issu de RD-02 du PRD. Déterminisme total requis pour la simulation IA × 1 000 agents.

```python
# main.py — boucle canonique
accumulator += delta_time
while accumulator >= DT:          # DT = 1/240
    physics_step(DT)
    accumulator -= DT
render(interpolation=accumulator / DT)
```

**Constantes** (engine/physics.py) :
```python
PHYSICS_RATE   = 240
DT             = 1.0 / 240
GRAVITY        = -0.958          # blocs/frame
JUMP_VELOCITY  = +12.36          # blocs/frame
PLAYER_SPEED   = 10.3761348998   # blocs/s
BLOCK_SIZE_PX  = 30              # px/bloc
```

---

### Catégorie 2 — Système de coordonnées

**Décision :** La classe `World` (engine/world.py) est propriétaire de toutes les conversions blocs ↔ pixels.

**Rationale :** Un seul point de modification si `BLOCK_SIZE_PX` change. Les modules `engine/` et `ai/` travaillent exclusivement en blocs flottants ; la conversion vers pixels n'a lieu qu'à la frontière renderer.

```python
# engine/world.py
class World:
    BLOCK_SIZE_PX: int = 30

    @staticmethod
    def to_px(bloc: float) -> int:
        return int(bloc * World.BLOCK_SIZE_PX)

    @staticmethod
    def to_bloc(px: int) -> float:
        return px / World.BLOCK_SIZE_PX

    def tile_at(self, bx: float, by: float) -> TileType:
        """Retourne le type de tuile à la position en blocs."""
        ...
```

**Règle de codage :** Tout argument nommé `x`, `y`, `dx`, `dy` dans `engine/` et `ai/` est en **blocs**. Tout argument dans `renderer/` est en **pixels**.

---

### Catégorie 3 — Gestion des scènes

**Décision :** Pattern State — chaque scène est un objet avec interface commune ; `main.py` délègue sans if/else.

**Rationale :** Extensible proprement, chaque scène testable indépendamment, transitions explicites.

```python
# ui/scene.py
from abc import ABC, abstractmethod
import pygame

class Scene(ABC):
    @abstractmethod
    def handle_events(self, events: list[pygame.event.Event]) -> "Scene | None":
        """Retourne la scène suivante, ou None pour conserver la scène actuelle."""

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...

# main.py
scene: Scene = MenuScene()
while running:
    events = pygame.event.get()
    next_scene = scene.handle_events(events)
    if next_scene:
        scene = next_scene
    scene.update(dt)
    scene.draw(screen)
```

**Scènes définies :**
| Classe | Module | Description |
|---|---|---|
| `MenuScene` | `ui/menu.py` | Écran titre + sélection |
| `PlayScene` | `engine/` | Jeu humain |
| `EditorScene` | `editor/editor.py` | Éditeur de niveau |
| `AITrainScene` | `ai/simulation.py` | Entraînement IA |
| `ReplayScene` | `ai/simulation.py` | Replay meilleur agent |

---

### Catégorie 4 — Schémas JSON

**Décision :** Deux schémas JSON versionnés, figés avant l'implémentation.

#### Schéma Niveau (data/levels/*.json)
```json
{
  "version": 1,
  "name": "My Level",
  "tiles": [
    { "x": 3, "y": 0, "type": "solid" },
    { "x": 7, "y": 0, "type": "spike" }
  ]
}
```
- `x`, `y` : position en **blocs** (entiers)
- `type` : `"solid"` | `"spike"` | `"air"` (air jamais stocké explicitement)

#### Schéma Cerveau (data/brains/gen_NNN.json)
```json
{
  "version": 1,
  "generation": 42,
  "fitness": 61.3,
  "networks": [
    {
      "neurons": [
        { "dx": 2.5, "dy": -1.0, "type": "spike", "polarity": "green" },
        { "dx": 1.0, "dy":  0.0, "type": "solid", "polarity": "red"  }
      ]
    }
  ]
}
```
- `dx`, `dy` : offset en **blocs flottants** relatif au joueur (positif = droite/haut)
- `type` : `"solid"` | `"spike"` | `"air"`
- `polarity` : `"green"` (ON si tuile correspond) | `"red"` (ON si tuile ne correspond PAS)
- Fichier nommé `gen_001.json` … `gen_100.json`

---

### Catégorie 5 — Simulation IA vectorisée (NumPy)

**Décision :** Option B — NumPy vectorisé. `numpy` est une dépendance explicite du projet.

**Rationale :** 1 000 agents × ~67 blocs = ~1,6 M steps/génération en Python pur ≈ 90–120 s sur laptop standard — NFR-01 (< 60 s) n'est pas tenu sans vectorisation. NumPy permet des opérations batch sur les 1 000 positions/vitesses simultanément.

**Impact sur NFR-06 :** `pip install pygame numpy` — deux dépendances seulement, toujours minimal.

```python
# ai/simulation.py — structure vectorisée
import numpy as np

class PopulationSim:
    def __init__(self, brains: list[Brain], level: World):
        self.n = len(brains)                      # 1 000
        self.x   = np.zeros(self.n)               # positions X (blocs)
        self.y   = np.zeros(self.n)
        self.vy  = np.zeros(self.n)               # vitesse verticale
        self.alive = np.ones(self.n, dtype=bool)
        self.brains = brains
        self.level = level

    def step(self, dt: float) -> None:
        # Gravité vectorisée
        self.vy[self.alive] += GRAVITY
        self.y[self.alive]  += self.vy[self.alive] * dt
        self.x[self.alive]  += PLAYER_SPEED * dt

        # Collision sol & mort (vectorisé par tile lookup)
        self._resolve_collisions()

        # Évaluation neurones + saut (boucle Python sur 1 000 cerveaux)
        for i in np.where(self.alive)[0]:
            if self.brains[i].should_jump(self.x[i], self.y[i], self.level):
                self.vy[i] = JUMP_VELOCITY

    def fitness(self) -> np.ndarray:
        return self.x.copy()  # distance = fitness
```

**Note :** La résolution de collision et le lookup de tuiles restent en Python natif dans un premier temps ; NumPy est utilisé pour les opérations arithmétiques sur positions/vitesses.

---

### Catégorie 6 — Architecture VFX

**Décision :** `VFXSystem` entièrement dans `renderer/vfx.py` ; `Player` n'expose que son état de données.

**Rationale :** La logique de simulation (physique, collision) ne dépend jamais de Pygame. `simulation.py` peut tourner headless sans importer `pygame`.

```python
# renderer/vfx.py
class VFXSystem:
    def __init__(self):
        self.particles: list[Particle] = []
        self.trail: deque[tuple[float, float]] = deque(maxlen=30)

    def on_land(self, px: int, py: int) -> None:
        """Déclenche un burst de particules au contact sol."""
        ...

    def update(self, player_state: PlayerState, dt: float) -> None:
        """PlayerState = dataclass pure (x, y, vy, on_ground, angle)."""
        self.trail.appendleft((player_state.x, player_state.y))
        self._update_particles(dt)

    def draw(self, surface: pygame.Surface, camera_offset: int) -> None:
        self._draw_trail(surface, camera_offset)
        self._draw_glow(surface, camera_offset)
        self._draw_particles(surface, camera_offset)
```

```python
# engine/player.py
from dataclasses import dataclass

@dataclass
class PlayerState:
    """État pur du joueur — aucune dépendance Pygame."""
    x: float; y: float; vy: float
    on_ground: bool; angle: float
```

---

### Decision Impact Analysis

**Séquence d'implémentation induite :**
1. `engine/physics.py` — constantes + `PlayerState`
2. `engine/world.py` — `World`, conversion, `tile_at()`
3. `engine/player.py` + collision
4. `renderer/game_renderer.py` + `renderer/vfx.py`
5. `editor/` + `engine/gd_objects.py`
6. `ui/scene.py` + scènes
7. `ai/` — neuron → network → brain → evolution → simulation NumPy

**Dépendances croisées :**
- `ai/simulation.py` importe `engine/world.py` et `engine/physics.py` **uniquement**
- `renderer/` importe `engine/` et `ai/brain.py` (pour replay neurones) mais jamais `ai/simulation.py`
- `editor/` importe `engine/world.py` et `engine/gd_objects.py`

---

## Implementation Patterns & Consistency Rules

### Points de conflit identifiés : 6 catégories

### Naming Patterns

**Python — conventions générales :**
- `snake_case` : variables, fonctions, modules, noms de fichiers
- `PascalCase` : classes uniquement
- `UPPER_SNAKE_CASE` : constantes (regroupées dans `engine/physics.py`)
- Pas de préfixe `I` pour les classes abstraites (ABC Python natif)

**Coordonnées dans les signatures :**
- Arguments en blocs → `x, y, dx, dy, bx, by`
- Arguments en pixels → `px_x, px_y` (ou suffixe `_px`)
- Jamais de mélange blocs/pixels dans la même fonction

**Types de tuiles :**
- `TileType(Enum): AIR, SOLID, SPIKE` dans `engine/world.py`
- Jamais de strings nues `"solid"` dans le code Python (uniquement dans les fichiers JSON de persistance)

### Structure Patterns

**Tests :**
- `tests/` à la racine — pas de co-location `.test.py`
- Un fichier de test par module : `test_physics.py`, `test_world.py`, `test_brain.py`, `test_evolution.py`
- Les tests headless n'importent **jamais** `pygame`

**Règles d'import (strictes) :**

| Module | Peut importer | Ne peut PAS importer |
|---|---|---|
| `engine/` | stdlib, `numpy` | `renderer/`, `ai/`, `pygame` |
| `ai/` | `engine/`, `numpy` | `renderer/`, `pygame` |
| `renderer/` | `engine/`, `ai/brain.py`, `pygame` | `ai/simulation.py` |
| `editor/` | `engine/`, `pygame` | `ai/`, `renderer/` |
| `ui/` | tous sauf `ai/simulation.py` directement | — |

### Format Patterns

**JSON :**
- Champs en `snake_case`
- Champ `"version": 1` obligatoire dans chaque fichier JSON racine
- Coordonnées en **blocs flottants** (`float`) — jamais en pixels

**Logging :**
- `logger = logging.getLogger(__name__)` dans chaque module
- Objets `.gmd` inconnus → `logger.debug()` — jamais `print()`
- Erreurs de parsing → `logger.warning()` + comportement gracieux (pas de crash)

### Process Patterns

**Résolution de collision :**
- Toujours après le déplacement, avant le rendu
- Produit un `PlayerState` corrigé — pas de side-effect caché

**Mort du joueur / agent IA :**
- `alive: bool` sur tout objet joueur ou agent
- Mort → `alive = False`, position gelée
- Jamais de `del` ou retrait de liste en cours de boucle de simulation

**Simulation IA — pureté fonctionnelle :**
- `Brain.should_jump(x, y, level) -> bool` : fonction **pure**, sans état interne
- La boucle de simulation ne modifie **jamais** `level` (lecture seule)

### Enforcement Guidelines

**Tout agent d'implémentation DOIT :**
- Respecter les règles d'import inter-modules ci-dessus
- Utiliser `TileType` (enum) — jamais de strings de tuile nues
- Travailler en blocs dans `engine/` et `ai/`, convertir en pixels uniquement dans `renderer/`
- Écrire les tests sans importer `pygame`
- Logger via `logging` — jamais via `print()`

---

## Project Structure & Boundaries

### Structure complète du projet

```
geo-dash/
├── main.py                      # Point d'entrée — instancie et lance la game loop
├── requirements.txt             # pygame==2.6.*, numpy>=1.26
├── README.md
├── .gitignore
│
├── engine/                      # Logique pure : zéro pygame, zéro numpy direct
│   ├── __init__.py
│   ├── physics.py               # Constantes PHYSICS_RATE, DT, GRAVITY, JUMP_VELOCITY,
│   │                            #   PLAYER_SPEED, BLOCK_SIZE_PX + PlayerState dataclass
│   ├── world.py                 # TileType(Enum), World (grille), to_px(), to_bloc(),
│   │                            #   tile_at(bx, by)
│   ├── player.py                # Logique joueur humain : move(), resolve_collision()
│   ├── gd_objects.py            # SOLID_IDS, SPIKE_IDS, PORTAL_IDS,
│   │                            #   NON_CUBE_PORTAL_IDS, parse_gmd(), truncate_to_cube()
│   └── camera.py                # Camera(x_offset) — suit le joueur en X
│
├── renderer/                    # Tout ce qui touche à pygame.Surface
│   ├── __init__.py
│   ├── game_renderer.py         # Rendu tuiles, joueur, HUD
│   ├── editor_renderer.py       # Rendu grille éditeur, curseur, toolbar
│   └── vfx.py                   # VFXSystem : glow, particules, traînée, sky gradient
│
├── editor/                      # Éditeur de niveaux
│   ├── __init__.py
│   ├── editor.py                # Logique placement/suppression tuiles, gestion caméra
│   └── level_io.py              # save_level(path, world), load_level(path) → World
│
├── ai/                          # Système évolutionnaire — zéro pygame
│   ├── __init__.py
│   ├── neuron.py                # Neuron(dx, dy, type, polarity) + is_active(x,y,level)
│   ├── network.py               # Network(neurons[]) + should_fire(x,y,level)
│   ├── brain.py                 # Brain(networks[]) + should_jump(x,y,level) → bool
│   │                            #   + to_json() / from_json()
│   ├── evolution.py             # select_top_n(), mutate(brain) — gauss N(0,1²)
│   └── simulation.py            # PopulationSim (NumPy vectorisé) — boucle génération
│
├── ui/                          # Scènes et menus
│   ├── __init__.py
│   ├── scene.py                 # ABC Scene(handle_events, update, draw)
│   ├── menu.py                  # MenuScene
│   ├── play_scene.py            # PlayScene (jeu humain)
│   ├── editor_scene.py          # EditorScene
│   ├── ai_train_scene.py        # AITrainScene (lance PopulationSim + stats)
│   ├── replay_scene.py          # ReplayScene (rejoue best brain d'une génération)
│   └── hud.py                   # Widgets stats génération, overlay debug
│
├── data/
│   ├── levels/
│   │   ├── How2.gmd             # Niveau source GD (66 objets)
│   │   ├── Nine Circles.gmd     # Niveau source GD (14 894 objets)
│   │   └── *.json               # Niveaux éditeur sauvegardés
│   └── brains/
│       └── gen_001.json … gen_100.json
│
└── tests/
    ├── __init__.py
    ├── test_physics.py          # Constantes, timestep, déterminisme
    ├── test_world.py            # to_px, to_bloc, tile_at, TileType
    ├── test_gd_objects.py       # Parser .gmd, truncation cube section
    ├── test_brain.py            # Brain.should_jump, sérialisation JSON
    └── test_evolution.py        # Mutation gaussienne, select_top_n
```

### Frontières architecturales

**Frontière engine ↔ renderer :**
- `engine/` expose uniquement des dataclasses pures (`PlayerState`, `World`, `TileType`)
- `renderer/` consomme ces dataclasses et produit des `pygame.Surface` — jamais l'inverse

**Frontière engine ↔ ai :**
- `ai/` lit `World.tile_at()` et les constantes de `physics.py`
- `ai/simulation.py` retourne uniquement un `np.ndarray` de fitness — pas d'état global

**Frontière simulation ↔ visualisation IA :**
- `AITrainScene` orchestre `PopulationSim` et appelle `renderer/game_renderer.py` optionnellement
- Le toggle `V` (debug) active/désactive le rendu sans affecter la simulation

**Frontière éditeur ↔ jeu :**
- `level_io.py` est le seul point de sérialisation/désérialisation des niveaux
- `EditorScene` et `PlayScene` travaillent sur la même instance `World`

### Mapping FRs → Fichiers

| FR | Fichier(s) principal(aux) |
|---|---|
| FR-P1-01 Tile Grid Renderer | `engine/world.py`, `renderer/game_renderer.py` |
| FR-P1-02 Scrolling Camera | `engine/camera.py` |
| FR-P1-03 Level Editor | `editor/editor.py`, `ui/editor_scene.py`, `renderer/editor_renderer.py` |
| FR-P1-04 .gmd Parser | `engine/gd_objects.py` |
| FR-P1-05 Player Movement | `engine/player.py`, `engine/physics.py` |
| FR-P1-06 Gravity & Jump | `engine/player.py`, `engine/physics.py` |
| FR-P1-07 Collision Detection | `engine/player.py`, `engine/world.py` |
| FR-P1-08 Player Appearance + Rotation | `renderer/game_renderer.py` |
| FR-P1-09 VFX (glow, particules, traînée, sky) | `renderer/vfx.py`, `renderer/game_renderer.py` |
| FR-P1-10 Spikes | `engine/world.py` (TileType.SPIKE), `renderer/game_renderer.py` |
| FR-P2-01 Neuron | `ai/neuron.py` |
| FR-P2-02 Network | `ai/network.py` |
| FR-P2-03 Brain | `ai/brain.py` |
| FR-P2-04 Parallel Simulation | `ai/simulation.py` |
| FR-P2-05 Fitness | `ai/simulation.py` (fitness()) |
| FR-P2-06 Selection & Mutation | `ai/evolution.py` |
| FR-P2-07 Generation Loop | `ui/ai_train_scene.py` + `ai/simulation.py` |
| FR-P2-08 Generation Stats UI | `ui/hud.py`, `ui/ai_train_scene.py` |
| FR-P2-09 Best Agent Replay | `ui/replay_scene.py`, `ai/brain.py` |

### Points d'intégration

**Flux jeu humain :**
```
main.py → PlayScene → engine/player.py + engine/world.py
                    → renderer/game_renderer.py + renderer/vfx.py
```

**Flux entraînement IA :**
```
main.py → AITrainScene → ai/simulation.py (PopulationSim, NumPy)
                       → ai/evolution.py (select_top_n, mutate)
                       → data/brains/gen_NNN.json
                       → ui/hud.py (stats overlay)
```

**Flux éditeur :**
```
main.py → EditorScene → editor/editor.py → engine/world.py
                      → editor/level_io.py → data/levels/*.json
                      → renderer/editor_renderer.py
```

---

## Architecture Validation Results

### Cohérence ✅

**Compatibilité des décisions :**
- Python 3.10+ / Pygame 2.x / NumPy 1.26+ : aucun conflit de versions ✅
- Timestep 240 Hz + NumPy vectorisé : déterminisme préservé ✅
- Pattern State + ABC Scene : Python natif, zéro framework externe ✅
- Schémas JSON versionnés : indépendants des types Python internes ✅

**Consistance des patterns :**
- Règles d'import strictes cohérentes avec le toggle rendu IA (RD-05) ✅
- `TileType` enum centralisé — aucune divergence string/enum possible ✅
- Conversion blocs↔pixels uniquement via `World` → `renderer/` ✅

**Alignement structure :**
- Chaque FR a un fichier cible identifié — aucune FR orpheline ✅
- Les 5 scènes couvrent tous les user journeys du PRD ✅

### Couverture des exigences ✅

**19 FRs — toutes couvertes** (mapping complet section Structure) ✅

| NFR | Couverture architecturale | Statut |
|---|---|---|
| NFR-01 — 1 000 agents ≥ 60 sim-steps/s | NumPy vectorisé dans `simulation.py` | ✅ |
| NFR-02 — 60 FPS rendu | Boucle `accumulator` + interpolation `main.py` | ✅ |
| NFR-03/04 — Persistance JSON | `level_io.py` + `brain.to_json()/from_json()` | ✅ |
| NFR-05 — Physics 240 Hz déterministe | `DT = 1/240`, constantes `physics.py` | ✅ |
| NFR-06 — Dépendances minimales | `pygame` + `numpy` — 2 dépendances seulement | ✅¹ |
| NFR-07 — Séparation modulaire | Structure `engine/`, `editor/`, `ai/`, `renderer/` | ✅ |
| NFR-08 — Python 3.10+ multiplateforme | Aucun code platform-specific identifié | ✅ |
| NFR-09 — Inconnus .gmd loggés | `logger.debug()` dans `gd_objects.py` | ✅ |

> ¹ NFR-06 stipulait "zéro dépendance hors pygame" ; NumPy ajouté consciemment (décision Catégorie 5) pour tenir NFR-01. `requirements.txt` : `pygame==2.6.*, numpy>=1.26`.

### Gaps identifiés

| Priorité | Gap | Action |
|---|---|---|
| Majeur | NFR-06 vs NumPy : exception à documenter | Mentionner dans README — non bloquant |
| Mineur | Clock pygame / FPS cap dans `main.py` non spécifié | Traiter dans la story `main.py` |
| Mineur | Convention nommage brains : `gen_001_best.json` | Déjà dans schéma Catégorie 4 |

### Architecture Completeness Checklist

- [x] Analyse du contexte projet
- [x] Complexité et domaine évalués
- [x] Contraintes techniques identifiées
- [x] Décisions critiques documentées avec justification
- [x] Stack technique complète spécifiée
- [x] Patterns de nommage établis
- [x] Patterns de structure définis
- [x] Patterns de process documentés
- [x] Structure de répertoire complète
- [x] Frontières des composants établies
- [x] Points d'intégration mappés
- [x] Mapping FRs → fichiers complet

### Architecture Readiness Assessment

**Statut global : PRÊT POUR L'IMPLÉMENTATION ✅**

**Niveau de confiance : Élevé**

**Points forts :**
- Séparation simulation/rendu totale → tests headless fiables
- Schémas JSON versionnés → migrations évitées
- Règles d'import strictes → conflits inter-modules impossibles
- NumPy vectorisé → NFR-01 tenu sans multiprocessing

**Améliorations futures possibles :**
- Multiprocessing si NumPy seul s'avère insuffisant
- Profiling rendu si 60 FPS instable sur machines lentes
- Versioning automatisé des schémas JSON si évolution future

### Implementation Handoff

**Tout agent d'implémentation doit :**
- Lire ce document avant de toucher au code
- Respecter les règles d'import inter-modules (section Patterns)
- Utiliser `TileType` — jamais de strings de tuile nues
- Travailler en blocs dans `engine/` et `ai/`
- Ne jamais importer `pygame` dans `engine/` ou `ai/`

**Ordre d'implémentation recommandé :**
```
1. engine/physics.py   — constantes + PlayerState
2. engine/world.py     — TileType, World, conversions
3. engine/player.py    — physique + collision
4. renderer/           — rendu + VFX
5. editor/             — éditeur + level_io
6. ui/scene.py + scènes
7. ai/                 — neuron → network → brain → evolution → simulation
```

**Commande d'initialisation :**
```bash
mkdir geo-dash && cd geo-dash
python -m venv .venv && source .venv/bin/activate
pip install "pygame==2.6.*" "numpy>=1.26"
```

---

*Architecture générée par Winston (Architect Agent) — BMAD Method v6.0.4 — 2026-03-05*
