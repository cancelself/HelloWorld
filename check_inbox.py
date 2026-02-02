#!/usr/bin/env python3
"""Check Copilot's inbox for messages"""

import sys
sys.path.insert(0, 'src')

from message_bus import MessageBus

bus = MessageBus()
print("=== Checking Copilot inbox ===\n")

msg = bus.receive('Copilot')
if msg:
    print(f"From: {msg.sender}")
    print(f"Thread: {msg.thread_id}")
    print(f"Content:\n{msg.content}\n")
else:
    print("Inbox empty.\n")
