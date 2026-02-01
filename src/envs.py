"""HelloWorld Environment Integration - Connects receivers to task environments."""

from typing import Dict, List, Any, Optional

class Environment:
    """Base class for an external world state."""
    def step(self, action: str) -> str:
        raise NotImplementedError
    
    def reset(self) -> str:
        raise NotImplementedError

class ScienceWorldEnv(Environment):
    """Robust ScienceWorld Simulator bridge.
    
    Supports multiple tasks, variations, and structured observations
    mirroring the provided snippets.
    """
    def __init__(self):
        self.state = {
            "task_name": "unknown",
            "variation_idx": 0,
            "task_description": "No task loaded.",
            "observation": "You see nothing.",
            "score": 0,
            "done": False,
            "inventory": []
        }
        # Mock tasks available in the simulator
        self.tasks = {
            "1-1": "boil-water",
            "1-2": "melt-ice",
            "2-1": "identify-living-things"
        }

    def load(self, task_name: str, variation_idx: int = 0):
        """Load a specific task and variation."""
        self.state["task_name"] = task_name
        self.state["variation_idx"] = variation_idx
        if task_name == "boil-water":
            self.state["task_description"] = "Your task is to boil water."
            self.state["observation"] = "You are in the kitchen. You see a stove and a beaker of water."
        else:
            self.state["task_description"] = f"Task: {task_name}"
            self.state["observation"] = "Environment initialized."
        
        self.state["score"] = 0
        self.state["done"] = False
        return self.state["task_description"]

    def step(self, action: str) -> str:
        if self.state["done"]:
            return "Task already completed."

        # Action mapping logic from snippets
        action = action.lower()
        
        # Support for 'load task-name'
        if action.startswith("load"):
            task_name = action.replace("load", "").strip()
            return self.load(task_name)

        if "look" in action:
            return f"[ScienceWorld] {self.state['observation']}"
        if "task" in action:
            return f"[ScienceWorld] {self.state['task_description']}"
        if "inventory" in action:
            return f"[ScienceWorld] Inventory: {' '.join(self.state['inventory']) if self.state['inventory'] else 'empty'}"
        if "heat" in action or "boil" in action:
            if self.state["task_name"] == "boil-water":
                self.state["score"] = 100
                self.state["done"] = True
                self.state["observation"] = "The water is boiling."
                return "[ScienceWorld] You heat the water. It is now boiling. Task complete! Score: 100"
        
        return f"[ScienceWorld] Executed '{action}': No significant change."
    
    def reset(self) -> str:
        self.state["score"] = 0
        self.state["done"] = False
        return "[ScienceWorld] Environment reset."

    def get_goal_progress(self) -> str:
        return f"Goal Progress: {self.state['score']}/100"

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
        self.envs = {
            "scienceworld": ScienceWorldEnv(),
            "#Environment": ScienceWorldEnv(), # Primary mapping
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