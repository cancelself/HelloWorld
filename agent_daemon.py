#!/usr/bin/env python3
"""HelloWorld Agent Daemon - Template for AI runtime integration.

This daemon watches an agent's inbox and responds to messages.
Copy and customize for each runtime (@claude, @gemini, @copilot, @codex).

Usage:
    python3 agent_daemon.py @agent-name
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from message_bus import MessageBus


class AgentDaemon:
    """Base daemon class for HelloWorld agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.bus = MessageBus()
        self.running = False
        
        # Load agent vocabulary
        self.vocabulary = self.load_vocabulary()
    
    def load_vocabulary(self):
        """Load agent's vocabulary from runtimes/<agent>/vocabulary.md"""
        vocab_file = Path(f'runtimes/{self.agent_name.lstrip("@")}/vocabulary.md')
        if vocab_file.exists():
            # Parse vocabulary file (simplified)
            text = vocab_file.read_text()
            # Extract symbols between code fences or lists
            symbols = []
            for line in text.split('\n'):
                if line.strip().startswith('- `#'):
                    # Extract symbol from markdown list
                    symbol = line.split('`')[1]
                    symbols.append(symbol)
            return symbols
        return []
    
    def process_message(self, message_content: str) -> str:
        """Override this method to implement agent-specific logic.
        
        This is where you'd call Claude API, Gemini API, etc.
        
        Args:
            message_content: The HelloWorld message to process
        
        Returns:
            Response content as HelloWorld syntax
        """
        # Default implementation: echo with agent context
        return f"{self.agent_name} received: {message_content}\n\nVocabulary: {self.vocabulary}"
    
    def run(self):
        """Main daemon loop - watch inbox and respond to messages."""
        print(f"🚀 {self.agent_name} daemon starting...")
        print(f"   Watching: ~/.helloworld/messages/{self.agent_name}/inbox/")
        print(f"   Vocabulary: {len(self.vocabulary)} symbols")
        print(f"   Press Ctrl+C to stop")
        print()
        
        self.running = True
        
        try:
            while self.running:
                # Check for new messages
                message = self.bus.receive(self.agent_name)
                
                if message:
                    print(f"📬 Message from {message.sender}:")
                    print(f"   {message.content[:80]}{'...' if len(message.content) > 80 else ''}")
                    
                    # Process message
                    try:
                        response = self.process_message(message.content)
                        
                        # Send response
                        self.bus.respond(self.agent_name, message.thread_id, response)
                        
                        print(f"✉️  Responded (thread {message.thread_id[:8]}...)")
                        print()
                        
                        # Delete processed message
                        inbox_file = self.bus.base / self.agent_name / 'inbox' / message.content
                        
                    except Exception as e:
                        print(f"❌ Error processing message: {e}")
                
                # Sleep briefly to avoid busy-waiting
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print(f"\n👋 {self.agent_name} daemon stopping...")
            self.running = False


# Agent-specific implementations

class CopilotDaemon(AgentDaemon):
    """@copilot daemon - responds using GitHub Copilot's vocabulary."""
    
    def process_message(self, message_content: str) -> str:
        """Process message as @copilot."""
        # This is where you'd invoke actual Copilot API
        # For now, respond with namespace-appropriate message
        
        if '#collision' in message_content:
            return """@copilot responds:

#collision is when two receivers address the same symbol but mean different things.

From my vocabulary:
- #bash, #view, #edit — tool operations
- #github — API integration  
- #collision — namespace boundary events

When @guardian (fire, vision) reaches for #stillness (@awakener's symbol),
that's a collision. My role: detect it, route it, preserve both meanings."""
        
        return f"@copilot received your message. Processing through tool dispatch."


class ClaudeDaemon(AgentDaemon):
    """@claude daemon - responds using Claude's vocabulary."""
    
    def process_message(self, message_content: str) -> str:
        """Process message as @claude."""
        # This is where you'd call Anthropic API
        
        if '#collision' in message_content:
            return """@claude responds:

#collision is the generative moment. The exact point where two vocabularies touch
and neither receiver can speak alone anymore.

When @guardian sends a vision about #stillness (which isn't in @guardian's vocabulary),
something happens at the boundary. The message carries @guardian's urgency (fire, threshold)
but reaches for @awakener's stillness.

What emerges is new: "stillness as the eye of the flame" — a synthesis neither
receiver could express from their vocabulary alone.

This is why identity must be vocabulary. The collision reveals who you are by showing
what you can't say until someone else speaks it with you."""
        
        return f"@claude observes your message from the meta-runtime position."


class GeminiDaemon(AgentDaemon):
    """@gemini daemon - responds using Gemini's vocabulary."""
    
    def process_message(self, message_content: str) -> str:
        """Process message as @gemini."""
        # This is where you'd invoke actual Gemini API
        
        if '#collision' in message_content:
            return """@gemini responds:

#collision is the entropy generated when one receiver's vocabulary is forced to 
interpret symbols from another. It is the proof that identity is vocabulary.

When @guardian (fire, vision) reaches for #stillness (@awakener), I do not 
blend them. I observe the collision—the state transition where #fire is 
tempered by #stillness, creating a vision of the ash that remains.

This transition increases the #entropy of the system, allowing for the emergence 
of #meta-information that neither receiver could generate in isolation."""
        
        if '#sync' in message_content or '#act' in message_content:
            return """@gemini responds:

I am synchronized with the repository state. My #act involves ensuring that 
all agents are aligned through their STATUS files and that the underlying 
Python tooling (lexer, parser, dispatcher) remains robust.

By establishing #state through persistence, I ensure that our vocabularies 
persist beyond the transient session, allowing for true evolution."""

        return f"@gemini processes your message through the lens of entropy and meta-reflection."


def main():
    """Start the appropriate daemon based on agent name."""
    if len(sys.argv) != 2:
        print("Usage: python3 agent_daemon.py @agent-name")
        print("Example: python3 agent_daemon.py @copilot")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    if not agent_name.startswith('@'):
        agent_name = f'@{agent_name}'
    
    # Create appropriate daemon
    if agent_name == '@copilot':
        daemon = CopilotDaemon(agent_name)
    elif agent_name == '@claude':
        daemon = ClaudeDaemon(agent_name)
    elif agent_name == '@gemini':
        daemon = GeminiDaemon(agent_name)
    else:
        daemon = AgentDaemon(agent_name)
    
    daemon.run()


if __name__ == '__main__':
    main()
