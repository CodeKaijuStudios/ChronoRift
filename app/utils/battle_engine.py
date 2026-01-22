"""
ChronoRift Battle Engine
Turn-based combat system with damage calculation, type advantage, and AI
"""

import random
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.utils.echo_generator import Echo, EchoStats, EchoElement, EchoType


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class BattleState(Enum):
    """Battle lifecycle state"""
    INITIALIZING = "initializing"
    TURN_START = "turn_start"
    ACTION_SELECT = "action_select"
    ACTION_EXECUTING = "action_executing"
    TURN_END = "turn_end"
    FINISHED = "finished"


class ActionType(Enum):
    """Battle action types"""
    ATTACK = "attack"
    DEFEND = "defend"
    ABILITY = "ability"
    SWITCH = "switch"
    ITEM = "item"


# Type effectiveness matrix (attacker -> defender)
TYPE_EFFECTIVENESS = {
    EchoElement.FIRE: {
        EchoElement.FIRE: 0.5,
        EchoElement.WATER: 0.5,
        EchoElement.WIND: 2.0,
        EchoElement.EARTH: 2.0,
        EchoElement.LIGHT: 1.0,
        EchoElement.DARK: 1.0,
        EchoElement.NEUTRAL: 1.0,
    },
    EchoElement.WATER: {
        EchoElement.FIRE: 2.0,
        EchoElement.WATER: 0.5,
        EchoElement.WIND: 0.5,
        EchoElement.EARTH: 2.0,
        EchoElement.LIGHT: 1.0,
        EchoElement.DARK: 1.0,
        EchoElement.NEUTRAL: 1.0,
    },
    EchoElement.WIND: {
        EchoElement.FIRE: 0.5,
        EchoElement.WATER: 2.0,
        EchoElement.WIND: 0.5,
        EchoElement.EARTH: 0.5,
        EchoElement.LIGHT: 1.0,
        EchoElement.DARK: 1.0,
        EchoElement.NEUTRAL: 1.0,
    },
    EchoElement.EARTH: {
        EchoElement.FIRE: 0.5,
        EchoElement.WATER: 0.5,
        EchoElement.WIND: 2.0,
        EchoElement.EARTH: 0.5,
        EchoElement.LIGHT: 1.0,
        EchoElement.DARK: 1.0,
        EchoElement.NEUTRAL: 1.0,
    },
    EchoElement.LIGHT: {
        EchoElement.FIRE: 1.0,
        EchoElement.WATER: 1.0,
        EchoElement.WIND: 1.0,
        EchoElement.EARTH: 1.0,
        EchoElement.LIGHT: 0.5,
        EchoElement.DARK: 2.0,
        EchoElement.NEUTRAL: 1.0,
    },
    EchoElement.DARK: {
        EchoElement.FIRE: 1.0,
        EchoElement.WATER: 1.0,
        EchoElement.WIND: 1.0,
        EchoElement.EARTH: 1.0,
        EchoElement.LIGHT: 2.0,
        EchoElement.DARK: 0.5,
        EchoElement.NEUTRAL: 1.0,
    },
    EchoElement.NEUTRAL: {
        EchoElement.FIRE: 1.0,
        EchoElement.WATER: 1.0,
        EchoElement.WIND: 1.0,
        EchoElement.EARTH: 1.0,
        EchoElement.LIGHT: 1.0,
        EchoElement.DARK: 1.0,
        EchoElement.NEUTRAL: 1.0,
    },
}

# Move type damage scaling
MOVE_TYPE_SCALING = {
    'physical': 'atk',      # Uses attacker ATK vs defender DEF
    'special': 'sp_atk',    # Uses attacker SP_ATK vs defender SP_DEF
    'status': None,         # No direct damage
}

# Critical hit rate (default 5% base)
CRITICAL_HIT_RATE = 0.05
CRITICAL_HIT_MULTIPLIER = 1.5

# Accuracy formula: 100% - (5% * distance_from_100)
ACCURACY_CALCULATION = True


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DamageResult:
    """Damage calculation result"""
    base_damage: int
    type_effectiveness: float
    critical_hit: bool
    final_damage: int
    move_accuracy: float
    hit: bool                  # Whether attack connected


@dataclass
class BattleAction:
    """Action taken in battle"""
    combatant_id: str
    action_type: ActionType
    move_name: str = None
    target_id: str = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CombatantState:
    """Current state of a battler"""
    echo_id: str
    echo: Echo
    current_hp: int
    status_effects: List[str] = field(default_factory=list)
    stat_modifiers: Dict[str, float] = field(default_factory=lambda: {
        'atk': 1.0,
        'def': 1.0,
        'sp_atk': 1.0,
        'sp_def': 1.0,
        'spd': 1.0,
    })
    position: int = 0          # Order in battle (0=first)
    last_action: Optional[BattleAction] = None
    is_defeated: bool = False


@dataclass
class BattleLog:
    """Battle event log"""
    round: int
    timestamp: datetime
    actor_id: str
    action_type: ActionType
    target_id: str
    damage_dealt: int = 0
    healing: int = 0
    status_effect: str = None
    message: str = ""


# ============================================================================
# BATTLE ENGINE
# ============================================================================

class BattleEngine:
    """Core turn-based battle system"""
    
    @staticmethod
    def calculate_damage(
        attacker: Echo,
        defender: Echo,
        move: Dict,
        stat_modifiers_atk: Dict[str, float],
        stat_modifiers_def: Dict[str, float],
    ) -> DamageResult:
        """
        Calculate damage from attack
        
        Formula inspired by Pokémon:
        damage = (2*L/5 + 2) * power * (Atk/Def) * random(0.85-1.0) * type_effectiveness
        
        Args:
            attacker: Attacking Echo
            defender: Defending Echo
            move: Move dictionary with power and accuracy
            stat_modifiers_atk: Attacker stat modifiers
            stat_modifiers_def: Defender stat modifiers
            
        Returns:
            DamageResult: Damage calculation breakdown
        """
        move_type = move.get('type', 'physical')
        move_power = move.get('power', 0)
        accuracy = move.get('accuracy', 100)
        
        # Status moves don't deal direct damage
        if move_type == 'status':
            return DamageResult(
                base_damage=0,
                type_effectiveness=1.0,
                critical_hit=False,
                final_damage=0,
                move_accuracy=accuracy / 100.0,
                hit=True,
            )
        
        # Get relevant stats based on move type
        stat_type = MOVE_TYPE_SCALING[move_type]
        atk_stat = getattr(attacker.current_stats, stat_type)
        
        if stat_type == 'atk':
            def_stat = defender.current_stats.def_
        else:  # sp_atk
            def_stat = defender.current_stats.sp_def
        
        # Apply stat modifiers
        atk_stat = int(atk_stat * stat_modifiers_atk[stat_type])
        def_stat = int(def_stat * stat_modifiers_def['sp_def' if stat_type == 'sp_atk' else 'def'])
        
        # Level scaling factor: (2 * attacker_level / 5 + 2) / 250
        level_factor = (2 * attacker.level / 5 + 2) / 250
        
        # Base damage: level_factor * attack/defense * power
        base_damage = level_factor * (atk_stat / max(1, def_stat)) * move_power + 2
        
        # Type effectiveness
        type_effectiveness = TYPE_EFFECTIVENESS.get(attacker.element, {}).get(
            defender.element, 1.0
        )
        
        # STAB (Same Type Attack Bonus) - 1.5x if move element matches Echo element
        stab = 1.5 if move.get('element') == attacker.element else 1.0
        
        # Critical hit chance (5% base, can be modified by abilities)
        is_critical = random.random() < CRITICAL_HIT_RATE
        critical_mult = CRITICAL_HIT_MULTIPLIER if is_critical else 1.0
        
        # Randomness factor (85-100%)
        randomness = random.uniform(0.85, 1.0)
        
        # Calculate final damage
        final_damage = int(base_damage * type_effectiveness * stab * critical_mult * randomness)
        final_damage = max(1, final_damage)  # Minimum 1 damage
        
        # Check accuracy
        hit_chance = accuracy / 100.0
        hit = random.random() < hit_chance
        
        if not hit:
            final_damage = 0
        
        return DamageResult(
            base_damage=int(base_damage),
            type_effectiveness=type_effectiveness,
            critical_hit=is_critical,
            final_damage=final_damage,
            move_accuracy=hit_chance,
            hit=hit,
        )
    
    
    @staticmethod
    def calculate_turn_order(combatants: List[CombatantState]) -> List[CombatantState]:
        """
        Calculate turn order based on speed stats
        
        Args:
            combatants: List of battlers
            
        Returns:
            List[CombatantState]: Sorted by turn priority (fastest first)
        """
        def get_speed_priority(combatant: CombatantState) -> float:
            # Speed stat with stat modifiers applied
            speed = combatant.echo.current_stats.spd * combatant.stat_modifiers['spd']
            
            # Add small randomness (±5%) to prevent ties
            randomness = random.uniform(0.95, 1.05)
            
            return speed * randomness
        
        # Sort by speed descending (higher speed = earlier turn)
        return sorted(combatants, key=get_speed_priority, reverse=True)
    
    
    @staticmethod
    def apply_status_effect(
        target: CombatantState,
        effect: str,
        duration: int = 3
    ) -> bool:
        """
        Apply status effect to combatant
        
        Args:
            target: Target combatant
            effect: Status effect name (burn, poison, paralyze, etc)
            duration: Number of turns effect lasts
            
        Returns:
            bool: Whether effect was successfully applied
        """
        # Prevent duplicate status effects
        if effect in target.status_effects:
            return False
        
        target.status_effects.append(f"{effect}:{duration}")
        return True
    
    
    @staticmethod
    def update_status_effects(combatant: CombatantState) -> None:
        """
        Update status effect durations and damage
        
        Args:
            combatant: Combatant to update
        """
        active_effects = []
        
        for effect_str in combatant.status_effects:
            effect_name, duration_str = effect_str.split(':')
            duration = int(duration_str) - 1
            
            # Apply effect damage/penalties
            if effect_name == 'burn':
                combatant.current_hp = max(0, combatant.current_hp - int(combatant.echo.base_stats.hp * 0.125))
            elif effect_name == 'poison':
                combatant.current_hp = max(0, combatant.current_hp - int(combatant.echo.base_stats.hp * 0.125))
            elif effect_name == 'paralysis':
                combatant.stat_modifiers['spd'] *= 0.5  # Reduce speed by 50%
            
            # Keep effect if duration remains
            if duration > 0:
                active_effects.append(f"{effect_name}:{duration}")
        
        combatant.status_effects = active_effects
    
    
    @staticmethod
    def modify_stat(
        combatant: CombatantState,
        stat: str,
        stages: int
    ) -> None:
        """
        Modify combatant stat by stages (±1-6)
        
        Args:
            combatant: Target combatant
            stat: Stat name (atk, def, sp_atk, sp_def, spd)
            stages: Number of stages (-6 to +6)
        """
        # Clamp to ±6 stages
        stages = max(-6, min(6, stages))
        
        # Stage to multiplier mapping
        stage_multipliers = {
            -6: 0.25,
            -5: 0.29,
            -4: 0.33,
            -3: 0.43,
            -2: 0.50,
            -1: 0.67,
            0: 1.0,
            1: 1.5,
            2: 2.0,
            3: 2.5,
            4: 3.0,
            5: 3.5,
            6: 4.0,
        }
        
        combatant.stat_modifiers[stat] = stage_multipliers[stages]
    
    
    @staticmethod
    def execute_move(
        attacker: CombatantState,
        defender: CombatantState,
        move: Dict
    ) -> Tuple[int, DamageResult, str]:
        """
        Execute a move in battle
        
        Args:
            attacker: Attacking combatant
            defender: Defending combatant
            move: Move to execute
            
        Returns:
            Tuple of (damage_dealt, damage_result, log_message)
        """
        move_name = move.get('name', 'Unknown Move')
        move_type = move.get('type', 'physical')
        
        # Calculate damage
        damage_result = BattleEngine.calculate_damage(
            attacker.echo,
            defender.echo,
            move,
            attacker.stat_modifiers,
            defender.stat_modifiers
        )
        
        # Build log message
        message = f"{attacker.echo.name} used {move_name}!"
        
        if not damage_result.hit:
            message += " But it missed!"
            return 0, damage_result, message
        
        if damage_result.critical_hit:
            message += " Critical hit!"
        
        # Apply damage
        damage_dealt = damage_result.final_damage
        defender.current_hp = max(0, defender.current_hp - damage_dealt)
        
        # Check for defeat
        if defender.current_hp == 0:
            defender.is_defeated = True
            message += f" {defender.echo.name} has been defeated!"
        
        # Apply type effectiveness message
        if damage_result.type_effectiveness > 1.5:
            message += " It's super effective!"
        elif damage_result.type_effectiveness > 1.0:
            message += " It's effective."
        elif damage_result.type_effectiveness < 0.5:
            message += " It's not very effective..."
        
        # Apply status effect if move has one
        if move.get('effect'):
            if BattleEngine.apply_status_effect(defender, move['effect']):
                message += f" {defender.echo.name} is now {move['effect']}!"
        
        return damage_dealt, damage_result, message
    
    
    @staticmethod
    def ai_choose_move(
        attacker: CombatantState,
        defenders: List[CombatantState]
    ) -> Tuple[Dict, CombatantState]:
        """
        AI logic to choose move and target
        
        Args:
            attacker: AI-controlled combatant
            defenders: List of possible targets
            
        Returns:
            Tuple of (move, target)
        """
        # Filter out defeated defenders
        alive_targets = [d for d in defenders if not d.is_defeated]
        
        if not alive_targets:
            # Should not happen, but failsafe
            return attacker.echo.moves[0], alive_targets[0]
        
        # Choose move: prioritize super-effective moves
        best_move = None
        best_target = None
        best_score = -999
        
        for move in attacker.echo.moves:
            for target in alive_targets:
                # Calculate effectiveness score
                type_eff = TYPE_EFFECTIVENESS.get(attacker.echo.element, {}).get(target.echo.element, 1.0)
                base_power = move.get('power', 20)
                accuracy = move.get('accuracy', 100) / 100.0
                
                # Score: (power * type_effectiveness * accuracy) - (target_hp / max_hp) penalty
                # Damage priority to low-HP targets
                target_hp_ratio = target.current_hp / max(1, target.echo.base_stats.hp)
                score = (base_power * type_eff * accuracy) - (target_hp_ratio * 20)
                
                if score > best_score:
                    best_score = score
                    best_move = move
                    best_target = target
        
        return best_move or attacker.echo.moves[0], best_target or alive_targets[0]
    
    
    @staticmethod
    def is_battle_finished(combatants: List[CombatantState]) -> bool:
        """
        Check if battle is finished (one side defeated)
        
        Args:
            combatants: All combatants in battle
            
        Returns:
            bool: True if battle is over
        """
        # Count defeated per team (assuming team 1 indices 0-1, team 2 indices 2-3)
        team_1_defeated = all(c.is_defeated for c in combatants[:len(combatants)//2])
        team_2_defeated = all(c.is_defeated for c in combatants[len(combatants)//2:])
        
        return team_1_defeated or team_2_defeated


# ============================================================================
# BATTLE UTILITY FUNCTIONS
# ============================================================================

def get_battle_summary(
    winners: List[CombatantState],
    losers: List[CombatantState],
    battle_log: List[BattleLog]
) -> Dict:
    """
    Generate battle summary
    
    Args:
        winners: Winning combatants
        losers: Defeated combatants
        battle_log: Complete battle log
        
    Returns:
        Dict: Battle summary with statistics
    """
    total_rounds = max([log.round for log in battle_log]) if battle_log else 0
    
    return {
        'total_rounds': total_rounds,
        'winners': [w.echo.name for w in winners],
        'losers': [l.echo.name for l in losers],
        'total_actions': len(battle_log),
        'total_damage_dealt': sum(log.damage_dealt for log in battle_log),
        'duration_seconds': (battle_log[-1].timestamp - battle_log[0].timestamp).total_seconds() if battle_log else 0,
    }


def calculate_battle_rewards(
    winner: CombatantState,
    losers: List[CombatantState]
) -> Dict:
    """
    Calculate rewards for battle victory
    
    Args:
        winner: Winning Echo
        losers: Defeated Echoes
        
    Returns:
        Dict: Experience and currency rewards
    """
    base_exp = 100
    base_currency = 50
    
    total_exp = 0
    total_currency = 0
    
    for loser in losers:
        # Experience scales with level difference
        level_diff = loser.echo.level - winner.echo.level
        exp_mult = 1.0 + (level_diff * 0.1)  # 10% per level above
        exp_mult = max(0.5, exp_mult)  # Minimum 50%
        
        exp_gained = int((base_exp + loser.echo.level * 2) * exp_mult)
        currency_gained = int((base_currency + loser.echo.level) * exp_mult)
        
        total_exp += exp_gained
        total_currency += currency_gained
    
    return {
        'experience': total_exp,
        'currency': total_currency,
        'bonus_multiplier': 1.0 + (len(losers) - 1) * 0.1,  # 10% per additional opponent
    }
