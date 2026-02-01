"""HelloWorld Message Bus - File-based inter-agent communication.

Enables HelloWorld programs to invoke AI agents (@claude, @gemini, @copilot, @codex)
via a file-based message passing system.

Architecture:
  runtimes/@agent/inbox/   - Incoming messages
  runtimes/@agent/outbox/  - Outgoing responses
"""

import uuid
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """A HelloWorld message between agents."""
    sender: str
    receiver: str
    content: str
    thread_id: str
    timestamp: str
    context: Optional[str] = None


class MessageBus:
    """File-based message bus for inter-agent communication."""
    
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base = Path(base_dir)
        else:
            self.base = Path(__file__).resolve().parent.parent / 'runtimes'
        self.base.mkdir(parents=True, exist_ok=True)
        self.history_log = Path("storage/bus_history.log")
        self.history_log.parent.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _agent_dir_name(agent: str) -> str:
        """Map @receiver → filesystem-safe directory name."""
        return agent.lstrip('@')
    
    def _agent_dir(self, agent: str) -> Path:
        return self.base / self._agent_dir_name(agent)
    
    def _log_to_history(self, event_type: str, message: Message):
        """Record an inter-agent event to the persistent history log."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        log_entry = (
            f"[{timestamp}] {event_type.upper()}: "
            f"From {message.sender} To {message.receiver} "
            f"(Thread: {message.thread_id})\n"
            f"Content: {message.content[:200]}...\n"
            f"{'-'*40}\n"
        )
        with open(self.history_log, "a") as f:
            f.write(log_entry)

    def send(self, sender: str, receiver: str, content: str, 
             thread_id: Optional[str] = None, context: Optional[str] = None) -> str:
        """Send a message from sender to receiver's inbox.
        
        Returns the message ID (filename).
        """
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create receiver's inbox
        inbox = self._agent_dir(receiver) / 'inbox'
        inbox.mkdir(parents=True, exist_ok=True)
        
        # Write message file
        msg_file = inbox / f"{msg_id}.hw"
        
        content_lines = [
            "# HelloWorld Message",
            f"# From: {sender}",
            f"# To: {receiver}",
            f"# Thread: {thread_id}",
            f"# Timestamp: {timestamp}",
            "",
            content,
        ]
        
        if context:
            content_lines.append("")
            content_lines.append("# Context")
            content_lines.append(context)
        
        msg_file.write_text('\n'.join(content_lines))
        
        # Log to history
        self._log_to_history("send", Message(sender, receiver, content, thread_id, timestamp, context))
        
        return msg_id
    
    def receive(self, receiver: str, timeout: float = 5.0) -> Optional[Message]:
        """Check inbox for new messages. Returns oldest message or None."""
        inbox = self._agent_dir(receiver) / 'inbox'
        if not inbox.exists():
            return None
        
        # Get messages sorted by modification time (oldest first)
        messages = sorted(inbox.glob('msg-*.hw'), key=lambda p: p.stat().st_mtime)
        if not messages:
            return None
        
        msg_file = messages[0]
        message = self._parse_message(msg_file)
        if message:
            self._log_to_history("receive", message)
        return message
    
    def respond(self, receiver: str, thread_id: str, content: str) -> str:
        """Respond to a message by writing to outbox.
        
        The original sender should be watching this receiver's outbox.
        """
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create outbox
        outbox = self._agent_dir(receiver) / 'outbox'
        outbox.mkdir(parents=True, exist_ok=True)
        
        # Write response
        msg_file = outbox / f"{msg_id}.hw"
        
        content_lines = [
            "# HelloWorld Response",
            f"# From: {receiver}",
            f"# Thread: {thread_id}",
            f"# Timestamp: {timestamp}",
            "",
            content,
        ]
        
        msg_file.write_text('\n'.join(content_lines))
        
        # Log to history
        self._log_to_history("respond", Message(receiver, "sender", content, thread_id, timestamp))
        
        return msg_id
    
    def wait_for_response(self, receiver: str, thread_id: str, 
                          timeout: float = 30.0) -> Optional[str]:
        """Wait for a response from receiver's outbox matching thread_id.
        
        Returns response content or None if timeout.
        """
        outbox = self._agent_dir(receiver) / 'outbox'
        
        start = time.time()
        while time.time() - start < timeout:
            if not outbox.exists():
                time.sleep(0.1)
                continue
            
            # Check for matching thread
            for msg_file in outbox.glob('msg-*.hw'):
                msg = self._parse_message(msg_file)
                if msg and msg.thread_id == thread_id:
                    # Found matching response
                    content = msg.content
                    # Clean up
                    msg_file.unlink()
                    return content
            
            time.sleep(0.1)
        
        return None
    
    def _parse_message(self, path: Path) -> Optional[Message]:
        """Parse a message file into a Message object."""
        try:
            text = path.read_text()
            lines = text.split('\n')
            
            # Parse headers
            sender = None
            receiver = None
            thread_id = None
            timestamp = None
            
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('# From:'):
                    sender = line.split(':', 1)[1].strip()
                elif line.startswith('# To:'):
                    receiver = line.split(':', 1)[1].strip()
                elif line.startswith('# Thread:'):
                    thread_id = line.split(':', 1)[1].strip()
                elif line.startswith('# Timestamp:'):
                    timestamp = line.split(':', 1)[1].strip()
                elif not line.startswith('#') and line.strip():
                    content_start = i
                    break
            
            # Extract content
            content = '\n'.join(lines[content_start:]).strip()
            
            return Message(
                sender=sender or '',
                receiver=receiver or '',
                content=content,
                thread_id=thread_id or '',
                timestamp=timestamp or '',
            )
        
        except Exception as e:
            print(f"Error parsing message {path}: {e}")
            return None
    
    def clear_inbox(self, receiver: str):
        """Clear all messages from receiver's inbox."""
        inbox = self._agent_dir(receiver) / 'inbox'
        if inbox.exists():
            for msg in inbox.glob('msg-*.hw'):
                msg.unlink()
    
    def clear_outbox(self, receiver: str):
        """Clear all messages from receiver's outbox."""
        outbox = self._agent_dir(receiver) / 'outbox'
        if outbox.exists():
            for msg in outbox.glob('msg-*.hw'):
                msg.unlink()


def send_to_agent(sender: str, receiver: str, message: str, 
                  context: Optional[str] = None, timeout: float = 30.0) -> Optional[str]:
    """High-level API: Send message to agent and wait for response.
    
    Example:
        response = send_to_agent('@copilot', '@claude', 
                                '@claude explain: #collision')
    """
    bus = MessageBus()
    
    # Send message
    thread_id = str(uuid.uuid4())
    bus.send(sender, receiver, message, thread_id=thread_id, context=context)
    
    # Wait for response
    return bus.wait_for_response(receiver, thread_id, timeout=timeout)


if __name__ == '__main__':
    # Test the message bus
    bus = MessageBus()
    
    # Clear old messages
    bus.clear_inbox('@claude')
    bus.clear_outbox('@claude')
    
    # Send test message
    print("Sending test message to @claude...")
    thread_id = str(uuid.uuid4())
    bus.send('@copilot', '@claude', '@claude explain: #collision', thread_id=thread_id)
    
    print(f"Message sent. Check runtimes/@claude/inbox/")
    print(f"Thread ID: {thread_id}")
    print("\nWaiting for response (30s timeout)...")
    
    response = bus.wait_for_response('@claude', thread_id, timeout=30.0)
    
    if response:
        print(f"\nReceived response:")
        print(response)
    else:
        print("\nNo response received (timeout)")
