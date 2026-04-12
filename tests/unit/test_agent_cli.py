"""Tests for the agent CLI commands module"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestAgentCLI:
    """Test suite for agent CLI commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_agent_deps(self):
        """Mock agent command dependencies"""
        with patch('wslaragon.cli.agent.Config') as mock_config, \
             patch('wslaragon.cli.agent.AgentManager') as mock_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_mgr_instance = MagicMock()
            mock_mgr_instance.get_presets.return_value = {
                'default': {'name': 'Default', 'description': 'Default preset', 'skills': ['skill1', 'skill2']},
                'laravel': {'name': 'Laravel', 'description': 'Laravel preset', 'skills': ['laravel_architect']},
                'wordpress': {'name': 'WordPress', 'description': 'WordPress preset', 'skills': ['wordpress_dev']},
            }
            mock_mgr_instance.init_agent_structure.return_value = {
                'success': True,
                'preset': 'default',
                'path': '/test/path/.agent',
                'skills': ['skill1', 'skill2']
            }
            mock_mgr_instance.install_skill_from_url.return_value = {
                'success': True,
                'name': 'test_skill',
                'path': '/test/.agent/skills/test_skill/SKILL.md'
            }
            mock_mgr.return_value = mock_mgr_instance

            yield {
                'config': mock_config_instance,
                'mgr': mock_mgr,
                'mgr_instance': mock_mgr_instance,
            }


class TestAgentInitCommand(TestAgentCLI):
    """Test suite for agent init command"""

    def test_agent_init_success(self, runner, mock_agent_deps):
        """Test agent init command with default preset"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init'])

        assert result.exit_code == 0
        mock_agent_deps['mgr_instance'].init_agent_structure.assert_called_once_with('.', 'default')

    def test_agent_init_with_preset(self, runner, mock_agent_deps):
        """Test agent init command with specific preset"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init', '--preset', 'laravel'])

        assert result.exit_code == 0
        mock_agent_deps['mgr_instance'].init_agent_structure.assert_called_once_with('.', 'laravel')

    def test_agent_init_with_path(self, runner, mock_agent_deps):
        """Test agent init command with custom path"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init', '--path', '/custom/path'])

        assert result.exit_code == 0
        mock_agent_deps['mgr_instance'].init_agent_structure.assert_called_once_with('/custom/path', 'default')

    def test_agent_init_with_preset_and_path(self, runner, mock_agent_deps):
        """Test agent init command with both preset and path"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init', '--preset', 'wordpress', '--path', '/wp/project'])

        assert result.exit_code == 0
        mock_agent_deps['mgr_instance'].init_agent_structure.assert_called_once_with('/wp/project', 'wordpress')

    def test_agent_init_invalid_preset(self, runner, mock_agent_deps):
        """Test agent init with invalid preset shows error"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init', '--preset', 'nonexistent'])

        assert result.exit_code == 0
        assert "Invalid preset 'nonexistent'" in result.output
        mock_agent_deps['mgr_instance'].init_agent_structure.assert_not_called()

    def test_agent_init_shows_available_presets_on_error(self, runner, mock_agent_deps):
        """Test that invalid preset shows available presets"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init', '--preset', 'invalid'])

        assert "Available:" in result.output
        assert "default" in result.output
        assert "laravel" in result.output

    def test_agent_init_failure_shows_error(self, runner, mock_agent_deps):
        """Test agent init shows error message on failure"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].init_agent_structure.return_value = {
            'success': False,
            'error': 'Permission denied'
        }

        result = runner.invoke(agent, ['init'])

        assert result.exit_code == 0
        assert 'Failed to initialize' in result.output
        assert 'Permission denied' in result.output

    def test_agent_init_shows_success_panel(self, runner, mock_agent_deps):
        """Test agent init shows success panel on success"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init'])

        assert result.exit_code == 0
        assert 'Agent Core Initialized' in result.output
        assert 'Preset: default' in result.output
        assert 'Success' in result.output

    def test_agent_init_shows_skills_tree(self, runner, mock_agent_deps):
        """Test agent init shows skills tree"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init'])

        assert result.exit_code == 0
        assert '.agent/' in result.output
        assert 'skills' in result.output
        assert 'skill1/SKILL.md' in result.output

    def test_agent_init_shows_tree_structure(self, runner, mock_agent_deps):
        """Test agent init shows full tree structure with memory and workflows"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init'])

        assert 'memory' in result.output
        assert 'workflows' in result.output

    def test_agent_init_multiple_skills_in_tree(self, runner, mock_agent_deps):
        """Test that all skills appear in the tree"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].init_agent_structure.return_value = {
            'success': True,
            'preset': 'laravel',
            'path': '/test/.agent',
            'skills': ['laravel_architect', 'test_engineer', 'git_manager']
        }

        result = runner.invoke(agent, ['init', '--preset', 'laravel'])

        assert 'laravel_architect/SKILL.md' in result.output
        assert 'test_engineer/SKILL.md' in result.output
        assert 'git_manager/SKILL.md' in result.output


class TestAgentImportCommand(TestAgentCLI):
    """Test suite for agent import command"""

    def test_agent_import_success(self, runner, mock_agent_deps):
        """Test agent import command with valid URL"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['import', 'https://example.com/skill.md'])

        assert result.exit_code == 0
        mock_agent_deps['mgr_instance'].install_skill_from_url.assert_called_once()

    def test_agent_import_shows_success_panel(self, runner, mock_agent_deps):
        """Test agent import shows success panel"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['import', 'https://example.com/skill.md'])

        assert 'Skill Imported Successfully' in result.output
        assert 'test_skill' in result.output

    def test_agent_import_shows_location(self, runner, mock_agent_deps):
        """Test agent import shows skill location"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].install_skill_from_url.return_value = {
            'success': True,
            'name': 'custom_skill',
            'path': '/custom/.agent/skills/custom_skill/SKILL.md'
        }

        result = runner.invoke(agent, ['import', 'https://example.com/custom.md'])

        assert 'custom_skill' in result.output
        assert '/custom/.agent/skills/custom_skill/SKILL.md' in result.output

    def test_agent_import_failure_shows_error(self, runner, mock_agent_deps):
        """Test agent import shows error message on failure"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].install_skill_from_url.return_value = {
            'success': False,
            'error': 'Invalid URL format'
        }

        result = runner.invoke(agent, ['import', 'invalid-url'])

        assert result.exit_code == 0
        assert 'Failed to import skill' in result.output
        assert 'Invalid URL format' in result.output

    def test_agent_import_failure_connection_error(self, runner, mock_agent_deps):
        """Test agent import handles connection errors"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].install_skill_from_url.return_value = {
            'success': False,
            'error': 'Failed to download: Connection refused'
        }

        result = runner.invoke(agent, ['import', 'https://example.com/skill.md'])

        assert 'Failed to import skill' in result.output
        assert 'Connection refused' in result.output

    def test_agent_import_failure_missing_agent_dir(self, runner, mock_agent_deps):
        """Test agent import handles missing .agent directory"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].install_skill_from_url.return_value = {
            'success': False,
            'error': '.agent directory not found. Run "agent init" first.'
        }

        result = runner.invoke(agent, ['import', 'https://example.com/skill.md'])

        assert '.agent directory not found' in result.output

    def test_agent_import_url_is_passed_to_manager(self, runner, mock_agent_deps):
        """Test that URL is passed correctly to AgentManager"""
        from wslaragon.cli.agent import agent

        test_url = 'https://raw.githubusercontent.com/user/repo/main/skills/my-skill.md'
        result = runner.invoke(agent, ['import', test_url])

        called_url = mock_agent_deps['mgr_instance'].install_skill_from_url.call_args[0][0]
        assert called_url == test_url


class TestAgentCommandGroup(TestAgentCLI):
    """Test suite for agent command group"""

    def test_agent_group_has_init_command(self, runner, mock_agent_deps):
        """Test that agent group has init subcommand"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['--help'])

        assert result.exit_code == 0
        assert 'init' in result.output

    def test_agent_group_has_import_command(self, runner, mock_agent_deps):
        """Test that agent group has import subcommand"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['--help'])

        assert result.exit_code == 0
        assert 'import' in result.output

    def test_agent_init_help(self, runner, mock_agent_deps):
        """Test agent init command help"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['init', '--help'])

        assert result.exit_code == 0
        assert '--preset' in result.output
        assert '--path' in result.output
        assert 'default' in result.output

    def test_agent_import_help(self, runner, mock_agent_deps):
        """Test agent import command help"""
        from wslaragon.cli.agent import agent

        result = runner.invoke(agent, ['import', '--help'])

        assert result.exit_code == 0
        assert 'URL' in result.output


class TestAgentInitAllPresets(TestAgentCLI):
    """Test suite for agent init with all valid presets"""

    @pytest.mark.parametrize('preset', ['default', 'laravel', 'wordpress', 'javascript', 'python', 'meta'])
    def test_agent_init_all_presets(self, runner, mock_agent_deps, preset):
        """Test agent init with all valid presets"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].get_presets.return_value = {
            'default': {'name': 'Default', 'description': 'Default', 'skills': ['s1']},
            'laravel': {'name': 'Laravel', 'description': 'Laravel', 'skills': ['s2']},
            'wordpress': {'name': 'WordPress', 'description': 'WordPress', 'skills': ['s3']},
            'javascript': {'name': 'JavaScript', 'description': 'JavaScript', 'skills': ['s4']},
            'python': {'name': 'Python', 'description': 'Python', 'skills': ['s5']},
            'meta': {'name': 'Meta', 'description': 'Meta', 'skills': ['s6']},
        }

        mock_agent_deps['mgr_instance'].init_agent_structure.return_value = {
            'success': True,
            'preset': preset,
            'path': '/test/.agent',
            'skills': ['skill1']
        }

        result = runner.invoke(agent, ['init', '--preset', preset])

        assert result.exit_code == 0


class TestAgentInitEdgeCases(TestAgentCLI):
    """Test suite for agent init edge cases"""

    def test_agent_init_empty_skills_list(self, runner, mock_agent_deps):
        """Test agent init with empty skills list"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].init_agent_structure.return_value = {
            'success': True,
            'preset': 'default',
            'path': '/test/.agent',
            'skills': []
        }

        result = runner.invoke(agent, ['init'])

        assert result.exit_code == 0
        assert '.agent/' in result.output

    def test_agent_init_special_characters_in_path(self, runner, mock_agent_deps):
        """Test agent init with special characters in path"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].init_agent_structure.return_value = {
            'success': True,
            'preset': 'default',
            'path': '/test/path with spaces/.agent',
            'skills': ['skill1']
        }

        result = runner.invoke(agent, ['init', '--path', '/test/path with spaces'])

        assert result.exit_code == 0

    def test_agent_init_unicode_in_error(self, runner, mock_agent_deps):
        """Test agent init handles unicode in error messages"""
        from wslaragon.cli.agent import agent

        mock_agent_deps['mgr_instance'].init_agent_structure.return_value = {
            'success': False,
            'error': 'Error: archivo no encontrado 🚫'
        }

        result = runner.invoke(agent, ['init'])

        assert 'archivo no encontrado' in result.output