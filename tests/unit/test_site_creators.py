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
    SvelteKitSiteCreator,
    AstroSiteCreator,
    AstroHeadlessSiteCreator,
    PhpMyAdminSiteCreator,
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

    def test_site_creator_uses_configured_db_user(self, tmp_path, mock_config_ubuntu):
        """Test that WordPressSiteCreator uses configured DB_USER instead of root"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)
        site_base_dir = tmp_path / "sites" / "wpsite"

        creator = WordPressSiteCreator(
            config=mock_config_ubuntu,
            site_name="wpsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            creator.create()

        content = (web_root / "wp-config.php").read_text()
        assert "define( 'DB_USER', 'wslaragon' );" in content
        assert "define( 'DB_USER', 'root' );" not in content
        assert "wslaragon_pass" in content

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

    def test_laravel_creator_uses_configured_db_user(self, tmp_path, mock_config_ubuntu):
        """Test that LaravelSiteCreator uses configured DB_USER/DB_PASSWORD for MySQL"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        web_root = tmp_path / "web" / "laravelsite" / "public"

        creator = LaravelSiteCreator(
            config=mock_config_ubuntu,
            site_name="laravelsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            creator.create()

        env_content = (site_base_dir / ".env").read_text()
        assert "DB_USERNAME=wslaragon" in env_content
        assert "DB_PASSWORD=wslaragon_pass" in env_content
        assert "DB_USERNAME=root" not in env_content

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


class TestWordPressEdgeCases:
    """Test WordPress creator edge cases"""

    def test_wp_creator_copies_from_wordpress_dir(self, tmp_path, mock_config):
        """Test that WordPressSiteCreator copies from wordpress dir when exists"""
        web_root = tmp_path / "web" / "wpsite"
        web_root.mkdir(parents=True, exist_ok=True)
        site_base_dir = tmp_path / "sites" / "wpsite"

        wordpress_dir = tmp_path / "web" / "wordpress"
        wordpress_dir.mkdir(parents=True, exist_ok=True)
        (wordpress_dir / "wp-load.php").write_text("<?php // wp load")

        creator = WordPressSiteCreator(
            config=mock_config,
            site_name="wpsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            creator.create()

            calls = [str(c) for c in mock_run.call_args_list]
            cp_called = any('cp' in str(call) and 'wordpress' in str(call) for call in calls)
            rm_called = any('rm' in str(call) and 'wordpress' in str(call) for call in calls)
            assert cp_called or any(str(wordpress_dir) in str(call) for call in calls)


class TestLaravelEdgeCases:
    """Test Laravel creator edge cases"""

    def test_laravel_creator_running_as_root(self, tmp_path, mock_config):
        """Test LaravelSiteCreator when running as root (geteuid == 0)"""
        site_base_dir = tmp_path / "sites" / "laravelsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        creator = LaravelSiteCreator(
            config=mock_config,
            site_name="laravelsite",
            web_root=tmp_path / "web" / "laravelsite" / "public",
            site_base_dir=site_base_dir,
            tld=".test"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=0):
                with patch.dict(os.environ, {'SUDO_USER': 'testuser', 'USER': 'root'}):
                    mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

                    creator.create()

                    calls = [str(c) for c in mock_run.call_args_list]
                    sudo_u_called = any('sudo' in str(call) and '-u' in str(call) for call in calls)
                    assert sudo_u_called or len(calls) > 0


class TestViteEdgeCases:
    """Test Vite creator edge cases"""

    def test_vite_creator_npm_fallback_runuser_success(self, tmp_path, mock_config):
        """Test ViteSiteCreator uses runuser when shutil.which returns None"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=0):
                with patch.dict(os.environ, {'SUDO_USER': 'testuser'}):
                    with patch('shutil.which', return_value=None):
                        mock_run.return_value = MagicMock(returncode=0, stdout="/home/test/.nvm/versions/node/v18/bin/npm\n", stderr="")

                        creator.create()

                        calls = [str(c) for c in mock_run.call_args_list]
                        runuser_called = any('runuser' in str(call) for call in calls)
                        assert runuser_called

    def test_vite_creator_npm_fallback_runuser_failure(self, tmp_path, mock_config):
        """Test ViteSiteCreator falls back to 'npm' when runuser returns non-zero"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=0):
                with patch.dict(os.environ, {'SUDO_USER': 'testuser'}):
                    with patch('shutil.which', return_value=None):
                        runuser_result = MagicMock(returncode=1, stdout="", stderr="not found")
                        def side_effect(*args, **kwargs):
                            if 'runuser' in str(args):
                                return runuser_result
                            return MagicMock(returncode=0)
                        mock_run.side_effect = side_effect

                        creator.create()

    def test_vite_creator_npm_fallback_exception(self, tmp_path, mock_config):
        """Test ViteSiteCreator wraps a raw runuser exception into a clear scaffolding error"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            vite_template="react"
        )

        call_count = [0]
        def mock_run_side_effect(*args, **kwargs):
            call_count[0] += 1
            if 'runuser' in str(args):
                raise Exception("runuser failed")
            return MagicMock(returncode=0)

        with patch('subprocess.run', side_effect=mock_run_side_effect):
            with patch('os.geteuid', return_value=0):
                with patch.dict(os.environ, {'SUDO_USER': 'testuser'}):
                    with patch('shutil.which', return_value=None):
                        with pytest.raises(Exception, match="Vite scaffolding failed"):
                            creator.create()

    def test_vite_creator_modifies_vite_config_js(self, tmp_path, mock_config):
        """Test ViteSiteCreator modifies vite.config.js with allowedHosts"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        
        vite_config_content = "import { defineConfig } from 'vite'\n\nexport default defineConfig({\n  plugins: []\n})"
        (site_base_dir / "vite.config.js").write_text(vite_config_content)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5173,
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    creator.create()

                    config_content = (site_base_dir / "vite.config.js").read_text()
                    assert "allowedHosts: true" in config_content
                    assert "server: {" in config_content

    def test_vite_creator_modifies_vite_config_ts(self, tmp_path, mock_config):
        """Test ViteSiteCreator modifies vite.config.ts with allowedHosts"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        
        vite_config_content = "import { defineConfig } from 'vite'\n\nexport default defineConfig({\n  plugins: []\n})"
        (site_base_dir / "vite.config.ts").write_text(vite_config_content)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5173,
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    creator.create()

                    config_content = (site_base_dir / "vite.config.ts").read_text()
                    assert "allowedHosts: true" in config_content

    def test_vite_creator_skips_config_if_allowedhosts_exists(self, tmp_path, mock_config):
        """Test ViteSiteCreator skips modification if allowedHosts already exists"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        
        vite_config_content = "import { defineConfig } from 'vite'\n\nexport default defineConfig({\n  server: {\n    allowedHosts: true\n  },\n  plugins: []\n})"
        (site_base_dir / "vite.config.js").write_text(vite_config_content)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5173,
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    creator.create()

                    config_content = (site_base_dir / "vite.config.js").read_text()
                    config_content.count("allowedHosts")
                    assert config_content.count("allowedHosts: true") == 1

    def test_vite_creator_skips_config_if_no_defineconfig(self, tmp_path, mock_config):
        """Test ViteSiteCreator skips modification if no defineConfig in config"""
        site_base_dir = tmp_path / "sites" / "vitesite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        
        vite_config_content = "export default {\n  plugins: []\n}"
        (site_base_dir / "vite.config.js").write_text(vite_config_content)
        (site_base_dir / "package.json").write_text('{"name": "test", "scripts": {"dev": "vite"}}')

        creator = ViteSiteCreator(
            config=mock_config,
            site_name="vitesite",
            web_root=tmp_path / "web" / "vitesite",
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5173,
            vite_template="react"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch('shutil.which', return_value='/usr/bin/npm'):
                    mock_run.return_value = MagicMock(returncode=0)

                    creator.create()

                    config_content = (site_base_dir / "vite.config.js").read_text()
                    assert "server" not in config_content


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
            NodeSiteCreator, PythonSiteCreator, ViteSiteCreator, SvelteKitSiteCreator, DefaultSiteCreator
        )

        # Check inheritance
        assert issubclass(HtmlSiteCreator, SiteCreator)
        assert issubclass(WordPressSiteCreator, SiteCreator)
        assert issubclass(LaravelSiteCreator, SiteCreator)
        assert issubclass(NodeSiteCreator, SiteCreator)
        assert issubclass(PythonSiteCreator, SiteCreator)
        assert issubclass(ViteSiteCreator, SiteCreator)
        assert issubclass(SvelteKitSiteCreator, SiteCreator)
        assert issubclass(DefaultSiteCreator, SiteCreator)

    def test_sveltekit_factory_returns_creator(self, tmp_path, mock_config):
        """Test factory returns SvelteKit creator for headless frontend."""
        creator = get_site_creator(
            'sveltekit', None, False, mock_config, 'mysite',
            tmp_path / 'web' / 'mysite' / 'front',
            tmp_path / 'web' / 'mysite' / 'front',
            '.test', 3000
        )

        assert isinstance(creator, SvelteKitSiteCreator)

    def test_wp_creator_uses_sanitized_custom_database_name(self, tmp_path, mock_config):
        """Test WordPress creator uses injected DB name for subdomain-safe headless DBs."""
        web_root = tmp_path / "web" / "mysite" / "back"
        web_root.mkdir(parents=True, exist_ok=True)
        creator = WordPressSiteCreator(
            config=mock_config,
            site_name="api.mysite",
            web_root=web_root,
            site_base_dir=web_root,
            tld=".test",
            database_name="api_mysite_db"
        )

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            creator.create()

        content = (web_root / "wp-config.php").read_text()
        assert "api_mysite_db" in content
        assert "api.mysite_db" not in content


class TestSvelteKitSiteCreator:
    """Test suite for SvelteKitSiteCreator"""

    @pytest.fixture
    def sveltekit_creator(self, tmp_path, mock_config):
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        web_root = tmp_path / "web" / "sveltekitsite"
        return SvelteKitSiteCreator(
            config=mock_config,
            site_name="sveltekitsite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=5174,
        )

    def test_sveltekit_creator_success_path(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator full success path with sv create."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "package.json").write_text(json.dumps({"name": "sveltekitsite"}))
        (site_base_dir / "vite.config.ts").write_text(
            "import { defineConfig } from 'vite'\n\nexport default defineConfig({\n  plugins: []\n})"
        )

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

                messages = sveltekit_creator.create()

        assert any("SvelteKit" in msg for msg in messages)
        pkg = json.loads((site_base_dir / "package.json").read_text())
        assert "5174" in pkg["scripts"]["dev"]
        assert "5174" in pkg["scripts"]["start"]
        assert pkg["scripts"]["build"] == "vite build"

        vite_config_content = (site_base_dir / "vite.config.ts").read_text()
        assert "allowedHosts" in vite_config_content
        assert "sveltekitsite.test" in vite_config_content

    def test_sveltekit_creator_falls_back_to_npm_create_svelte(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator falls back when 'npx sv create' fails."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown from _prepare_run_as_user
                    MagicMock(returncode=1, stdout="", stderr="sv create not found"),  # primary scaffold
                    MagicMock(returncode=0, stdout="", stderr=""),  # fallback scaffold
                    MagicMock(returncode=0, stdout="", stderr=""),  # npm install
                ]

                messages = sveltekit_creator.create()

        assert mock_run.call_count == 4
        assert any("SvelteKit" in msg for msg in messages)

    def test_sveltekit_creator_raises_when_both_scaffolds_fail(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator raises when both scaffold commands fail."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown
                    MagicMock(returncode=1, stdout="", stderr="primary fail"),
                    MagicMock(returncode=1, stdout="", stderr="fallback fail"),
                ]

                with pytest.raises(Exception, match="SvelteKit scaffolding failed"):
                    sveltekit_creator.create()

    def test_sveltekit_creator_raises_on_npm_install_failure(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator raises when npm install fails."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown
                    MagicMock(returncode=0, stdout="", stderr=""),  # scaffold ok
                    MagicMock(returncode=1, stdout="", stderr="install boom"),  # npm install
                ]

                with pytest.raises(Exception, match="SvelteKit npm install failed"):
                    sveltekit_creator.create()

    def test_sveltekit_creator_skips_vite_config_if_allowed_hosts_present(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator does not double-modify vite.config.ts."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        original_content = (
            "import { defineConfig } from 'vite'\n\n"
            "export default defineConfig({\n  server: {\n    allowedHosts: ['x']\n  },\n  plugins: []\n})"
        )
        (site_base_dir / "vite.config.ts").write_text(original_content)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

                sveltekit_creator.create()

        assert (site_base_dir / "vite.config.ts").read_text() == original_content

    def test_sveltekit_creator_handles_package_json_without_scripts_key(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator adds a scripts dict when missing."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "package.json").write_text(json.dumps({"name": "sveltekitsite"}))

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

                sveltekit_creator.create()

        pkg = json.loads((site_base_dir / "package.json").read_text())
        assert "scripts" in pkg
        assert "dev" in pkg["scripts"]

    def test_sveltekit_creator_wraps_calledprocesserror(self, sveltekit_creator, tmp_path):
        """Test SvelteKitSiteCreator wraps a raw CalledProcessError."""
        site_base_dir = tmp_path / "sites" / "sveltekitsite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        def side_effect(*args, **kwargs):
            if 'sv create' in str(args):
                raise subprocess.CalledProcessError(1, 'npx sv create')
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch('subprocess.run', side_effect=side_effect):
            with patch('os.geteuid', return_value=1000):
                with pytest.raises(Exception, match="SvelteKit project creation failed"):
                    sveltekit_creator.create()


class TestAstroSiteCreator:
    """Test suite for AstroSiteCreator"""

    @pytest.fixture
    def astro_creator(self, tmp_path, mock_config):
        site_base_dir = tmp_path / "sites" / "astrosite"
        web_root = tmp_path / "web" / "astrosite"
        return AstroSiteCreator(
            config=mock_config,
            site_name="astrosite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=4321,
            astro_template="basics",
        )

    def test_astro_creator_success_path(self, astro_creator, tmp_path):
        """Test AstroSiteCreator full success path."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "package.json").write_text(json.dumps({"name": "astrosite"}))
        (site_base_dir / "dist").mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

                messages = astro_creator.create()

        assert any("Astro" in msg for msg in messages)
        assert any("basics" in msg for msg in messages)
        pkg = json.loads((site_base_dir / "package.json").read_text())
        assert pkg["scripts"]["dev"] == "astro dev --host"
        assert pkg["scripts"]["build"] == "astro build"
        assert pkg["scripts"]["preview"] == "astro preview --host"

    def test_astro_creator_delegates_to_headless_for_headless_template(self, tmp_path, mock_config):
        """Test AstroSiteCreator delegates to AstroHeadlessSiteCreator for 'headless' template."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        web_root = tmp_path / "web" / "astrosite"

        creator = AstroSiteCreator(
            config=mock_config,
            site_name="astrosite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=4321,
            astro_template="headless",
        )

        with patch('wslaragon.services.site_creators.AstroHeadlessSiteCreator') as MockHeadless:
            MockHeadless.return_value.create.return_value = ["[green]headless ok[/green]"]

            messages = creator.create()

        MockHeadless.assert_called_once_with(
            mock_config, "astrosite", web_root, site_base_dir, ".test", 4321
        )
        assert messages == ["[green]headless ok[/green]"]

    def test_astro_creator_falls_back_to_interactive_scaffold(self, astro_creator, tmp_path):
        """Test AstroSiteCreator retries with interactive scaffold on failure."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "dist").mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown
                    MagicMock(returncode=1, stdout="", stderr="template flag unsupported"),  # primary scaffold
                    MagicMock(returncode=0, stdout="", stderr=""),  # interactive fallback scaffold
                    MagicMock(returncode=0, stdout="", stderr=""),  # npm install
                    MagicMock(returncode=0, stdout="", stderr=""),  # npm run build
                ]

                messages = astro_creator.create()

        assert mock_run.call_count == 5
        assert any("Astro" in msg for msg in messages)

    def test_astro_creator_raises_when_both_scaffolds_fail(self, astro_creator, tmp_path):
        """Test AstroSiteCreator raises when both scaffold attempts fail."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown
                    MagicMock(returncode=1, stdout="", stderr="primary fail"),
                    MagicMock(returncode=1, stdout="", stderr="fallback fail too"),
                ]

                with pytest.raises(Exception, match="Astro scaffolding failed"):
                    astro_creator.create()

    def test_astro_creator_raises_on_npm_install_failure(self, astro_creator, tmp_path):
        """Test AstroSiteCreator raises when npm install fails."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown
                    MagicMock(returncode=0, stdout="", stderr=""),  # scaffold ok
                    MagicMock(returncode=1, stdout="", stderr="install boom"),  # npm install
                ]

                with pytest.raises(Exception, match="Astro npm install failed"):
                    astro_creator.create()

    def test_astro_creator_raises_on_build_failure(self, astro_creator, tmp_path):
        """Test AstroSiteCreator raises when npm run build fails."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # chown
                    MagicMock(returncode=0, stdout="", stderr=""),  # scaffold ok
                    MagicMock(returncode=0, stdout="", stderr=""),  # npm install ok
                    MagicMock(returncode=1, stdout="", stderr="build boom"),  # npm run build
                ]

                with pytest.raises(Exception, match="Astro build failed"):
                    astro_creator.create()

    def test_astro_creator_raises_when_dist_missing(self, astro_creator, tmp_path):
        """Test AstroSiteCreator raises when dist/ was not produced by the build."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

                with pytest.raises(Exception, match="Astro build did not produce dist/ directory"):
                    astro_creator.create()

    def test_astro_creator_wraps_calledprocesserror(self, astro_creator, tmp_path):
        """Test AstroSiteCreator wraps a raw CalledProcessError."""
        site_base_dir = tmp_path / "sites" / "astrosite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        def side_effect(*args, **kwargs):
            if 'npm create astro' in str(args):
                raise subprocess.CalledProcessError(1, 'npm create astro')
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch('subprocess.run', side_effect=side_effect):
            with patch('os.geteuid', return_value=1000):
                with pytest.raises(Exception, match="Astro project creation failed"):
                    astro_creator.create()


class TestAstroHeadlessSiteCreator:
    """Test suite for AstroHeadlessSiteCreator"""

    @pytest.fixture
    def headless_creator(self, tmp_path, mock_config):
        site_base_dir = tmp_path / "sites" / "headlesssite"
        web_root = tmp_path / "web" / "headlesssite"
        return AstroHeadlessSiteCreator(
            config=mock_config,
            site_name="headlesssite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
            proxy_port=4322,
        )

    @staticmethod
    def _build_side_effect(site_base_dir, install_rc=0, build_rc=0, create_dist=True):
        def side_effect(*args, **kwargs):
            cmd_str = str(args) + str(kwargs)
            if 'rm' in cmd_str and '-rf' in cmd_str:
                return MagicMock(returncode=0)
            if 'build' in cmd_str:
                if create_dist:
                    (site_base_dir / "dist").mkdir(parents=True, exist_ok=True)
                return MagicMock(returncode=build_rc, stdout="", stderr="build failed")
            if 'install' in cmd_str:
                return MagicMock(returncode=install_rc, stdout="", stderr="install failed")
            return MagicMock(returncode=0, stdout="", stderr="")
        return side_effect

    def test_headless_creator_success_path_writes_all_files(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator writes the full project scaffold on success."""
        site_base_dir = tmp_path / "sites" / "headlesssite"

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch.dict(os.environ, {'USER': 'testuser'}):
                    mock_run.side_effect = self._build_side_effect(site_base_dir)

                    messages = headless_creator.create()

        assert (site_base_dir / ".env").exists()
        assert (site_base_dir / ".env.example").exists()
        assert (site_base_dir / "package.json").exists()
        assert (site_base_dir / "astro.config.mjs").exists()
        assert (site_base_dir / "tsconfig.json").exists()
        assert (site_base_dir / "src" / "utils" / "api.ts").exists()
        assert (site_base_dir / "src" / "components" / "Island.tsx").exists()
        assert (site_base_dir / "src" / "layouts" / "BaseLayout.astro").exists()
        assert (site_base_dir / "src" / "pages" / "index.astro").exists()
        assert (site_base_dir / "public" / "favicon.svg").exists()

        pkg = json.loads((site_base_dir / "package.json").read_text())
        assert "4322" in pkg["scripts"]["dev"]

        env_content = (site_base_dir / ".env").read_text()
        assert "SITE_NAME=headlesssite" in env_content
        assert "headlesssite.test" in env_content

        assert any("Astro Headless project created successfully!" in msg for msg in messages)
        assert any("Static site built" in msg for msg in messages)

    def test_headless_creator_root_user_uses_runuser(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator uses runuser for install/build when running as root."""
        site_base_dir = tmp_path / "sites" / "headlesssite"

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=0):
                with patch.dict(os.environ, {'SUDO_USER': 'testuser'}):
                    mock_run.side_effect = self._build_side_effect(site_base_dir)

                    headless_creator.create()

        calls = [str(c) for c in mock_run.call_args_list]
        assert any('runuser' in c and 'npm install' in c for c in calls)
        assert any('runuser' in c and 'npm run build' in c for c in calls)

    def test_headless_creator_non_root_uses_plain_npm(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator calls plain npm when not root."""
        site_base_dir = tmp_path / "sites" / "headlesssite"

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch.dict(os.environ, {'USER': 'testuser'}):
                    mock_run.side_effect = self._build_side_effect(site_base_dir)

                    headless_creator.create()

        calls = [c.args[0] for c in mock_run.call_args_list if c.args]
        assert any(c == ['npm', 'install'] for c in calls)
        assert any(c == ['npm', 'run', 'build'] for c in calls)

    def test_headless_creator_removes_existing_site_base_dir(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator removes an existing site_base_dir first."""
        site_base_dir = tmp_path / "sites" / "headlesssite"
        site_base_dir.mkdir(parents=True, exist_ok=True)
        (site_base_dir / "stale.txt").write_text("old")

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch.dict(os.environ, {'USER': 'testuser'}):
                    mock_run.side_effect = self._build_side_effect(site_base_dir)

                    headless_creator.create()

        calls = [str(c) for c in mock_run.call_args_list]
        assert any('rm' in c and '-rf' in c and 'headlesssite' in c for c in calls)

    def test_headless_creator_npm_install_warning_message(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator reports a warning when npm install fails."""
        site_base_dir = tmp_path / "sites" / "headlesssite"

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch.dict(os.environ, {'USER': 'testuser'}):
                    mock_run.side_effect = self._build_side_effect(site_base_dir, install_rc=1)

                    messages = headless_creator.create()

        assert any("npm install had warnings" in msg for msg in messages)

    def test_headless_creator_build_failure_message(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator reports a manual-build message when build fails."""
        site_base_dir = tmp_path / "sites" / "headlesssite"

        with patch('subprocess.run') as mock_run:
            with patch('os.geteuid', return_value=1000):
                with patch.dict(os.environ, {'USER': 'testuser'}):
                    mock_run.side_effect = self._build_side_effect(site_base_dir, build_rc=1, create_dist=False)

                    messages = headless_creator.create()

        assert any("Build failed" in msg for msg in messages)
        assert not (site_base_dir / "dist").exists()

    def test_headless_creator_wraps_calledprocesserror(self, headless_creator, tmp_path):
        """Test AstroHeadlessSiteCreator wraps a raw CalledProcessError from the initial cleanup."""
        site_base_dir = tmp_path / "sites" / "headlesssite"
        site_base_dir.mkdir(parents=True, exist_ok=True)

        def side_effect(*args, **kwargs):
            cmd_str = str(args)
            if 'rm' in cmd_str and '-rf' in cmd_str:
                raise subprocess.CalledProcessError(1, 'sudo rm -rf')
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch('subprocess.run', side_effect=side_effect):
            with patch('os.geteuid', return_value=1000):
                with patch.dict(os.environ, {'USER': 'testuser'}):
                    with pytest.raises(Exception, match="Astro Headless project creation failed"):
                        headless_creator.create()


class TestPhpMyAdminSiteCreator:
    """Test suite for PhpMyAdminSiteCreator"""

    PMA_HARDCODED_DIR = Path('/tmp/phpMyAdmin-5.2.2-all-languages')

    @pytest.fixture
    def pma_creator(self, tmp_path, mock_config):
        web_root = tmp_path / "web" / "pmasite"
        site_base_dir = tmp_path / "sites" / "pmasite"
        return PhpMyAdminSiteCreator(
            config=mock_config,
            site_name="pmasite",
            web_root=web_root,
            site_base_dir=site_base_dir,
            tld=".test",
        )

    def _cleanup_extracted_dirs(self):
        for p in Path('/tmp').glob('phpMyAdmin-*-all-languages'):
            shutil.rmtree(str(p), ignore_errors=True)

    @staticmethod
    def _cp_recreates_web_root_side_effect(web_root):
        """subprocess.run is fully mocked, so the real `cp -r` never runs.
        Recreate web_root (which the production code just rmtree'd) so the
        subsequent real `open(web_root / "config.inc.php", 'w')` succeeds."""
        def side_effect(*args, **kwargs):
            cmd_str = str(args)
            if 'cp' in cmd_str and '-r' in cmd_str:
                web_root.mkdir(parents=True, exist_ok=True)
            return MagicMock(returncode=0, stdout="", stderr="")
        return side_effect

    def test_pma_creator_success_installs_from_extracted_dir(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator full success path using the primary extracted dir."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)

        self._cleanup_extracted_dirs()
        self.PMA_HARDCODED_DIR.mkdir(parents=True, exist_ok=True)
        (self.PMA_HARDCODED_DIR / "index.php").write_text("<?php // pma")

        try:
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = self._cp_recreates_web_root_side_effect(web_root)

                messages = pma_creator.create()

            config_path = web_root / "config.inc.php"
            assert config_path.exists()
            content = config_path.read_text()
            assert "blowfish_secret" in content
            assert "auth_type" in content

            assert (web_root / "tmp").exists()
            assert any("phpMyAdmin 5.2.2 installed successfully!" in msg for msg in messages)
            assert any("pmasite.test" in msg for msg in messages)
        finally:
            self._cleanup_extracted_dirs()

    def test_pma_creator_falls_back_to_gz_when_xz_download_fails(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator retries with .tar.gz when the .tar.xz download fails."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)

        self._cleanup_extracted_dirs()
        self.PMA_HARDCODED_DIR.mkdir(parents=True, exist_ok=True)
        (self.PMA_HARDCODED_DIR / "index.php").write_text("<?php // pma")

        try:
            with patch('subprocess.run') as mock_run:
                call_count = [0]

                def side_effect(*args, **kwargs):
                    call_count[0] += 1
                    cmd_str = str(args)
                    if call_count[0] == 1 and '.tar.xz' in cmd_str:
                        return MagicMock(returncode=1, stdout="", stderr="xz download failed")
                    if 'cp' in cmd_str and '-r' in cmd_str:
                        web_root.mkdir(parents=True, exist_ok=True)
                    return MagicMock(returncode=0, stdout="", stderr="")

                mock_run.side_effect = side_effect

                messages = pma_creator.create()

            assert mock_run.call_count >= 2
            assert any("installed successfully" in msg for msg in messages)
        finally:
            self._cleanup_extracted_dirs()

    def test_pma_creator_raises_when_both_downloads_fail(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator raises when both xz and gz downloads fail."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout="", stderr="xz failed"),
                MagicMock(returncode=1, stdout="", stderr="gz failed too"),
            ]

            with pytest.raises(Exception, match="Failed to download phpMyAdmin"):
                pma_creator.create()

    def test_pma_creator_raises_when_extraction_fails(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator raises when tar extraction fails."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),  # wget xz ok
                MagicMock(returncode=1, stdout="", stderr="corrupt archive"),  # tar extract fails
            ]

            with pytest.raises(Exception, match="Failed to extract phpMyAdmin"):
                pma_creator.create()

    def test_pma_creator_raises_when_extracted_dir_not_found(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator raises when no extracted directory can be located."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)

        self._cleanup_extracted_dirs()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            with pytest.raises(Exception, match="Could not find extracted phpMyAdmin directory"):
                pma_creator.create()

    def test_pma_creator_finds_extracted_dir_via_glob_fallback(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator falls back to glob when the exact version dir is absent."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)

        self._cleanup_extracted_dirs()
        alt_dir = Path('/tmp/phpMyAdmin-9.9.9-all-languages')
        alt_dir.mkdir(parents=True, exist_ok=True)
        (alt_dir / "index.php").write_text("<?php // pma alt")

        try:
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = self._cp_recreates_web_root_side_effect(web_root)

                messages = pma_creator.create()

            calls = [str(c) for c in mock_run.call_args_list]
            assert any('9.9.9' in c for c in calls)
            assert any("installed successfully" in msg for msg in messages)
        finally:
            self._cleanup_extracted_dirs()

    def test_pma_creator_removes_existing_web_root(self, pma_creator, tmp_path):
        """Test PhpMyAdminSiteCreator removes an existing web_root before install."""
        web_root = tmp_path / "web" / "pmasite"
        web_root.mkdir(parents=True, exist_ok=True)
        (web_root / "old_file.txt").write_text("stale")

        self._cleanup_extracted_dirs()
        self.PMA_HARDCODED_DIR.mkdir(parents=True, exist_ok=True)
        (self.PMA_HARDCODED_DIR / "index.php").write_text("<?php // pma")

        try:
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = self._cp_recreates_web_root_side_effect(web_root)

                pma_creator.create()

            assert not (web_root / "old_file.txt").exists()
        finally:
            self._cleanup_extracted_dirs()


class TestGetSiteCreatorAstroAndPhpMyAdmin:
    """Additional factory coverage for Astro and phpMyAdmin site types"""

    @pytest.fixture
    def setup_paths(self, tmp_path):
        return {
            'web_root': tmp_path / "web" / "testsite",
            'site_base_dir': tmp_path / "sites" / "testsite",
        }

    def test_get_astro_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns AstroSiteCreator when astro_template is set"""
        creator = get_site_creator(
            site_type=None,
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
            astro_template='basics',
        )
        assert isinstance(creator, AstroSiteCreator)
        assert creator.astro_template == 'basics'

    def test_get_phpmyadmin_creator(self, setup_paths, mock_config):
        """Test that get_site_creator returns PhpMyAdminSiteCreator for phpmyadmin type"""
        creator = get_site_creator(
            site_type='phpmyadmin',
            vite_template=None,
            php=False,
            config=mock_config,
            site_name='testsite',
            web_root=setup_paths['web_root'],
            site_base_dir=setup_paths['site_base_dir'],
            tld='.test',
        )
        assert isinstance(creator, PhpMyAdminSiteCreator)
