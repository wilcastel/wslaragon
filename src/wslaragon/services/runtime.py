"""Central lifecycle management for the local development environment."""

import os
import subprocess
from typing import Dict, List

from ..core.config import Config
from ..core.services import ServiceManager
from .mysql import MySQLManager
from .node.pm2 import PM2Manager


class RuntimeManager:
    """Start, stop and inspect all WSLaragon runtime components."""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.services = ServiceManager(self.config)
        self.mysql = MySQLManager(self.config)
        self.pm2 = PM2Manager(self.config)

    def start(self) -> Dict:
        results = []
        results.append(self._systemd_action('php-fpm', 'start'))
        results.append(self._mysql_action('start'))
        results.append(self._optional_systemd_action('redis', 'start'))
        results.append(self._systemd_action('nginx', 'start'))

        dump_file = self.config.home_dir / '.pm2' / 'dump.pm2'
        if dump_file.exists():
            pm2_result = self.pm2.resurrect()
            results.append(self._result('pm2', pm2_result.get('success', False),
                                        pm2_result.get('error')))
        else:
            results.append(self._result('pm2', True, 'No saved processes', skipped=True))
        return self._summary(results)

    def stop(self) -> Dict:
        results = []
        # Kill PM2 first so proxied applications stop accepting new work.
        if self._pm2_daemon_running():
            pm2_result = self.pm2.kill()
            results.append(self._result('pm2', pm2_result.get('success', False),
                                        pm2_result.get('error')))
        else:
            results.append(self._result('pm2', True, 'Already stopped', skipped=True))
        results.append(self._systemd_action('nginx', 'disable', now=True))
        results.append(self._systemd_action('php-fpm', 'disable', now=True))
        results.append(self._optional_systemd_action('redis', 'disable', now=True))
        results.append(self._mysql_action('stop'))
        return self._summary(results)

    def status(self) -> Dict:
        system_status = self.services.status()
        pm2_running = self._pm2_daemon_running()
        processes = self.pm2.list_processes() if pm2_running else []
        components = [
            self._result('nginx', system_status['nginx']['running']),
            self._result('php-fpm', system_status['php-fpm']['running']),
            self._result('mysql', self.mysql.is_running()),
            self._result('redis', system_status['redis']['running']),
            self._result('pm2', pm2_running and any(
                proc.get('pm2_env', {}).get('status') == 'online' for proc in processes
            ), f"{len(processes)} registered process(es)"),
        ]
        return {'running': all(item['running'] for item in components[:3]),
                'components': components}

    def _systemd_action(self, component: str, action: str, now: bool = False) -> Dict:
        service = self.services.services[component]['service']
        command = ['sudo', 'systemctl', action]
        if now:
            command.append('--now')
        command.append(service)
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            return self._result(component, False, 'Timed out after 30 seconds')
        error = result.stderr.strip() if result.returncode else None
        return self._result(component, result.returncode == 0, error)

    def _optional_systemd_action(self, component: str, action: str,
                                 now: bool = False) -> Dict:
        service = self.services.services[component]['service']
        exists = subprocess.run(
            ['systemctl', 'cat', service], capture_output=True, text=True
        ).returncode == 0
        if not exists:
            return self._result(component, True, 'Not installed', skipped=True)
        return self._systemd_action(component, action, now=now)

    def _mysql_action(self, action: str) -> Dict:
        running = self.mysql.is_running()
        if action == 'start' and running:
            return self._result('mysql', True, 'Already running', skipped=True)
        if action == 'stop' and not running:
            return self._result('mysql', True, 'Already stopped', skipped=True)
        success = getattr(self.mysql, action)()
        return self._result('mysql', success, None if success else 'Lifecycle command failed')

    def _pm2_daemon_running(self) -> bool:
        pid_file = self.config.home_dir / '.pm2' / 'pm2.pid'
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def _result(component: str, success: bool, detail: str = None,
                skipped: bool = False) -> Dict:
        return {'component': component, 'success': success, 'running': success,
                'detail': detail, 'skipped': skipped}

    @staticmethod
    def _summary(results: List[Dict]) -> Dict:
        return {'success': all(item['success'] for item in results), 'components': results}
