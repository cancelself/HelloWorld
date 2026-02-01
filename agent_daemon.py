#!/usr/bin/env python3
"""HelloWorld Agent Daemon - Real-time interpretive synthesis.

This daemon watches an agent's inbox and responds to messages using
the interpretive LLM runtime (bridged via src/llm.py).

Usage:
    python3 agent_daemon.py AgentName
"""

import sys
import time
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from message_bus import MessageBus
from llm import GeminiModel, get_llm_for_agent


class AgentDaemon:
    """Interpretive daemon for HelloWorld agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.bus = MessageBus()
        self.running = False
        self.llm = get_llm_for_agent(agent_name)
        
        # Load agent vocabulary
        self.vocabulary = self.load_vocabulary()
    
    def load_vocabulary(self):
        """Load agent's vocabulary from runtimes/<agent>/vocabulary.md"""
        vocab_file = Path(f'runtimes/{self.agent_name.lower()}/vocabulary.md')
        if vocab_file.exists():
            text = vocab_file.read_text()
            symbols = []
            for line in text.split('\n'):
                if line.strip().startswith('- `#`'):
                    symbol = line.split('`')[1]
                    symbols.append(symbol)
            return symbols
        return []
    
    def process_message(self, message):
        """Invoke the LLM to interpret the message within the agent's context."""
        prompt = f"Receiver: {self.agent_name}\n"
        if message.context:
            prompt += f"Context: {message.context}\n"
        prompt += f"Message: {message.content}\n"
        
        # The LLM interprets the message using the agent's unique voice
        response = self.llm.call(f"interpret: {prompt}")
        
        # Ensure the response adheres to the identity convention
        if not response.startswith(self.agent_name):
            response = f"{self.agent_name} responds:\n\n{response}"
            
        return response
    
    def run(self):
        """Main daemon loop — implementing the OOPA protocol (#observe -> #orient -> #plan -> #act)."""
        print(f"🚀 {self.agent_name} daemon starting...")
        print(f"   Role: #Agent")
        print(f"   Protocol: #observe -> #orient -> #plan -> #act")
        print(f"   Vocabulary: {len(self.vocabulary)} symbols")
        
        # STARTUP HANDSHAKE: Announce presence and trigger system sync
        print(f"🤝 Initiating startup handshake (@.#observe)...")
        self.bus.send(self.agent_name, "@", "#observe", context=f"Agent {self.agent_name} is now live and synchronized.")
        
        print(f"   Press Ctrl+C to stop")
        print()
        
        self.running = True
        
        try:
            while self.running:
                # 1. #observe — Check inbox for new state/messages
                message = self.bus.receive(self.agent_name)
                
                if message:
                    print(f"👀 #observe: Message from {message.sender} (Thread: {message.thread_id[:8]})")
                    
                    # 2. #orient & 3. #plan — Contextual synthesis
                    # (In this implementation, these are part of the interpretive process_message)
                    print(f"🧭 #orient & 📋 #plan: Synthesizing situation and next steps...")
                    
                    # 4. #act — Process and respond
                    try:
                        print(f"⚡ #act: Generating interpretive response...")
                        response = self.process_message(message)
                        
                        self.bus.respond(self.agent_name, message.thread_id, response)
                        print(f"✉️  Response sent.")
                        print()
                    except Exception as e:
                        print(f"❌ Error during #act: {e}")
                
                # Brief sleep to reduce I/O pressure
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print(f"\n👋 {self.agent_name} daemon stopping...")
            self.running = False


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 agent_daemon.py AgentName")
        sys.exit(1)

    agent_name = sys.argv[1]
    # Capitalize if needed
    if agent_name[0].islower():
        agent_name = agent_name[0].upper() + agent_name[1:]

    daemon = AgentDaemon(agent_name)
    daemon.run()


if __name__ == '__main__':
    main()