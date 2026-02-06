import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

class PM2Manager:
    """Manages Node.js processes via PM2"""
    
    def __init__(self, config=None):
        self.config = config

    def _run_pm2(self, args: List[str]) -> Dict:
        """Run a PM2 command and return result"""
        try:
            cmd = ['pm2'] + args + ['--json']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            try:
                # PM2 returns valid JSON on stdout usually
                if result.stdout.strip():
                     return {'success': result.returncode == 0, 'data': json.loads(result.stdout), 'error': result.stderr}
                return {'success': result.returncode == 0, 'data': None, 'error': result.stderr}
            except json.JSONDecodeError:
                return {'success': False, 'data': None, 'error': f"Invalid JSON: {result.stdout}"}
        except FileNotFoundError:
             return {'success': False, 'error': "PM2 not found. Install it with 'npm install -g pm2'"}

    def list_processes(self) -> List[Dict]:
        """List all PM2 processes"""
        result = self._run_pm2(['jlist']) # jlist is faster/cleaner json
        if result['success'] and result['data']:
             return result['data']
        return []

    def start_process(self, site_name: str, script_path: str, port: int, interpreter: str = 'node', cwd: str = None) -> Dict:
        """Start a new process with PM2"""
        # We assume the name is the site name unique ID
        
        args = [
            'start', script_path,
            '--name', site_name,
            '--port', str(port), # Pass port as environment variable
            '--time' # Add timestamp to logs
        ]
        
        if cwd:
             args.extend(['--cwd', cwd])
        
        if interpreter != 'node':
             args.extend(['--interpreter', interpreter])
             
        # Environment variables injection
        # Note: PM2 doesn't take --port as a flag for the app usually, 
        # but we can set PORT env var which most apps respect
        
        # We need to construct the command differently to pass env vars:
        # pm2 start app.js --name "myapp" -- --port 3000 (arguments passed to script)
        # OR env var PORT=3000 pm2 start ... 
        
        # Best approach: Use ecosystem config logic or environment update
        # But simpler for CLI:
        # pm2 start "npm run start" --name "my-site" --update-env
        
        # Let's try to run specifically setting the environment variable
        cmd = ['pm2', 'start', script_path, '--name', site_name]
        
        # If it's an npm script (e.g. "npm run start"), script_path should be "npm" and args "run start"
        # But for simplicity let's assume we are running the entry file directly OR using npm
        
        return self._run_pm2(args)
        
    def stop_process(self, site_name: str) -> Dict:
        return self._run_pm2(['stop', site_name])

    def restart_process(self, site_name: str) -> Dict:
        return self._run_pm2(['restart', site_name])

    def delete_process(self, site_name: str) -> Dict:
        return self._run_pm2(['delete', site_name])

    def save(self) -> Dict:
        """Freeze current process list for respawn"""
        return self._run_pm2(['save'])
