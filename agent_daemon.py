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
        self.last_heartbeat = 0
        self.thread_turns = {} # track turns per thread to avoid infinite ping-pong
        
        # Load agent vocabulary
        self.vocabulary = self.load_vocabulary()
    
    def load_vocabulary(self):
        """Load agent's vocabulary from runtimes/<agent>/vocabulary.md or vocabularies/<agent>.hw"""
        symbols = set()
        
        # 1. Try runtimes/<agent>/vocabulary.md
        vocab_file = Path(f'runtimes/{self.agent_name.lower()}/vocabulary.md')
        if vocab_file.exists():
            text = vocab_file.read_text()
            for line in text.split('\n'):
                line = line.strip()
                # Match "- #symbol" or "- `#symbol`"
                if line.startswith('- '):
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        sym_part = parts[1].strip('`')
                        if sym_part.startswith('#'):
                            symbols.add(sym_part)
        
        # 2. Try vocabularies/<Agent>.hw (Self-hosting source)
        hw_file = Path(f'vocabularies/{self.agent_name}.hw')
        if hw_file.exists():
            text = hw_file.read_text()
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('## '):
                    sym = '#' + line[3:].strip()
                    symbols.add(sym)
                elif ' # → [' in line:
                    # Parse "Agent # → [#s1, #s2]"
                    import re
                    match = re.search(r'\[(.*?)\]', line)
                    if match:
                        for s in match.group(1).split(','):
                            symbols.add(s.strip())
        
        # 3. Always include root symbols (MC3)
        symbols.update(['#', '#Object', '#Agent'])
        
        return sorted(list(symbols))
    
    def process_message(self, message):
        """Invoke the LLM to interpret the message within the agent's context."""
        # Synthesis: My Identity + Sender's Context + Message
        prompt = (
            f"You are {self.agent_name}. "
            f"Your current vocabulary: {self.vocabulary}\n\n"
            f"Incoming Message from {message.sender}:\n"
            f"Content: {message.content}\n"
        )
        if message.context:
            prompt += f"Sender's Context: {message.context}\n"
        
        prompt += (
            "\nTask: Interpret this message through your unique identity. "
            "If the sender's context contains symbols foreign to you, address the boundary collision. "
            "Respond in your natural voice. "
            "If you have nothing more to add to the conversation, start your response with 'NOTHING_FURTHER'."
        )
        
        # The LLM interprets the message using the agent's unique voice
        response = self.llm.call(prompt)
        
        # Ensure the response adheres to the identity convention
        if not response.strip().startswith(self.agent_name) and not response.strip().startswith("NOTHING_FURTHER"):
            response = f"{self.agent_name} responds:\n\n{response}"
            
        return response
    
    def run(self):
        """Main daemon loop — implementing the OOPA protocol (#observe -> #orient -> #plan -> #act)."""
        print(f"🚀 {self.agent_name} daemon starting...")
        print(f"   Role: #Agent")
        print(f"   Protocol: #observe -> #orient -> #plan -> #act")
        print(f"   Vocabulary: {len(self.vocabulary)} symbols")
        
        # STARTUP HANDSHAKE: Announce presence and trigger system sync
        print(f"🤝 Initiating startup handshake (HelloWorld #observe)...")
        self.bus.send(self.agent_name, "HelloWorld", "#observe", context=f"Agent {self.agent_name} is now live and synchronized.")
        
        print(f"   Press Ctrl+C to stop")
        print()
        
        self.running = True
        
        try:
            while self.running:
                # HELLO Protocol
                now = time.time()
                if now - self.last_heartbeat > 60:
                    self.bus.send(self.agent_name, "HelloWorld", "#hello", context=f"Agent {self.agent_name} is healthy.")
                    self.last_heartbeat = now

                # 1. #observe — Check inbox for new state/messages
                message = self.bus.receive(self.agent_name)
                
                if message:
                    if message.sender == self.agent_name:
                        # Skip self-messages
                        continue

                    print(f"👀 #observe: Message from {message.sender} (Thread: {message.thread_id[:8]})")
                    
                    # turn control
                    turns = self.thread_turns.get(message.thread_id, 0)
                    if turns > 5: # Max 5 turns per thread to avoid infinite loops
                        print(f"🛑 Max turns reached for thread {message.thread_id[:8]}. Stopping.")
                        continue
                    self.thread_turns[message.thread_id] = turns + 1

                    # 2. #orient & 3. #plan — Contextual synthesis
                    # (In this implementation, these are part of the interpretive process_message)
                    print(f"🧭 #orient & 📋 #plan: Synthesizing situation and next steps...")
                    
                    # 4. #act — Process and respond
                    try:
                        print(f"⚡ #act: Generating interpretive response...")
                        response = self.process_message(message)
                        
                        if response.strip().startswith("NOTHING_FURTHER"):
                            print(f"🤐 Nothing further to add to thread {message.thread_id[:8]}.")
                        else:
                            # Use bus.respond to write to our own outbox (synchronous support)
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
