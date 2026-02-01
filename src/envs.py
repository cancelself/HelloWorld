"""HelloWorld Environment Integration - Connects receivers to task environments."""

from typing import Dict, List, Any, Optional

class Environment:
    """Base class for an external world state."""
    def step(self, action: str) -> str:
        raise NotImplementedError
    
    def reset(self) -> str:
        raise NotImplementedError

class ScienceWorldEnv(Environment):
    def step(self, action: str) -> str:
        # Mock ScienceWorld response
        return f"[ScienceWorld] Executed '{action}': The temperature of the water increased to 100°C. It is now boiling."
    
    def reset(self) -> str:
        return "[ScienceWorld] Environment reset to initial state (Kitchen)."

class AlfWorldEnv(Environment):
    def step(self, action: str) -> str:
        # Mock AlfWorld response
        return f"[AlfWorld] Executed '{action}': You picked up the apple from the counter."
    
    def reset(self) -> str:
        return "[AlfWorld] Environment reset. You are in the middle of a room."

class BabyAIEnv(Environment):
    def step(self, action: str) -> str:
        # Mock BabyAI response
        return f"[BabyAI] Executed '{action}': You moved forward one step toward the red ball."
    
    def reset(self) -> str:
        return "[BabyAI] Environment reset. Level: go to the red ball."

class EnvironmentRegistry:
    def __init__(self):
        self.envs: Dict[str, Environment] = {
            "scienceworld": ScienceWorldEnv(),
            "alfworld": AlfWorldEnv(),
            "babyai": BabyAIEnv()
        }

    def get_env(self, name: str) -> Optional[Environment]:
        return self.envs.get(name.lower())

class EnvironmentReceiver:
    """A HelloWorld receiver that proxies to an environment."""
    def __init__(self, name: str, env_name: str, registry: EnvironmentRegistry):
        self.name = name
        self.env = registry.get_env(env_name)
        # The environment's vocabulary is the set of actions it supports
        self.vocabulary = {"#step", "#look", "#inventory", "#reset", "#env"}

    def handle_message(self, action: str, args: Optional[str] = None) -> str:
        if not self.env:
            return f"Error: Environment for {self.name} not found."
        
        if action == "#reset":
            return self.env.reset()
            
        full_action = f"{action} {args}" if args else action
        observation = self.env.step(full_action)
        return observation