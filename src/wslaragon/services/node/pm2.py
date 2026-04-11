"""PM2 process manager for WSLaragon.

Manages Node.js and Python application processes via PM2.
"""
import logging
import os
import subprocess
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PM2Manager:
    """Manages Node.js processes via PM2
    
    Provides methods to start, stop, restart, delete, and list
    PM2-managed processes.
    """
    
    def __init__(self, config=None):
        self.config = config

    def _run_pm2(self, args: List[str], env: Dict[str, str] = None) -> Dict:
        """Run a PM2 command and return result
        
        Args:
            args: List of PM2 command arguments (without 'pm2' prefix)
            env: Optional environment variables to pass to the subprocess
            
        Returns:
            Dict with 'success', 'data', and 'error' keys
        """
        try:
            cmd = ['pm2'] + args + ['--json']
            run_env = os.environ.copy()
            if env:
                run_env.update(env)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=run_env
            )
            
            try:
                # PM2 sometimes returns empty stdout on error
                stdout_stripped = result.stdout.strip()
                if stdout_stripped:
                    data = json.loads(stdout_stripped)
                    return {
                        'success': result.returncode == 0,
                        'data': data,
                        'error': result.stderr if result.returncode != 0 else None
                    }
                return {
                    'success': result.returncode == 0,
                    'data': None,
                    'error': result.stderr
                }
            except json.JSONDecodeError:
                # PM2 sometimes returns non-JSON output for certain commands
                return {
                    'success': result.returncode == 0,
                    'data': None,
                    'error': f"PM2 output: {result.stdout[:200]}"
                }
        except FileNotFoundError:
            logger.error("PM2 not found. Install with 'npm install -g pm2'")
            return {'success': False, 'error': "PM2 not found. Install it with 'npm install -g pm2'"}
        except Exception as e:
            logger.error(f"Error running PM2 command: {e}")
            return {'success': False, 'error': str(e)}

    def list_processes(self) -> List[Dict]:
        """List all PM2 processes
        
        Returns:
            List of process dictionaries from PM2
        """
        result = self._run_pm2(['jlist'])
        if result['success'] and result['data']:
            return result['data']
        return []

    def start_process(self, site_name: str, script_path: str, port: int,
                      interpreter: str = None, cwd: str = None) -> Dict:
        """Start a new process with PM2
        
        Args:
            site_name: Unique name for the process
            script_path: Path to the script to run
            port: Port number (set as PORT env variable)
            interpreter: Optional interpreter (e.g., 'python3')
            cwd: Working directory for the process
            
        Returns:
            Dict with 'success' and error info
        """
        # Build environment with PORT variable
        env = {'PORT': str(port)}
        
        # Build PM2 arguments
        args = ['start', script_path, '--name', site_name]
        
        # Set environment variables via PM2 --env flag
        # PM2 respects PORT env var for most frameworks
        args.extend(['--env', f'PORT={port}'])
        
        if cwd:
            args.extend(['--cwd', cwd])
        
        if interpreter and interpreter != 'node':
            args.extend(['--interpreter', interpreter])
        
        logger.info(f"Starting PM2 process '{site_name}' on port {port}")
        return self._run_pm2(args, env=env)

    def stop_process(self, site_name: str) -> Dict:
        """Stop a PM2 process
        
        Args:
            site_name: Name of the process to stop
            
        Returns:
            Dict with 'success' and error info
        """
        logger.info(f"Stopping PM2 process '{site_name}'")
        return self._run_pm2(['stop', site_name])

    def restart_process(self, site_name: str) -> Dict:
        """Restart a PM2 process
        
        Args:
            site_name: Name of the process to restart
            
        Returns:
            Dict with 'success' and error info
        """
        logger.info(f"Restarting PM2 process '{site_name}'")
        return self._run_pm2(['restart', site_name])

    def delete_process(self, site_name: str) -> Dict:
        """Delete a PM2 process
        
        Args:
            site_name: Name of the process to delete
            
        Returns:
            Dict with 'success' and error info
        """
        logger.info(f"Deleting PM2 process '{site_name}'")
        return self._run_pm2(['delete', site_name])

    def save(self) -> Dict:
        """Save current process list for respawn on restart
        
        Returns:
            Dict with 'success' and error info
        """
        logger.info("Saving PM2 process list")
        return self._run_pm2(['save'])