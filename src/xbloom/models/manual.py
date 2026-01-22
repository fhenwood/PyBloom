"""
XBloom Manual Recipe - Simple recipe for manual operations.

This is a lightweight alternative to XBloomRecipe for simple operations
like pouring water or grinding beans without the full recipe protocol.
Uses the same PourStep class for consistency.
"""

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
import asyncio

# Reuse existing PourStep for consistency
from xbloom.models.types import PourStep, PourPattern, VibrationPattern

if TYPE_CHECKING:
    from xbloom.core.client import XBloomClient


@dataclass 
class XBloomManualRecipe:
    """
    Simple recipe for manual operations (pour-only, grind-only, or combined).
    
    Unlike XBloomRecipe, this uses direct brewer control instead of the
    complex recipe protocol. Supports multiple pour steps with pauses.
    
    Example:
        # Simple single pour
        recipe = XBloomManualRecipe.pour_only(volume=100, temperature=85)
        
        # Multiple pours with bloom (uses existing PourStep)
        recipe = XBloomManualRecipe(
            pours=[
                PourStep(volume=50, temperature=93, pausing=30),  # Bloom
                PourStep(volume=100, temperature=93, pausing=15),
                PourStep(volume=100, temperature=93),
            ]
        )
        
        # Execute
        await recipe.execute(client)
    """
    # Pour steps (uses existing PourStep class)
    pours: List[PourStep] = field(default_factory=list)
    
    # Grind settings (optional - set to 0 for pour-only)
    grind_size: int = 0             # Grinder setting (1-100), 0 = no grinding
    grind_speed_rpm: int = 80       # Grinder motor speed (60-100)
    
    # Optional metadata
    name: str = "Manual Operation"
    
    @classmethod
    def pour_only(cls, volume: int = 100, temperature: int = 93) -> 'XBloomManualRecipe':
        """Create a single pour recipe (no grinding)."""
        return cls(
            pours=[PourStep(volume=volume, temperature=temperature)],
            grind_size=0,
            name=f"Pour {volume}ml at {temperature}°C"
        )
    
    @classmethod
    def grind_only(cls, grind_size: int = 50, grind_speed_rpm: int = 80) -> 'XBloomManualRecipe':
        """Create a grind-only recipe (no pour)."""
        return cls(
            pours=[],
            grind_size=grind_size,
            grind_speed_rpm=grind_speed_rpm,
            name=f"Grind at size {grind_size}, speed {grind_speed_rpm}"
        )
    
    @property
    def total_volume(self) -> int:
        """Total water volume across all pours (ml)."""
        return sum(p.volume for p in self.pours)
    
    @property
    def has_grinding(self) -> bool:
        """Whether this recipe includes grinding."""
        return self.grind_size > 0
    
    @property
    def has_pours(self) -> bool:
        """Whether this recipe includes water pours."""
        return len(self.pours) > 0
    
    async def execute(self, client: 'XBloomClient') -> float:
        """
        Execute this recipe on the XBloom machine.
        
        Uses direct brewer control (APP_BREWER_START/STOP) instead of the
        recipe protocol. This bypasses sensor checks.
        
        Args:
            client: Connected XBloomClient
            
        Returns:
            Total amount poured (grams from scale)
        """
        initial_weight = client.status.scale.weight
        
        # Step 1: Grinding (if requested)
        if self.has_grinding:
            print(f"⚙️  Grinding at size {self.grind_size}, speed {self.grind_speed_rpm}...")
            await client.scale.move_left()
            await asyncio.sleep(2)
            await client.grinder.start(size=self.grind_size, speed=self.grind_speed_rpm)
            
            # Wait for grinder to finish (monitor status)
            timeout = 120
            start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start < timeout:
                if not client.status.grinder.is_running:
                    break
                await asyncio.sleep(0.5)
            
            await client.grinder.stop()
            print("✓ Grinding complete")
        
        # Step 2: Pouring (if requested)
        if self.has_pours:
            # Move scale to brewer
            print("📍 Moving scale to brewer...")
            await client.scale.move_right()
            await asyncio.sleep(2)
            
            # Execute each pour step
            for i, pour in enumerate(self.pours, 1):
                print(f"💧 Pour {i}/{len(self.pours)}: {pour.volume}ml at {pour.temperature}°C")
                
                # Start pouring with full parameters
                # The machine handles the pour duration based on volume
                await client.brewer.start(
                    volume=pour.volume,
                    temperature=pour.temperature,
                    flow_rate=pour.flow_rate,
                    pattern=pour.pattern.value if hasattr(pour.pattern, 'value') else pour.pattern
                )
                
                # Wait for pour to complete (estimated time + buffer)
                estimated_time = pour.volume / pour.flow_rate
                await asyncio.sleep(estimated_time + 2)  # Add 2s buffer
                
                # Note: Don't call stop() between pours - the machine auto-stops when volume reached
                # Calling stop() puts the machine in a "confirmation required" state
                
                # Pause if specified (uses 'pausing' field)
                if pour.pausing > 0:
                    print(f"   ⏸️  Pausing {pour.pausing}s...")
                    await asyncio.sleep(pour.pausing)
            
            # Stop after all pours complete (safety)
            await client.brewer.stop()
        
        # Calculate total poured
        final_weight = client.status.scale.weight
        total_poured = final_weight - initial_weight
        
        return total_poured
