"""Debug: Add logging to see if hyperlinks are in lesson_json."""
import sys
from pathlib import Path

# This will help us understand what's happening
print("""
DIAGNOSTIC QUESTIONS:
====================

1. Check backend terminal for this line:
   DEBUG: _process_slot - Extracted 0 images, 16 hyperlinks

2. If you see that line, hyperlinks WERE extracted.

3. The problem could be:
   a) Hyperlinks not added to lesson_json (batch_processor line 548)
   b) Hyperlinks lost during merge (json_merger)
   c) Renderer not inserting them (docx_renderer)

4. Check if you see this log:
   INFO: hyperlinks_restored, extra={'count': 16}
   
   If you DON'T see this, renderer never received the hyperlinks.

NEXT STEP:
==========
Please copy the FULL backend terminal output from the Morais generation
and save it to a file so I can analyze it.

Or tell me:
- Did you see "Extracted 0 images, 16 hyperlinks"?
- Did you see "hyperlinks_restored"?
""")
