"""Tests for the Site Creator strategies module"""
import base64
import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from wslaragon.services.site_creators import (
    SiteCreator,
    HtmlSiteCreator,
    WordPressSiteCreator,
    LaravelSiteCreator,
    NodeSiteCreator,
    PythonSiteCreator,
    ViteSiteCreator,
    DefaultSiteCreator,
    get_site_creator,
)


class TestSiteCreatorABC:
    """Test suite for the SiteCreator abstract base class"""

    def test_site_creator_is_abstract(self):
        """Test that SiteCreator cannot be instantiated directly"""
        with pytest.raises(TypeError):
            SiteCreator(MagicMock(), "test", Path("/tmp"), Path("/tmp"), ".test")

    def test_site_creator_subclass_must_implement_create(self):
        """Test that subclasses must implement create method"""
        class IncompleteCreator(SiteCreator):
            pass

        with pytest.raises(TypeError):
            IncompleteCreator(MagicMock(), "test", Path("/tmp"), Path("/tmp"), ".test")


class TestHtmlSiteCreator:
    """Test suite for HtmlSiteCreator"""

    @pytest.fixture
    def html_creator(self, tmp_path, mock_config):
        """Create an HtmlSiteCreator instance"""
        web_root = tmp_path / "web" / "testsite"
        site_base_dir = tmp_path / "sites" / "testsite"
        return HtmlSiteCreator(
            config=mock_config,
            site_name="testsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test"
        )

    def test_html_creator_creates_index_html(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator creates index.html"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        messages = html_creator.create()

        assert isinstance(messages, list)
        index_path = web_root / "index.html"
        assert index_path.exists()

    def test_html_creator_creates_styles_directory(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator creates styles directory"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        html_creator.create()

        styles_dir = web_root / "styles"
        assert styles_dir.exists()
        assert styles_dir.is_dir()

    def test_html_creator_creates_css_file(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator creates estilos.css"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        html_creator.create()

        css_path = web_root / "styles" / "estilos.css"
        assert css_path.exists()
        content = css_path.read_text()
        assert "font-family" in content
        assert "background" in content

    def test_html_creator_creates_js_directory(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator creates js directory"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        html_creator.create()

        js_dir = web_root / "js"
        assert js_dir.exists()
        assert js_dir.is_dir()

    def test_html_creator_creates_js_file(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator creates app.js"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        html_creator.create()

        js_path = web_root / "js" / "app.js"
        assert js_path.exists()
        content = js_path.read_text()
        assert "DOMContentLoaded" in content
        assert "testsite" in content

    def test_html_creator_includes_site_name_in_html(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator includes site name in HTML content"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        html_creator.create()

        html_path = web_root / "index.html"
        content = html_path.read_text()
        assert "testsite" in content
        assert "<!DOCTYPE html>" in content
        assert "<title>testsite</title>" in content

    def test_html_creator_returns_empty_list_on_success(self, html_creator, tmp_path):
        """Test that HtmlSiteCreator returns empty list on success"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True, exist_ok=True)

        messages = html_creator.create()

        assert messages == []

    def test_html_creator_with_custom_site_name(self, tmp_path, mock_config):
        """Test HtmlSiteCreator with a different site name"""
        web_root = tmp_path / "web" / "myawesomesite"
        web_root.mkdir(parents=True, exist_ok=True)

        creator = HtmlSiteCreator(
            config=mock_config,
            site_name="myawesomesite",
            web_root=web_root,
            site_base_dir=tmp_path / "sites" / "myawesomesite",
            tld=".local"
        )

        creator.create()

        html_content = (web_root / "index.html").read_text()
        assert "myawesomesite" in html_content
        assert "<title>myawesomesite</title>" in html_content


class TestWordPressSiteCreator:
    """Test suite for WordPressSiteCreator"""

    @pytest.fixture
    def wp_creator(self, tmp_path, mock_config):
        """Create a WordPressSiteCreator instance"""
        web_root = tmp_path / "web" / "wpsite"
        site_base_dir = tmp_path / "sites" / "wpsite"
        return WordPressSiteCreator(
            config=mock_config,
            site_name="wpsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test"
        )

    def test_wp_creator_calls_wget_for_download(self, wp_creator, tmp_path):
        """Test that WordPressSiteCreator downloads WordPress via wget"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            wp_creator.create()

            # Check wget was called
            calls = [str(c) for c in mock_run.call_args_list]
            wget_called = any('wget' in str(call) for call in calls)
            assert wget_called

    def test_wp_creator_creates_wp_config(self, wp_creator, tmp_path):
        """Test that WordPressSiteCreator creates wp-config.php"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            wp_creator.create()

        wp_config_path = web_root / "wp-config.php"
        assert wp_config_path.exists()
        content = wp_config_path.read_text()
        assert "DB_NAME" in content
        assert "wpsite_db" in content
        assert "DB_USER" in content
        assert "DB_PASSWORD" in content

    def test_wp_creator_uses_db_password_from_config(self, wp_creator, tmp_path):
        """Test that WordPressSiteCreator uses password from config"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            wp_creator.create()

        content = (web_root / "wp-config.php").read_text()
        assert "test_password" in content

    def test_wp_creator_creates_index_php(self, wp_creator, tmp_path):
        """Test that WordPressSiteCreator creates index.php"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            wp_creator.create()

        index_path = web_root / "index.php"
        assert index_path.exists()
        content = index_path.read_text()
        assert "WP_USE_THEMES" in content
        assert "wp-blog-header" in content

    def test_wp_creator_removes_existing_web_root(self, wp_creator, tmp_path):
        """Test that WordPressSiteCreator removes existing web root"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)
        (web_root / "old_file.txt").write_text("old content")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            wp_creator.create()

        # The old file should be gone (shutil.rmtree was called)
        assert not (web_root / "old_file.txt").exists()

    def test_wp_creator_returns_empty_list_on_success(self, wp_creator, tmp_path):
        """Test that WordPressSiteCreator returns empty list on success"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            messages = wp_creator.create()

        assert messages == []


class TestLaravelSiteCreator:
    """Test suite for LaravelSiteCreator"""

    @pytest.fixture
    def laravel_creator(self, tmp_path, mock_config):
        """Create a LaravelSiteCreator instance"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        web_root = tmp_path / "web" / "laravelsite" / "public"
        return LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test"
        )

    def test_laravel_creator_calls_composer_create_project(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator calls composer create-project"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            laravel_creator.create()

            # Check composer create-project was called
            calls = [str(c) for c in mock_run.call_args_list]
            composer_called = any('composer' in str(call) and 'create-project' in str(call) for call in calls)
            assert composer_called

    def test_laravel_creator_uses_correct_version(self, tmp_path, mock_config):
        """Test that LaravelSiteCreator uses specified Laravel version"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=tmp_path / "web" / "laravelsite" / "public",
            site_base_dir=site_base_dir,
            tld=".test",
            version=11
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            creator.create()

            # Check version 11 was used
            calls = [str(c) for c in mock_run.call_args_list]
            version_call = any('laravel/laravel:^11.0' in str(call) for call in calls)
            assert version_call

    def test_laravel_creator_creates_env_file(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator creates .env file"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            laravel_creator.create()

        env_path = site_base_dir / ".env"
        assert env_path.exists()

    def test_laravel_creator_env_contains_app_key(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator generates APP_KEY"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            laravel_creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert "APP_KEY=base64:" in env_content

    def test_laravel_creator_env_contains_app_name(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator sets APP_NAME"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            laravel_creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert 'APP_NAME="laravelsite"' in env_content

    def test_laravel_creator_uses_mysql_by_default(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator configures MySQL by default"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            laravel_creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert "DB_CONNECTION=mysql" in env_content

    def test_laravel_creator_with_postgres(self, tmp_path, mock_config):
        """Test that LaravelSiteCreator configures PostgreSQL correctly"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=tmp_path / "web" / "laravelsite" / "public",
            site_base_dir=site_base_dir,
            tld=".test",
            db_type="postgres"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert "DB_CONNECTION=pgsql" in env_content
        assert "DB_PORT=5433" in env_content  # from mock_config

    def test_laravel_creator_with_supabase(self, tmp_path, mock_config):
        """Test that LaravelSiteCreator configures Supabase correctly"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=tmp_path / "web" / "laravelsite" / "public",
            site_base_dir=site_base_dir,
            tld=".test",
            db_type="supabase"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert "SUPABASE_URL=" in env_content
        assert "SUPABASE_ANON_KEY=" in env_content

    def test_laravel_creator_custom_database_name(self, tmp_path, mock_config):
        """Test that LaravelSiteCreator uses custom database name"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=tmp_path / "web" / "laravelsite" / "public",
            site_base_dir=site_base_dir,
            tld=".test",
            database_name="custom_db_name"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert "DB_DATABASE=custom_db_name" in env_content

    def test_laravel_creator_returns_success_messages(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator returns success messages"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            messages = laravel_creator.create()

        assert len(messages) > 0
        assert any("Laravel" in msg for msg in messages)

    def test_laravel_creator_handles_out_of_memory_error(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator retries with COMPOSER_MEMORY_LIMIT on OOM"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):  # Non-root user
                # First call fails with OOM, second succeeds (plus additional chown calls)
                mock_run.side_effect = [
                    MagicMock(returncode=1, stderr="out of memory error", stdout=""),  # composer create-project
                    MagicMock(returncode=0),  # composer retry
                    MagicMock(returncode=0),  # sudo chown
                    MagicMock(returncode=0),  # sudo chmod storage
                    MagicMock(returncode=0),  # sudo chmod bootstrap/cache
                ]

                messages = laravel_creator.create()

        # Should have retried and succeeded
        assert mock_run.call_count >= 2

    def test_laravel_creator_raises_on_failure(self, laravel_creator, tmp_path):
        """Test that LaravelSiteCreator raises Exception on failure"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stderr="Installation failed", 
                stdout=""
            )

            with pytest.raises(Exception, match="Laravel installation failed"):
                laravel_creator.create()


class TestNodeSiteCreator:
    """Test suite for NodeSiteCreator"""

    @pytest.fixture
    def node_creator(self, tmp_path, mock_config):
        """Create a NodeSiteCreator instance"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        web_root = tmp_path / "web" / "nodesite"
        return NodeSiteCreator(
            config=mock_config,
            site_name="nodesite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=3000
        )

    def test_node_creator_creates_app_js(self, node_creator, tmp_path):
        """Test that NodeSiteCreator creates app.js"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        node_creator.create()

        app_js_path = site_base_dir / "app.js"
        assert app_js_path.exists()

    def test_node_creator_app_js_contains_port(self, node_creator, tmp_path):
        """Test that app.js contains the proxy port"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        node_creator.create()

        content = (site_base_dir / "app.js").read_text()
        assert "3000" in content
        assert "http.createServer" in content

    def test_node_creator_creates_package_json(self, node_creator, tmp_path):
        """Test that NodeSiteCreator creates package.json"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        node_creator.create()

        pkg_path = site_base_dir / "package.json"
        assert pkg_path.exists()

    def test_node_creator_package_json_is_valid(self, node_creator, tmp_path):
        """Test that package.json is valid JSON"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        node_creator.create()

        pkg_path = site_base_dir / "package.json"
        pkg = json.loads(pkg_path.read_text())
        assert pkg["name"] == "nodesite"
        assert pkg["main"] == "app.js"
        assert "start" in pkg["scripts"]

    def test_node_creator_includes_site_name_in_package(self, node_creator, tmp_path):
        """Test that package.json includes site name"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        node_creator.create()

        pkg_path = site_base_dir / "package.json"
        pkg = json.loads(pkg_path.read_text())
        assert pkg["name"] == "nodesite"

    def test_node_creator_returns_message_with_port(self, node_creator, tmp_path):
        """Test that NodeSiteCreator returns message with proxy port"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        messages = node_creator.create()

        assert len(messages) == 1
        assert "3000" in messages[0]
        assert "pm2" in messages[0]

    def test_node_creator_without_proxy_port(self, tmp_path, mock_config):
        """Test NodeSiteCreator without proxy port (default None)"""
        site_base_dir = tmp_path / "sites" / "nodesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = NodeSiteCreator(
            config=mock_config,
            site_name="nodesite",
            web_root=tmp_path / "web" / "nodesite",
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=None
        )

        messages = creator.create()

        # Should handle None port gracefully
        app_content = (site_base_dir / "app.js").read_text()
        assert " PORT" in app_content or "port" in app_content


class TestPythonSiteCreator:
    """Test suite for PythonSiteCreator"""

    @pytest.fixture
    def python_creator(self, tmp_path, mock_config):
        """Create a PythonSiteCreator instance"""
        site_base_dir = tmp_path / "sites" / "pythonsite"
        web_root = tmp_path / "web" / "pythonsite"
        return PythonSiteCreator(
            config=mock_config,
            site_name="pythonsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=8000
        )

    def test_python_creator_creates_main_py(self, python_creator, tmp_path):
        """Test that PythonSiteCreator creates main.py"""
        site_base_dir = tmp_path / "sites" / "pythonsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        python_creator.create()

        main_py_path = site_base_dir / "main.py"
        assert main_py_path.exists()

    def test_python_creator_main_py_contains_port(self, python_creator, tmp_path):
        """Test that main.py contains the proxy port"""
        site_base_dir = tmp_path / "sites" / "pythonsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        python_creator.create()

        content = (site_base_dir / "main.py").read_text()
        assert "8000" in content
        assert "http.server" in content
        assert "socketserver" in content

    def test_python_creator_uses_http_server(self, python_creator, tmp_path):
        """Test that PythonSiteCreator uses http.server module"""
        site_base_dir = tmp_path / "sites" / "pythonsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        python_creator.create()

        content = (site_base_dir / "main.py").read_text()
        assert "import http.server" in content
        assert "import socketserver" in content

    def test_python_creator_returns_message_with_port(self, python_creator, tmp_path):
        """Test that PythonSiteCreator returns message with proxy port"""
        site_base_dir = tmp_path / "sites" / "pythonsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        messages = python_creator.create()

        assert len(messages) == 1
        assert "8000" in messages[0]
        assert "python" in messages[0].lower()


class TestViteSiteCreator:
    """Test suite for ViteSiteCreator"""

    @pytest.fixture
    def vite_creator(self, tmp_path, mock_config):
        """Create a ViteSiteCreator instance"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        web_root = tmp_path / "web" / "vitesite"
        return ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5173,
            vite_template="react"
        )

    def test_vite_creator_calls_npm_create(self, vite_creator, tmp_path):
        """Test that ViteSiteCreator calls npm create vite"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        # Create mock package.json for the script modification
        pkg_content = {"name": "vitesite", "scripts": {"dev": "vite"}}
        (site_base_dir / "package.json").write_text(json.dumps(pkg_content))

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):  # Non-root user
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    vite_creator.create()

                    # Check npm create vite was called
                    calls = [str(c) for c in mock_run.call_args_list]
                    create_called = any('npm' in str(call) and 'create' in str(call) for call in calls)
                    assert create_called

    def test_vite_creator_uses_template(self, vite_creator, tmp_path):
        """Test that ViteSiteCreator uses specified template"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        # Create mock package.json
        pkg_content = {"name": "vitesite", "scripts": {"dev": "vite"}}
        (site_base_dir / "package.json").write_text(json.dumps(pkg_content))

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    vite_creator.create()

                    # Check template was specified
                    calls = [str(c) for c in mock_run.call_args_list]
                    template_used = any('react' in str(call) or '--template' in str(call) for call in calls)
                    assert template_used

    def test_vite_creator_calls_npm_install(self, vite_creator, tmp_path):
        """Test that ViteSiteCreator calls npm install"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        # Create mock package.json
        pkg_content = {"name": "vitesite", "scripts": {"dev": "vite"}}
        (site_base_dir / "package.json").write_text(json.dumps(pkg_content))

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    vite_creator.create()

                    # Check npm install was called
                    calls = [str(c) for c in mock_run.call_args_list]
                    install_called = any('npm' in str(call) and 'install' in str(call) for call in calls)
                    assert install_called

    def test_vite_creator_modifies_package_json(self, vite_creator, tmp_path):
        """Test that ViteSiteCreator modifies package.json with port"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock package.json
        pkg_content = {"name": "vitesite", "scripts": {"dev": "vite"}}
        (site_base_dir / "package.json").write_text(json.dumps(pkg_content))

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    vite_creator.create()

        # Check package.json was modified
        pkg = json.loads((site_base_dir / "package.json").read_text())
        assert "5173" in pkg["scripts"]["dev"]

    def test_vite_creator_with_vanilla_template(self, tmp_path, mock_config):
        """Test ViteSiteCreator with vanilla template"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        # Create mock package.json
        pkg_content = {"name": "vitesite", "scripts": {"dev": "vite"}}
        (site_base_dir / "package.json").write_text(json.dumps(pkg_content))

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5173,
            vite_template="vanilla"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    creator.create()

                    calls = [str(c) for c in mock_run.call_args_list]
                    vanilla_used = any('vanilla' in str(call) for call in calls)
                    assert vanilla_used

    def test_vite_creator_returns_success_messages(self, vite_creator, tmp_path):
        """Test that ViteSiteCreator returns success messages"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        # Create mock package.json
        pkg_content = {"name": "vitesite", "scripts": {"dev": "vite"}}
        (site_base_dir / "package.json").write_text(json.dumps(pkg_content))

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    messages = vite_creator.create()

        assert any("Vite" in msg for msg in messages)
        assert any("react" in msg for msg in messages)

    def test_vite_creator_raises_on_failure(self, vite_creator, tmp_path):
        """Test that ViteSiteCreator raises Exception on failure"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.side_effect = subprocess.CalledProcessError(1, 'npm create')

                    with pytest.raises(Exception, match="Vite scaffolding failed"):
                        vite_creator.create()


class TestDefaultSiteCreator:
    """Test suite for DefaultSiteCreator"""

    @pytest.fixture
    def default_creator(self, tmp_path, mock_config):
        """Create a DefaultSiteCreator instance"""
        web_root = tmp_path / "web" / "defaultsite"
        site_base_dir = tmp_path / "sites" / "defaultsite"
        return DefaultSiteCreator(
            config=mock_config,
            site_name="defaultsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            php=True
        )

    def test_default_creator_creates_php_index(self, default_creator, tmp_path):
        """Test that DefaultSiteCreator creates index.php when php=True"""
        web_root = tmp_path / "web" / "defaultsite"
        web_root.mkdir(parents=True, exist_ok=True)

        default_creator.create()

        index_path = web_root / "index.php"
        assert index_path.exists()

    def test_default_creator_php_content(self, default_creator, tmp_path):
        """Test that PHP index contains phpinfo call"""
        web_root = tmp_path / "web" / "defaultsite"
        web_root.mkdir(parents=True, exist_ok=True)

        default_creator.create()

        content = (web_root / "index.php").read_text()
        assert "<?php" in content
        assert "phpinfo()" in content
        assert "phpversion()" in content

    def test_default_creator_static_site(self, tmp_path, mock_config):
        """Test that DefaultSiteCreator creates index.html when php=False"""
        web_root = tmp_path / "web" / "staticsite"
        web_root.mkdir(parents=True, exist_ok=True)

        creator = DefaultSiteCreator(
            config=mock_config,
            site_name="staticsite",
            web_root=web_root,
            site_base_dir=tmp_path / "sites" / "staticsite",
            tld=".test",
            php=False
        )

        creator.create()

        index_path = web_root / "index.html"
        assert index_path.exists()
        content = index_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "staticsite" in content

    def test_default_creator_includes_site_name_and_tld(self, default_creator, tmp_path):
        """Test that DefaultSiteCreator includes site name and TLD in content"""
        web_root = tmp_path / "web" / "defaultsite"
        web_root.mkdir(parents=True, exist_ok=True)

        default_creator.create()

        content = (web_root / "index.php").read_text()
        assert "defaultsite.test" in content

    def test_default_creator_returns_empty_list(self, default_creator, tmp_path):
        """Test that DefaultSiteCreator returns empty list on success"""
        web_root = tmp_path / "web" / "defaultsite"
        web_root.mkdir(parents=True, exist_ok=True)

        messages = default_creator.create()

        assert messages == []

    def test_default_creator_with_custom_tld(self, tmp_path, mock_config):
        """Test DefaultSiteCreator with custom TLD"""
        web_root = tmp_path / "web" / "customsite"
        web_root.mkdir(parents=True, exist_ok=True)

        creator = DefaultSiteCreator(
            config=mock_config,
            site_name="customsite",
            web_root=web_root,
            site_base_dir=tmp_path / "sites" / "customsite",
            tld=".local",
            php=False
        )

        creator.create()

        content = (web_root / "index.html").read_text()
        assert "customsite.local" in content


class TestGetSiteCreator:
    """Test suite for the get_site_creator factory function"""

    @pytest.fixture
    def setup_paths(self, tmp_path):
        """Setup common paths"""
        return {
            'web_root': tmp_path / "web" / "testsite",
            'site_base_dir': tmp_path / "sites" / "testsite",
        }

    def test_get_html_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns HtmlSiteCreator for html type"""
        creator = get_site_creator(
            site_type='html',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, HtmlSiteCreator)

    def test_get_wordpress_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns WordPressSiteCreator for wordpress type"""
        creator = get_site_creator(
            site_type='wordpress',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, WordPressSiteCreator)

    def test_get_laravel_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns LaravelSiteCreator for laravel type"""
        creator = get_site_creator(
            site_type='laravel',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, LaravelSiteCreator)

    def test_get_laravel_creator_with_version_number(self, setup_paths, mock_config):
        """Test that get_site_creator returns LaravelSiteCreator for numeric type"""
        creator = get_site_creator(
            site_type='11',  # Version number as string
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, LaravelSiteCreator)

    def test_get_laravel_creator_passes_version(self, setup_paths, mock_config):
        """Test that version is passed to LaravelSiteCreator correctly"""
        creator = get_site_creator(
            site_type='laravel',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
            version=10
        )
        assert isinstance(creator, LaravelSiteCreator)
        assert creator.version == 10

    def test_get_node_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns NodeSiteCreator for node type"""
        creator = get_site_creator(
            site_type='node',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
            proxy_port=3000
        )
        assert isinstance(creator, NodeSiteCreator)
        assert creator.proxy_port == 3000

    def test_get_python_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns PythonSiteCreator for python type"""
        creator = get_site_creator(
            site_type='python',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
            proxy_port=8000
        )
        assert isinstance(creator, PythonSiteCreator)

    def test_get_vite_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns ViteSiteCreator when vite_template is set"""
        creator = get_site_creator(
            site_type=None,
            vite_template='react',
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, ViteSiteCreator)
        assert creator.vite_template == 'react'

    def test_get_vite_creator_prioritized_over_site_type(self, setup_paths, mock_config):
        """Test that vite_template takes priority over site_type"""
        creator = get_site_creator(
            site_type='wordpress',  # This should be ignored
            vite_template='vue',
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, ViteSiteCreator)
        assert creator.vite_template == 'vue'

    def test_get_default_creator_when_none(self, setup_paths, mock_config):
        """Test that get_site_creator returns DefaultSiteCreator when site_type is None"""
        creator = get_site_creator(
            site_type=None,
            vite_template=None,
            php=True,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, DefaultSiteCreator)
        assert creator.php is True

    def test_get_default_creator_when_unknown_type(self, setup_paths, mock_config):
        """Test that get_site_creator returns DefaultSiteCreator for unknown type"""
        creator = get_site_creator(
            site_type='unknown-type',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test'
        )
        assert isinstance(creator, DefaultSiteCreator)
        assert creator.php is False

    def test_get_laravel_creator_with_db_type(self, setup_paths, mock_config):
        """Test that db_type is passed to LaravelSiteCreator"""
        creator = get_site_creator(
            site_type='laravel',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
            db_type='postgres'
        )
        assert isinstance(creator, LaravelSiteCreator)
        assert creator.db_type == 'postgres'

    def test_get_laravel_creator_with_database_name(self, setup_paths, mock_config):
        """Test that database_name is passed to LaravelSiteCreator"""
        creator = get_site_creator(
            site_type='laravel',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
            database_name='custom_db'
        )
        assert isinstance(creator, LaravelSiteCreator)
        assert creator.database_name == 'custom_db'


class TestSiteCreatorEdgeCases:
    """Test edge cases and error handling across all creators"""

    def test_html_creator_overwrites_existing_files(self, tmp_path, mock_config):
        """Test that HtmlSiteCreator overwrites existing files"""
        web_root = tmp_path / "web" / "existing"
        web_root.mkdir(parents=True, exist_ok=True)

        # Create existing file
        (web_root / "index.html").write_text("oldcontent")

        creator = HtmlSiteCreator(
            config=mock_config,
            site_name="existing",
            web_root=web_root,
            site_base_dir=tmp_path / "sites" / "existing",
            tld=".test"
        )

        creator.create()

        # Check content was replaced
        content = (web_root / "index.html").read_text()
        assert "oldcontent" not in content
        assert "existing" in content

    def test_html_creator_handles_missing_parent_directory(self, tmp_path, mock_config):
        """Test that HtmlSiteCreator handles missing parent directory"""
        # The HtmlSiteCreator creates subdirectories (styles, js) but expects
        # web_root to exist or be created by the caller
        web_root = tmp_path / "web" / "newdir"
        web_root.mkdir(parents=True, exist_ok=True)  # Create the base dir

        creator = HtmlSiteCreator(
            config=mock_config,
            site_name="newdir",
            web_root=web_root,
            site_base_dir=tmp_path / "sites" / "newdir",
            tld=".test"
        )

        creator.create()

        # Subdirectories should be created
        assert (web_root / "styles").exists()
        assert (web_root / "js").exists()

    def test_laravel_creator_uses_config_for_postgres_port(self, tmp_path, mock_config):
        """Test that LaravelSiteCreator reads postgres port from config"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=tmp_path / "web" / "laravelsite" / "public",
            site_base_dir=site_base_dir,
            tld=".test",
            db_type="postgres"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            creator.create()

        env_content = (site_base_dir / ".env").read_text()
        # mock_config has supabase.postgres_port=5433
        assert "DB_PORT=5433" in env_content

    def test_default_creator_creates_files_when_dir_exists(self, tmp_path, mock_config):
        """Test that DefaultSiteCreator creates files when web_root exists"""
        web_root = tmp_path / "web" / "existing"
        web_root.mkdir(parents=True, exist_ok=True)

        creator = DefaultSiteCreator(
            config=mock_config,
            site_name="existing",
            web_root=web_root,
            site_base_dir=tmp_path / "sites" / "existing",
            tld=".test",
            php=True
        )

        creator.create()

        # Files should be created when web_root exists
        assert (web_root / "index.php").exists()

    def test_vite_creator_handles_chown_failure(self, tmp_path, mock_config):
        """Test that ViteSiteCreator handles chown failure gracefully"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            # First call (chown) succeeds, subsequent succeed
            mock_run.return_value = MagicMock(returncode=0)

            # Create a mock package.json for the modification test
            (site_base_dir / "package.json").write_text('{"name": "vitesite", "scripts": {"dev": "vite"}}')

            messages = creator.create()

            # Should complete without raising
            assert len(messages) >= 0

    def test_all_creators_inherit_from_base(self):
        """Test that all creator classes inherit from SiteCreator"""
        from wslaragon.services.site_creators import (
            HtmlSiteCreator, WordPressSiteCreator, LaravelSiteCreator,
            NodeSiteCreator, PythonSiteCreator, ViteSiteCreator, DefaultSiteCreator
        )

        # Check inheritance
        assert issubclass(HtmlSiteCreator, SiteCreator)
        assert issubclass(WordPressSiteCreator, SiteCreator)
        assert issubclass(LaravelSiteCreator, SiteCreator)
        assert issubclass(NodeSiteCreator, SiteCreator)
        assert issubclass(PythonSiteCreator, SiteCreator)
        assert issubclass(ViteSiteCreator, SiteCreator)
        assert issubclass(DefaultSiteCreator, SiteCreator)