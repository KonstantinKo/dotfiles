"""Exercise the BSD tail fallback without GNU tac on PATH."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StatuslineTests(unittest.TestCase):
    def test_latest_usage_with_bsd_tail_fallback(self):
        if not shutil.which('jq'):
            self.skipTest('jq is required by the statusline')
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            tools = home / 'tools'
            tools.mkdir()
            for name in ['cat', 'jq', 'grep', 'awk']:
                (tools / name).symlink_to(shutil.which(name))
            # Emulate BSD tail -r so the same fallback is exercised on Linux CI.
            tail = tools / 'tail'
            tail.write_text('''#!/bin/sh
[ "$1" = -r ] || exit 2
shift
exec /usr/bin/awk '{line[NR]=$0} END {for(i=NR;i>0;i--)print line[i]}' "$@"
''')
            tail.chmod(0o755)
            transcript = home / 'session.jsonl'
            transcript.write_text('\n'.join(json.dumps(row) for row in [
                {'usage': {'input_tokens': 1000}},
                {'message': {'usage': {'input_tokens': 12000, 'cache_read_input_tokens': 3000}}},
                {'type': 'other'},
            ]))
            env = dict(os.environ, HOME=tmp, PATH=str(tools))
            result = subprocess.run(['/bin/bash', str(ROOT / 'agents/shared/claude/statusline.sh')],
                                    input=json.dumps({'transcript_path': str(transcript)}),
                                    env=env, capture_output=True, text=True, check=True)
            self.assertIn('15.0k/200k', result.stdout)
            self.assertNotIn('1.0k/', result.stdout)
            self.assertEqual(result.stderr, '')
