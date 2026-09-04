"""Tests for centralized runtime lifecycle management."""

from unittest.mock import MagicMock, patch

from wslaragon.services.runtime import RuntimeManager


def make_runtime(tmp_path):
    config = MagicMock()
    config.home_dir = tmp_path
    config.get.side_effect = lambda key, default=None: {
        'platform.name': 'omarchy',
        'php.fpm_service': 'php-fpm',
        'mysql.backend': 'docker',
        'mysql.container': 'mariadb11',
        'mysql.config_file': '/etc/my.cnf',
        'mysql.user': 'root',
        'mysql.password': '',
        'mysql.host': '127.0.0.1',
        'mysql.port': 3306,
    }.get(key, default)
    return RuntimeManager(config)


@patch('wslaragon.services.runtime.subprocess.run')
def test_start_omarchy_runtime(mock_run, tmp_path):
    manager = make_runtime(tmp_path)
    manager.mysql.start = MagicMock(return_value=True)
    manager.mysql.is_running = MagicMock(return_value=False)
    manager.pm2.resurrect = MagicMock(return_value={'success': True})
    (tmp_path / '.pm2').mkdir()
    (tmp_path / '.pm2' / 'dump.pm2').touch()
    mock_run.return_value = MagicMock(returncode=0, stderr='')

    result = manager.start()

    assert result['success'] is True
    assert ['sudo', 'systemctl', 'start', 'php-fpm'] in [
        call.args[0] for call in mock_run.call_args_list
    ]
    assert ['sudo', 'systemctl', 'start', 'nginx'] in [
        call.args[0] for call in mock_run.call_args_list
    ]
    manager.mysql.start.assert_called_once_with()
    manager.pm2.resurrect.assert_called_once_with()


@patch('wslaragon.services.runtime.subprocess.run')
def test_stop_disables_autostart_and_stops_database(mock_run, tmp_path):
    manager = make_runtime(tmp_path)
    manager.mysql.stop = MagicMock(return_value=True)
    manager.mysql.is_running = MagicMock(return_value=True)
    manager.pm2.kill = MagicMock(return_value={'success': True})
    manager._pm2_daemon_running = MagicMock(return_value=True)
    mock_run.return_value = MagicMock(returncode=0, stderr='')

    result = manager.stop()

    assert result['success'] is True
    calls = [call.args[0] for call in mock_run.call_args_list]
    assert ['sudo', 'systemctl', 'disable', '--now', 'nginx'] in calls
    assert ['sudo', 'systemctl', 'disable', '--now', 'php-fpm'] in calls
    manager.mysql.stop.assert_called_once_with()
    manager.pm2.kill.assert_called_once_with()


def test_status_requires_core_components(tmp_path):
    manager = make_runtime(tmp_path)
    manager.services.status = MagicMock(return_value={
        'nginx': {'running': True},
        'php-fpm': {'running': True},
        'mysql': {'running': False},
        'redis': {'running': False},
    })
    manager.mysql.is_running = MagicMock(return_value=True)
    manager.pm2.list_processes = MagicMock(return_value=[])
    manager._pm2_daemon_running = MagicMock(return_value=False)

    result = manager.status()

    assert result['running'] is True
    assert result['components'][3]['component'] == 'redis'
    assert result['components'][3]['running'] is False
    manager.pm2.list_processes.assert_not_called()
