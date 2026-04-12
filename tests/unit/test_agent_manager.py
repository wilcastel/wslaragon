"""Tests for the AgentManager module"""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest


class TestAgentManagerInit:
    """Test suite for AgentManager initialization"""

    def test_init_with_config(self):
        """Test AgentManager initializes with config"""
        from wslaragon.services.agent.agent_manager import AgentManager
        
        config = {'test': 'value'}
        manager = AgentManager(config)
        
        assert manager.config == config

    def test_init_with_none_config(self):
        """Test AgentManager initializes with None config"""
        from wslaragon.services.agent.agent_manager import AgentManager
        
        manager = AgentManager(None)
        
        assert manager.config is None


class TestAgentManagerGetPresets:
    """Test suite for get_presets method"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({})

    def test_get_presets_returns_dict(self, manager):
        """Test get_presets returns a dictionary"""
        result = manager.get_presets()
        
        assert isinstance(result, dict)

    def test_get_presets_contains_default(self, manager):
        """Test get_presets contains default preset"""
        result = manager.get_presets()
        
        assert 'default' in result
        assert 'name' in result['default']
        assert 'description' in result['default']
        assert 'skills' in result['default']

    def test_get_presets_default_has_correct_skills(self, manager):
        """Test default preset has expected skills"""
        result = manager.get_presets()
        
        default_skills = result['default']['skills']
        assert 'product_analyst' in default_skills
        assert 'architect' in default_skills
        assert 'git_manager' in default_skills
        assert 'librarian' in default_skills
        assert 'ui_designer' in default_skills

    def test_get_presets_contains_laravel(self, manager):
        """Test get_presets contains laravel preset"""
        result = manager.get_presets()
        
        assert 'laravel' in result
        assert 'laravel_architect' in result['laravel']['skills']
        assert 'test_engineer' in result['laravel']['skills']

    def test_get_presets_contains_wordpress(self, manager):
        """Test get_presets contains wordpress preset"""
        result = manager.get_presets()
        
        assert 'wordpress' in result
        assert 'wordpress_developer' in result['wordpress']['skills']
        assert 'theme_designer' in result['wordpress']['skills']

    def test_get_presets_contains_javascript(self, manager):
        """Test get_presets contains javascript preset"""
        result = manager.get_presets()
        
        assert 'javascript' in result
        assert 'frontend_architect' in result['javascript']['skills']
        assert 'node_specialist' in result['javascript']['skills']

    def test_get_presets_contains_python(self, manager):
        """Test get_presets contains python preset"""
        result = manager.get_presets()
        
        assert 'python' in result
        assert 'python_expert' in result['python']['skills']
        assert 'data_engineer' in result['python']['skills']

    def test_get_presets_contains_meta(self, manager):
        """Test get_presets contains meta preset"""
        result = manager.get_presets()
        
        assert 'meta' in result
        assert 'skill_creator' in result['meta']['skills']

    def test_get_presets_returns_all_expected_presets(self, manager):
        """Test get_presets returns all 6 expected presets"""
        result = manager.get_presets()
        
        expected_presets = ['default', 'laravel', 'wordpress', 'javascript', 'python', 'meta']
        assert set(result.keys()) == set(expected_presets)


class TestAgentManagerInitAgentStructure:
    """Test suite for init_agent_structure method"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({})

    def test_init_agent_structure_creates_directories(self, manager, tmp_path):
        """Test init_agent_structure creates all required directories"""
        result = manager.init_agent_structure(str(tmp_path))
        
        assert result['success'] is True
        assert (tmp_path / '.agent').exists()
        assert (tmp_path / '.agent' / 'skills').exists()
        assert (tmp_path / '.agent' / 'workflows').exists()
        assert (tmp_path / '.agent' / 'memory').exists()
        assert (tmp_path / '.agent' / 'ui' / 'assets').exists()
        assert (tmp_path / '.agent' / 'specs').exists()
        assert (tmp_path / '.agent' / 'qa').exists()

    def test_init_agent_structure_creates_gitignore(self, manager, tmp_path):
        """Test init_agent_structure creates .gitignore file"""
        result = manager.init_agent_structure(str(tmp_path))
        
        gitignore_path = tmp_path / '.agent' / '.gitignore'
        assert gitignore_path.exists()
        
        content = gitignore_path.read_text()
        assert 'memory/*.md' in content
        assert '!memory/README.md' in content
        assert 'logs/' in content

    def test_init_agent_structure_skips_existing_gitignore(self, manager, tmp_path):
        """Test init_agent_structure doesn't overwrite existing .gitignore"""
        gitignore_path = tmp_path / '.agent' / '.gitignore'
        gitignore_path.parent.mkdir(parents=True, exist_ok=True)
        gitignore_path.write_text("existing content\n")
        
        result = manager.init_agent_structure(str(tmp_path))
        
        assert result['success'] is True
        assert gitignore_path.read_text() == "existing content\n"

    def test_init_agent_structure_creates_memory_readme(self, manager, tmp_path):
        """Test init_agent_structure creates memory README"""
        result = manager.init_agent_structure(str(tmp_path))
        
        readme_path = tmp_path / '.agent' / 'memory' / 'README.md'
        assert readme_path.exists()
        
        content = readme_path.read_text()
        assert '# Project Memory' in content

    def test_init_agent_structure_skips_existing_memory_readme(self, manager, tmp_path):
        """Test init_agent_structure doesn't overwrite existing README"""
        readme_path = tmp_path / '.agent' / 'memory' / 'README.md'
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_text("existing readme\n")
        
        result = manager.init_agent_structure(str(tmp_path))
        
        assert readme_path.read_text() == "existing readme\n"

    def test_init_agent_structure_creates_memory_templates(self, manager, tmp_path):
        """Test init_agent_structure creates memory template files"""
        result = manager.init_agent_structure(str(tmp_path))
        
        memory_dir = tmp_path / '.agent' / 'memory'
        assert (memory_dir / 'active_context.md').exists()
        assert (memory_dir / 'architecture.md').exists()
        assert (memory_dir / 'decisions.md').exists()

    def test_init_agent_structure_active_context_content(self, manager, tmp_path):
        """Test active_context.md has correct content"""
        manager.init_agent_structure(str(tmp_path))
        
        content = (tmp_path / '.agent' / 'memory' / 'active_context.md').read_text()
        assert '# Active Context' in content
        assert '## Current Focus' in content
        assert 'Initial setup' in content

    def test_init_agent_structure_architecture_content(self, manager, tmp_path):
        """Test architecture.md has correct content"""
        manager.init_agent_structure(str(tmp_path))
        
        content = (tmp_path / '.agent' / 'memory' / 'architecture.md').read_text()
        assert '# Architecture' in content
        assert '## Overview' in content

    def test_init_agent_structure_decisions_content(self, manager, tmp_path):
        """Test decisions.md has correct content"""
        manager.init_agent_structure(str(tmp_path))
        
        content = (tmp_path / '.agent' / 'memory' / 'decisions.md').read_text()
        assert '# Decision Log' in content
        assert '## Records' in content

    def test_init_agent_structure_skips_existing_memory_files(self, manager, tmp_path):
        """Test init_agent_structure doesn't overwrite existing memory files"""
        memory_dir = tmp_path / '.agent' / 'memory'
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in ['active_context.md', 'architecture.md', 'decisions.md']:
            (memory_dir / filename).write_text("existing content\n")
        
        result = manager.init_agent_structure(str(tmp_path))
        
        assert result['success'] is True
        assert (memory_dir / 'active_context.md').read_text() == "existing content\n"
        assert (memory_dir / 'architecture.md').read_text() == "existing content\n"

    def test_init_agent_structure_returns_success_path(self, manager, tmp_path):
        """Test init_agent_structure returns success and path"""
        result = manager.init_agent_structure(str(tmp_path))
        
        assert result['success'] is True
        assert '.agent' in result['path']
        assert str(tmp_path) in result['path']

    def test_init_agent_structure_returns_preset_name(self, manager, tmp_path):
        """Test init_agent_structure returns preset name"""
        result = manager.init_agent_structure(str(tmp_path))
        
        assert result['preset'] == 'Standard Development'

    def test_init_agent_structure_returns_installed_skills(self, manager, tmp_path):
        """Test init_agent_structure returns installed skills list"""
        result = manager.init_agent_structure(str(tmp_path))
        
        assert 'skills' in result
        assert isinstance(result['skills'], list)
        assert len(result['skills']) > 0

    def test_init_agent_structure_with_laravel_preset(self, manager, tmp_path):
        """Test init_agent_structure with laravel preset"""
        result = manager.init_agent_structure(str(tmp_path), preset='laravel')
        
        assert result['success'] is True
        assert result['preset'] == 'Laravel Specialist'
        assert 'laravel_architect' in result['skills']
        assert 'test_engineer' in result['skills']

    def test_init_agent_structure_with_wordpress_preset(self, manager, tmp_path):
        """Test init_agent_structure with wordpress preset"""
        result = manager.init_agent_structure(str(tmp_path), preset='wordpress')
        
        assert result['success'] is True
        assert result['preset'] == 'WordPress Expert'
        assert 'wordpress_developer' in result['skills']

    def test_init_agent_structure_with_javascript_preset(self, manager, tmp_path):
        """Test init_agent_structure with javascript preset"""
        result = manager.init_agent_structure(str(tmp_path), preset='javascript')
        
        assert result['success'] is True
        assert result['preset'] == 'JavaScript/Node Stack'
        assert 'frontend_architect' in result['skills']

    def test_init_agent_structure_with_python_preset(self, manager, tmp_path):
        """Test init_agent_structure with python preset"""
        result = manager.init_agent_structure(str(tmp_path), preset='python')
        
        assert result['success'] is True
        assert result['preset'] == 'Python Data/Web'
        assert 'python_expert' in result['skills']

    def test_init_agent_structure_with_meta_preset(self, manager, tmp_path):
        """Test init_agent_structure with meta preset"""
        result = manager.init_agent_structure(str(tmp_path), preset='meta')
        
        assert result['success'] is True
        assert result['preset'] == 'Meta Skills'
        assert 'skill_creator' in result['skills']

    def test_init_agent_structure_with_invalid_preset_falls_back_to_default(self, manager, tmp_path):
        """Test init_agent_structure falls back to default for invalid preset"""
        result = manager.init_agent_structure(str(tmp_path), preset='invalid_preset')
        
        assert result['success'] is True
        assert result['preset'] == 'Standard Development'
        assert 'product_analyst' in result['skills']

    def test_init_agent_structure_handles_exception(self, manager):
        """Test init_agent_structure handles exceptions gracefully"""
        with patch.object(Path, 'resolve') as mock_resolve:
            mock_resolve.side_effect = PermissionError("Access denied")
            
            result = manager.init_agent_structure('/nonexistent/path')
            
            assert result['success'] is False
            assert 'error' in result

    def test_init_agent_structure_with_dot_argument(self, manager, tmp_path):
        """Test init_agent_structure uses current directory with '.' argument"""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = manager.init_agent_structure('.')
            
            assert result['success'] is True
            assert (tmp_path / '.agent').exists()
        finally:
            os.chdir(original_cwd)


class TestAgentManagerCreateSkillTemplate:
    """Test suite for _create_skill_template method"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({})

    def test_create_skill_template_creates_directory(self, manager, tmp_path):
        """Test _create_skill_template creates skill directory"""
        skills_dir = tmp_path / 'skills'
        skills_dir.mkdir()
        
        manager._create_skill_template(skills_dir, 'test_skill')
        
        assert (skills_dir / 'test_skill').exists()
        assert (skills_dir / 'test_skill').is_dir()

    def test_create_skill_template_creates_skill_md(self, manager, tmp_path):
        """Test _create_skill_template creates SKILL.md file"""
        skills_dir = tmp_path / 'skills'
        skills_dir.mkdir()
        
        manager._create_skill_template(skills_dir, 'test_skill')
        
        assert (skills_dir / 'test_skill' / 'SKILL.md').exists()

    def test_create_skill_template_skips_existing_file(self, manager, tmp_path):
        """Test _create_skill_template doesn't overwrite existing SKILL.md"""
        skills_dir = tmp_path / 'skills'
        skill_path = skills_dir / 'existing_skill'
        skill_path.mkdir(parents=True)
        (skill_path / 'SKILL.md').write_text("existing content\n")
        
        manager._create_skill_template(skills_dir, 'existing_skill')
        
        assert (skill_path / 'SKILL.md').read_text() == "existing content\n"

    def test_create_skill_template_handles_existing_directory(self, manager, tmp_path):
        """Test _create_skill_template handles existing skill directory"""
        skills_dir = tmp_path / 'skills'
        skill_path = skills_dir / 'test_skill'
        skill_path.mkdir(parents=True)
        
        manager._create_skill_template(skills_dir, 'test_skill')
        
        assert (skill_path / 'SKILL.md').exists()


class TestAgentManagerGetSkillContent:
    """Test suite for _get_skill_content method"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({})

    def test_get_skill_content_skill_creator(self, manager):
        """Test _get_skill_content returns correct content for skill_creator"""
        content = manager._get_skill_content('skill_creator')
        
        assert 'name: Skill Creator' in content
        assert 'description: A meta-agent' in content
        assert '## Role' in content
        assert 'AI Agent Architect' in content

    def test_get_skill_content_skill_creator_has_process_section(self, manager):
        """Test skill_creator content has process section"""
        content = manager._get_skill_content('skill_creator')
        
        assert '## Process' in content
        assert 'Interview' in content
        assert 'Drafting' in content

    def test_get_skill_content_skill_creator_has_standard_format(self, manager):
        """Test skill_creator content includes standard skill format"""
        content = manager._get_skill_content('skill_creator')
        
        assert '## Standard Skill Format' in content
        assert '```markdown' in content

    def test_get_skill_content_librarian(self, manager):
        """Test _get_skill_content returns correct content for librarian"""
        content = manager._get_skill_content('librarian')
        
        assert 'name: Librarian' in content
        assert 'description: Manages project memory' in content
        assert '## Role' in content
        assert 'Project Librarian' in content

    def test_get_skill_content_librarian_has_context_files(self, manager):
        """Test librarian content has context files section"""
        content = manager._get_skill_content('librarian')
        
        assert '## Context Files' in content
        assert 'active_context.md' in content
        assert 'architecture.md' in content
        assert 'decisions.md' in content

    def test_get_skill_content_librarian_has_rules(self, manager):
        """Test librarian content has rules section"""
        content = manager._get_skill_content('librarian')
        
        assert '## Rules' in content
        assert 'Be Concise' in content
        assert 'No Hallucinations' in content

    def test_get_skill_content_ui_designer(self, manager):
        """Test _get_skill_content returns correct content for ui_designer"""
        content = manager._get_skill_content('ui_designer')
        
        assert 'name: UI Designer' in content
        assert 'description: Specialist in converting visual designs' in content
        assert '## Role' in content
        assert 'UI/UX Engineer' in content

    def test_get_skill_content_ui_designer_has_workflow(self, manager):
        """Test ui_designer content has workflow section"""
        content = manager._get_skill_content('ui_designer')
        
        assert '## Workflow' in content
        assert 'Image to Code' in content
        assert 'Analysis' in content
        assert 'Implementation' in content

    def test_get_skill_content_ui_designer_has_rules(self, manager):
        """Test ui_designer content has rules section"""
        content = manager._get_skill_content('ui_designer')
        
        assert 'Responsiveness' in content
        assert 'Accessibility' in content
        assert 'Fidelity' in content

    def test_get_skill_content_unknown_skill_returns_generic(self, manager):
        """Test _get_skill_content returns generic template for unknown skills"""
        content = manager._get_skill_content('unknown_skill')
        
        assert 'name: Unknown Skill' in content
        assert '## Role' in content
        assert '## Capabilities' in content
        assert '## Rules' in content

    def test_get_skill_content_unknown_skill_has_title_cased_name(self, manager):
        """Test unknown skill name is title-cased in content"""
        content = manager._get_skill_content('custom_python_expert')
        
        assert 'name: Custom Python Expert' in content
        assert '# Custom Python Expert Instructions' in content

    def test_get_skill_content_generic_has_placeholder_capabilities(self, manager):
        """Test generic skill content has placeholder capabilities"""
        content = manager._get_skill_content('new_skill')
        
        assert '- Analyze requirements' in content
        assert '- Propose solutions' in content
        assert '- Review code' in content

    def test_get_skill_content_generic_has_default_rules(self, manager):
        """Test generic skill content has default rules"""
        content = manager._get_skill_content('new_skill')
        
        assert '1. Always follow project standards.' in content
        assert '2. Verify output before confirming.' in content


class TestAgentManagerGetSkillDescription:
    """Test suite for _get_skill_description method"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({})

    def test_get_skill_description_product_analyst(self, manager):
        """Test _get_skill_description returns correct description for product_analyst"""
        result = manager._get_skill_description('product_analyst')
        
        assert 'user requirements' in result.lower()
        assert 'technical specs' in result.lower()

    def test_get_skill_description_architect(self, manager):
        """Test _get_skill_description returns correct description for architect"""
        result = manager._get_skill_description('architect')
        
        assert 'software structure' in result.lower()
        assert 'decisions' in result.lower()

    def test_get_skill_description_git_manager(self, manager):
        """Test _get_skill_description returns correct description for git_manager"""
        result = manager._get_skill_description('git_manager')
        
        assert 'version control' in result.lower()

    def test_get_skill_description_laravel_architect(self, manager):
        """Test _get_skill_description returns correct description for laravel_architect"""
        result = manager._get_skill_description('laravel_architect')
        
        assert 'laravel' in result.lower()

    def test_get_skill_description_wordpress_developer(self, manager):
        """Test _get_skill_description returns correct description for wordpress_developer"""
        result = manager._get_skill_description('wordpress_developer')
        
        assert 'wp' in result.lower() or 'wordpress' in result.lower()

    def test_get_skill_description_test_engineer(self, manager):
        """Test _get_skill_description returns correct description for test_engineer"""
        result = manager._get_skill_description('test_engineer')
        
        assert 'test' in result.lower() or 'quality' in result.lower()

    def test_get_skill_description_unknown_skill_returns_default(self, manager):
        """Test _get_skill_description returns default for unknown skills"""
        result = manager._get_skill_description('unknown_skill')
        
        assert result == "Specialized agent skill."

    def test_get_skill_description_python_expert(self, manager):
        """Test _get_skill_description returns correct description for python_expert"""
        result = manager._get_skill_description('python_expert')
        
        assert 'python' in result.lower()


class TestAgentManagerInstallSkillFromUrl:
    """Test suite for install_skill_from_url method"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({})

    def test_install_skill_from_url_invalid_url_format(self, manager):
        """Test install_skill_from_url rejects invalid URL format"""
        result = manager.install_skill_from_url('invalid-url')
        
        assert result['success'] is False
        assert 'Invalid URL format' in result['error']

    def test_install_skill_from_url_invalid_url_no_protocol(self, manager):
        """Test install_skill_from_url rejects URL without protocol"""
        result = manager.install_skill_from_url('www.example.com/skill.md')
        
        assert result['success'] is False
        assert 'Invalid URL format' in result['error']

    def test_install_skill_from_url_missing_agent_directory(self, manager, tmp_path):
        """Test install_skill_from_url fails when .agent directory doesn't exist"""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b'---\nname: Test Skill\n---\nContent'
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                assert result['success'] is False
                assert '.agent directory not found' in result['error']
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_success(self, manager, tmp_path):
        """Test install_skill_from_url successfully downloads and installs skill"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: Test Skill\ndescription: A test skill\n---\n\n# Test Skill\n\nContent here.'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/test-skill.md')
                
                assert result['success'] is True
                assert 'test_skill' in result['name']
                assert 'SKILL.md' in result['path']
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_creates_skill_file(self, manager, tmp_path):
        """Test install_skill_from_url creates SKILL.md file"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: My Custom Skill\ndescription: Custom\n---\n\n# Instructions\n\nDo stuff.'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                manager.install_skill_from_url('https://example.com/skill.md')
                
                skill_file = skills_dir / 'my_custom_skill' / 'SKILL.md'
                assert skill_file.exists()
                content = skill_file.read_text()
                assert 'My Custom Skill' in content
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_sanitizes_skill_name(self, manager, tmp_path):
        """Test install_skill_from_url sanitizes skill name for folder"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: My@#$% Skill!!!\ndescription: Test\n---\n\nContent'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                assert result['success'] is True
                assert '@' not in result['name']
                assert '#' not in result['name']
                assert '$' not in result['name']
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_download_failure(self, manager, tmp_path):
        """Test install_skill_from_url handles download failure"""
        agent_dir = tmp_path / '.agent'
        agent_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = Exception("Connection refused")
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                assert result['success'] is False
                assert 'Failed to download' in result['error']
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_missing_frontmatter(self, manager, tmp_path):
        """Test install_skill_from_url handles missing frontmatter"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '# My Skill\n\nThis is content without frontmatter.'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/my-skill.md')
                
                assert result['success'] is True
                skill_file = skills_dir / 'my-skill' / 'SKILL.md'
                content = skill_file.read_text()
                assert '---' in content
                assert 'name:' in content
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_adds_frontmatter_if_missing(self, manager, tmp_path):
        """Test install_skill_from_url adds frontmatter to content without it"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '# Just a Skill\n\nNo frontmatter here.'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                skill_file = skills_dir / 'skill' / 'SKILL.md'
                content = skill_file.read_text()
                assert content.startswith('---')
                assert 'name:' in content
                assert 'description: Imported from' in content
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_uses_filename_as_fallback(self, manager, tmp_path):
        """Test install_skill_from_url uses filename from URL as fallback name"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '# Skill without name\n\nContent.'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/awesome-skill.md')
                
                assert 'awesome-skill' in result['name']
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_handles_special_characters_in_url(self, manager, tmp_path):
        """Test install_skill_from_url handles URLs with special characters"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: My Skill\ndescription: Test\n---\nContent'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/path/Skill@123.md')
                
                assert result['success'] is True
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_handles_http(self, manager, tmp_path):
        """Test install_skill_from_url accepts http URLs"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        skills_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: Test\ndescription: Test\n---\nContent'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('http://example.com/skill.md')
                
                assert result['success'] is True
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_exception_handling(self, manager, tmp_path):
        """Test install_skill_from_url handles general exceptions"""
        agent_dir = tmp_path / '.agent'
        agent_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = RuntimeError("Unexpected error")
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                assert result['success'] is False
                assert 'error' in result
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_creates_parent_directories(self, manager, tmp_path):
        """Test install_skill_from_url creates parent directories if needed"""
        agent_dir = tmp_path / '.agent'
        agent_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: Test Skill\n---\nContent'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                assert result['success'] is True
                assert (agent_dir / 'skills' / 'test_skill').exists()
        finally:
            os.chdir(original_cwd)

    def test_install_skill_from_url_existing_skill_directory(self, manager, tmp_path):
        """Test install_skill_from_url handles existing skill directory"""
        agent_dir = tmp_path / '.agent'
        skills_dir = agent_dir / 'skills'
        existing_skill = skills_dir / 'test_skill'
        existing_skill.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            skill_content = '---\nname: Test Skill\n---\nNew Content'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                result = manager.install_skill_from_url('https://example.com/skill.md')
                
                assert result['success'] is True
                skill_file = existing_skill / 'SKILL.md'
                assert skill_file.exists()
        finally:
            os.chdir(original_cwd)


class TestAgentManagerIntegration:
    """Integration tests for AgentManager"""

    @pytest.fixture
    def manager(self):
        from wslaragon.services.agent.agent_manager import AgentManager
        return AgentManager({'test': 'config'})

    def test_full_init_workflow(self, manager, tmp_path):
        """Test complete init_agent_structure workflow creates all expected files"""
        result = manager.init_agent_structure(str(tmp_path))
        
        assert result['success'] is True
        
        expected_dirs = [
            '.agent',
            '.agent/skills',
            '.agent/workflows',
            '.agent/memory',
            '.agent/ui/assets',
            '.agent/specs',
            '.agent/qa'
        ]
        for dir_path in expected_dirs:
            assert (tmp_path / dir_path).exists(), f"Directory {dir_path} not created"
        
        assert (tmp_path / '.agent/.gitignore').exists()
        assert (tmp_path / '.agent/memory/README.md').exists()
        assert (tmp_path / '.agent/memory/active_context.md').exists()
        assert (tmp_path / '.agent/memory/architecture.md').exists()
        assert (tmp_path / '.agent/memory/decisions.md').exists()

    def test_multiple_preset_skills_installed(self, manager, tmp_path):
        """Test that all skills from preset are installed"""
        result = manager.init_agent_structure(str(tmp_path), preset='javascript')
        
        assert result['success'] is True
        skills_dir = tmp_path / '.agent' / 'skills'
        
        for skill in result['skills']:
            skill_path = skills_dir / skill
            assert skill_path.exists(), f"Skill directory {skill} not created"
            assert (skill_path / 'SKILL.md').exists(), f"SKILL.md for {skill} not created"

    def test_init_then_install_skill_workflow(self, manager, tmp_path):
        """Test initializing structure then installing additional skill"""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            init_result = manager.init_agent_structure(str(tmp_path))
            assert init_result['success'] is True
            
            skill_content = '---\nname: Extra Skill\ndescription: Additional\n---\n\n# Extra Skill\n\nExtra content.'
            
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = skill_content.encode('utf-8')
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response
                
                install_result = manager.install_skill_from_url('https://example.com/extra.md')
                
                assert install_result['success'] is True
                assert (tmp_path / '.agent' / 'skills' / 'extra_skill' / 'SKILL.md').exists()
        finally:
            os.chdir(original_cwd)

    def test_all_presets_create_different_skills(self, manager, tmp_path):
        """Test that each preset creates different skill directories"""
        from pathlib import Path
        
        preset_skills = {}
        for preset_name in manager.get_presets().keys():
            test_dir = tmp_path / preset_name
            test_dir.mkdir()
            
            result = manager.init_agent_structure(str(test_dir), preset=preset_name)
            assert result['success'] is True
            
            skills_path = test_dir / '.agent' / 'skills'
            actual_skills = [d.name for d in skills_path.iterdir() if d.is_dir()]
            preset_skills[preset_name] = set(actual_skills)
        
        assert len(preset_skills['default']) > 0
        assert preset_skills['laravel'] != preset_skills['wordpress']
        assert preset_skills['python'] != preset_skills['javascript']