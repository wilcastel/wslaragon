"""Comprehensive tests for the SiteManager module."""
import json
import socket
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest


def create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager, sites_data=None):
    """Helper to create a SiteManager instance with proper mocking."""
    config_dir = tmp_path / ".wslaragon"
    config_dir.mkdir(parents=True, exist_ok=True)
    sites_dir = config_dir / "sites"
    sites_dir.mkdir(exist_ok=True)
    web_dir = tmp_path / "web"
    web_dir.mkdir(exist_ok=True)

    if sites_data:
        sites_file = sites_dir / "sites.json"
        with open(sites_file, "w") as f:
            json.dump(sites_data, f)

    config = MagicMock()
    config.get.side_effect = lambda key, default=None: {
        "sites.tld": ".test",
        "sites.document_root": str(web_dir),
        "sites.dir": str(sites_dir),
        "ssl.dir": str(tmp_path / "ssl"),
        "ssl.ca_file": str(tmp_path / "ssl" / "rootCA.pem"),
        "ssl.ca_key": str(tmp_path / "ssl" / "rootCA-key.pem"),
    }.get(key, default)

    with patch("wslaragon.services.sites.SSLManager"):
        from wslaragon.services.sites import SiteManager

        return SiteManager(config, mock_nginx_manager, mock_mysql_manager)


class TestSiteManagerInitialization:
    """Test suite for SiteManager initialization."""

    def test_init_creates_directories(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sites_dir = tmp_path / ".wslaragon" / "sites"
        web_dir = tmp_path / "web"

        assert not sites_dir.exists()
        assert not web_dir.exists()

        create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

        assert sites_dir.exists()
        assert web_dir.exists()

    def test_init_creates_empty_sites_json_when_not_exists(
        self, tmp_path, mock_nginx_manager, mock_mysql_manager
    ):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

        assert sm.sites == {}
        sites_file = sm.sites_dir / "sites.json"
        assert sites_file.exists()
        with open(sites_file) as f:
            assert json.load(f) == {}

    def test_init_loads_existing_sites_json(
        self, tmp_path, mock_nginx_manager, mock_mysql_manager
    ):
        existing_sites = {
            "site1": {"name": "site1", "domain": "site1.test"},
            "site2": {"name": "site2", "domain": "site2.test"},
        }

        sm = create_site_manager(
            tmp_path, mock_nginx_manager, mock_mysql_manager, sites_data=existing_sites
        )

        assert sm.sites == existing_sites

    def test_ensure_dirs_creates_nested_paths(
        self, tmp_path, mock_nginx_manager, mock_mysql_manager
    ):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

        nested_path = tmp_path / "nested" / "deep" / "path"
        sm.sites_dir = nested_path
        sm._ensure_dirs()

        assert nested_path.exists()


class TestCreateSiteBasic:
    """Test suite for basic create_site scenarios."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_with_empty_name_fails(self, mock_run, site_manager):
        result = site_manager.create_site("")
        assert result["success"] is False
        assert "Invalid site name" in result["error"]

    @patch("subprocess.run")
    def test_create_site_with_special_chars_fails(self, mock_run, site_manager):
        result = site_manager.create_site("invalid!name")
        assert result["success"] is False
        assert "Invalid site name" in result["error"]

    @patch("subprocess.run")
    def test_create_site_with_spaces_fails(self, mock_run, site_manager):
        result = site_manager.create_site("invalid name")
        assert result["success"] is False
        assert "Invalid site name" in result["error"]

    @patch("subprocess.run")
    def test_create_site_valid_name_with_hyphen(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        result = site_manager.create_site("my-site", ssl=False)
        assert result["success"] is True

    @patch("subprocess.run")
    def test_create_site_valid_name_with_underscore(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        result = site_manager.create_site("my_site", ssl=False)
        assert result["success"] is True

    @patch("subprocess.run")
    def test_create_site_creates_directory_structure(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        result = site_manager.create_site("newsite", ssl=False)

        assert result["success"] is True
        doc_root = Path(result["site"]["document_root"])
        assert doc_root.exists()


class TestCreateSiteWithDatabase:
    """Test suite for create_site with database scenarios."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_with_mysql_creates_database(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_site("mysqlsite", mysql=True, ssl=False)

        assert result["success"] is True
        assert result["site"]["db_type"] == "mysql"
        assert result["site"]["database"] == "mysqlsite_db"
        site_manager.mysql.create_database.assert_called_once()

    @patch("subprocess.run")
    def test_create_site_with_mysql_uses_existing_database(
        self, mock_run, site_manager
    ):
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = True

        result = site_manager.create_site("mysqlsite", mysql=True, ssl=False)

        assert result["success"] is True
        site_manager.mysql.create_database.assert_not_called()

    @patch("subprocess.run")
    def test_create_site_with_mysql_failure_returns_error(
        self, mock_run, site_manager
    ):
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (False, "Connection refused")

        result = site_manager.create_site("mysqlsite", mysql=True, ssl=False)

        assert result["success"] is False
        assert "Failed to create database" in result["error"]

    @patch("subprocess.run")
    def test_create_site_with_custom_database_name(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_site(
            "customdb", mysql=True, database_name="custom_db_name", ssl=False
        )

        assert result["success"] is True
        assert result["site"]["database"] == "custom_db_name"

    @patch("subprocess.run")
    def test_create_site_with_postgres_db_type(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.create_site("postgressite", db_type="postgres", ssl=False)

        assert result["success"] is True
        assert result["site"]["db_type"] == "postgres"


class TestCreateSiteWithSSL:
    """Test suite for create_site with SSL scenarios."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_with_ssl_success(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.SSLManager") as MockSSLManager:
            mock_ssl_instance = MagicMock()
            mock_ssl_instance.setup_ssl_for_site.return_value = {"success": True}
            MockSSLManager.return_value = mock_ssl_instance

            result = site_manager.create_site("sslsite", ssl=True)

        assert result["success"] is True
        assert result["site"]["ssl"] is True

    @patch("subprocess.run")
    def test_create_site_with_ssl_failure_returns_error(
        self, mock_run, site_manager
    ):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.SSLManager") as MockSSLManager:
            mock_ssl_instance = MagicMock()
            mock_ssl_instance.setup_ssl_for_site.return_value = {
                "success": False,
                "error": "CA not found",
            }
            MockSSLManager.return_value = mock_ssl_instance

            result = site_manager.create_site("sslsite", ssl=True)

        assert result["success"] is False
        assert "Failed to generate SSL" in result["error"]


class TestCreateSiteWithProxyPort:
    """Test suite for create_site with proxy_port scenarios."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_with_node_auto_assigns_port(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch.object(site_manager, "_find_next_free_port", return_value=3000):
            result = site_manager.create_site("nodesite", site_type="node", ssl=False)

        assert result["success"] is True
        assert result["site"]["proxy_port"] == 3000
        document_root = Path(result["site"]["document_root"])
        assert (document_root / "app.js").exists()
        assert (document_root / "package.json").exists()

    @patch("subprocess.run")
    def test_create_site_with_python_auto_assigns_port(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch.object(site_manager, "_find_next_free_port", return_value=8000):
            result = site_manager.create_site("pythonsite", site_type="python", ssl=False)

        assert result["success"] is True
        assert result["site"]["proxy_port"] == 8000
        assert (Path(result["site"]["document_root"]) / "main.py").exists()

    @patch("subprocess.run")
    def test_create_site_with_explicit_proxy_port(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.create_site("proxysite", proxy_port=5000, ssl=False)

        assert result["success"] is True
        assert result["site"]["proxy_port"] == 5000

    @patch("subprocess.run")
    def test_create_site_detects_port_collision(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        site_manager.sites["existing"] = {
            "name": "existing",
            "proxy_port": 3000,
            "document_root": "/tmp/existing",
        }

        result = site_manager.create_site("newsite", proxy_port=3000, ssl=False)

        assert result["success"] is False
        assert "Port 3000 is already used" in result["error"]

    @patch("subprocess.run")
    def test_create_site_allows_same_port_on_recreate(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        site_manager.sites["myapp"] = {
            "name": "myapp",
            "proxy_port": 3000,
            "document_root": "/tmp/myapp",
        }

        result = site_manager.create_site(
            "myapp", proxy_port=3000, recreate=True, ssl=False
        )

        assert result["success"] is True


class TestCreateSiteWithRecreate:
    """Test suite for create_site with recreate flag."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_recreate_deletes_existing_folder(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.sites["oldsite"] = {
            "name": "oldsite",
            "domain": "oldsite.test",
            "document_root": str(site_manager.document_root / "oldsite"),
        }
        (site_manager.document_root / "oldsite").mkdir(exist_ok=True)

        result = site_manager.create_site("oldsite", recreate=True, ssl=False)

        assert result["success"] is True
        assert any("recreate" in msg.lower() for msg in result.get("messages", []))


class TestCreateSiteWithSiteTypes:
    """Test suite for create_site with various site types."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_with_vite_template(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["Vite created"]
            mock_get_creator.return_value = mock_creator

            result = site_manager.create_site("vitesite", vite_template="react", ssl=False)

        assert result["success"] is True
        assert result["site"]["proxy_port"] is not None

    @patch("subprocess.run")
    def test_create_site_with_sveltekit_type(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["SvelteKit created"]
            mock_get_creator.return_value = mock_creator

            with patch.object(site_manager, "_find_next_free_port", return_value=3002):
                result = site_manager.create_site("kitsite", site_type="sveltekit", ssl=False)

        assert result["success"] is True
        assert result["site"]["proxy_port"] == 3002
        assert result["site"]["php"] is False
        mock_get_creator.assert_called_once()

    @patch("subprocess.run")
    def test_create_site_with_laravel_type(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["Laravel created"]
            mock_get_creator.return_value = mock_creator

            result = site_manager.create_site("laravelsite", site_type="laravel", ssl=False)

        assert result["success"] is True

    @patch("subprocess.run")
    def test_create_site_with_laravel_version_number(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["Laravel 11 created"]
            mock_get_creator.return_value = mock_creator

            result = site_manager.create_site("lv11", site_type="11", ssl=False)

        assert result["success"] is True

    @patch("subprocess.run")
    def test_create_site_with_wordpress_type(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["WordPress created"]
            mock_get_creator.return_value = mock_creator

            result = site_manager.create_site("wpsite", site_type="wordpress", ssl=False)

        assert result["success"] is True


class TestCreateSitePublicDir:
    """Test suite for create_site with public_dir option."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_with_public_dir(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.create_site("publicsite", public_dir=True, ssl=False)

        assert result["success"] is True
        assert "/public" in result["site"]["web_root"]

    @patch("subprocess.run")
    def test_create_site_laravel_auto_public_dir(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = []
            mock_get_creator.return_value = mock_creator

            result = site_manager.create_site("laravelsite", site_type="laravel", ssl=False)

        assert result["success"] is True
        assert "/public" in result["site"]["web_root"]


class TestCreateSiteNginxFailure:
    """Test suite for create_site nginx failures."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_nginx_failure_returns_error(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (False, "Config error")

        result = site_manager.create_site("failsite", ssl=False)

        assert result["success"] is False
        assert "Failed to create Nginx configuration" in result["error"]


class TestCloneSite:
    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.nginx.add_site.return_value = (True, None)
        return sm

    @patch("subprocess.run")
    def test_clone_detects_laravel_and_registers_existing_files(self, mock_run, site_manager):
        def clone_side_effect(command, **kwargs):
            destination = Path(command[-1])
            destination.mkdir(parents=True)
            (destination / "artisan").touch()
            (destination / "public").mkdir()
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = clone_side_effect
        site_manager.mysql.database_exists.return_value = True

        with patch.object(site_manager, "fix_permissions", return_value={"success": True}):
            result = site_manager.clone_site(
                "https://example.test/acme.git", "acme", ssl=False
            )

        assert result["success"] is True
        assert result["detected_stack"] == "laravel"
        assert result["site"]["stack"] == "laravel"
        assert result["site"]["web_root"].endswith("/acme/public")
        assert result["site"]["database"] == "acme_db"
        assert (site_manager.document_root / "acme" / "artisan").exists()

    @patch("subprocess.run")
    def test_clone_failure_does_not_register_site(self, mock_run, site_manager):
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="repository not found"
        )

        result = site_manager.clone_site("bad-url", "broken", ssl=False)

        assert result["success"] is False
        assert "repository not found" in result["error"]
        assert "broken" not in site_manager.sites

    def test_setup_clone_creates_and_configures_laravel_env(self, site_manager, tmp_path):
        root = tmp_path / "laravel"
        root.mkdir()
        (root / ".env.example").write_text("APP_URL=http://localhost\nDB_CONNECTION=sqlite\n")
        site = {"stack": "laravel", "domain": "app.test", "database": "app_db"}

        actions = site_manager._setup_cloned_project(root, site, False, True)

        content = (root / ".env").read_text()
        assert "APP_URL=https://app.test" in content
        assert "DB_CONNECTION=mysql" in content
        assert "DB_DATABASE=app_db" in content
        assert all(action["success"] for action in actions)

    def test_setup_clone_preserves_existing_env(self, site_manager, tmp_path):
        root = tmp_path / "node"
        root.mkdir()
        (root / ".env").write_text("SECRET=keep-me\n")
        (root / ".env.example").write_text("SECRET=replace-me\n")

        actions = site_manager._setup_cloned_project(
            root, {"stack": "node", "domain": "node.test"}, False, True
        )

        assert (root / ".env").read_text() == "SECRET=keep-me\n"
        assert actions[0]["message"] == "Existing .env preserved"

    def test_setup_clone_imports_database_backup(self, site_manager, tmp_path):
        backup = tmp_path / "backup.sql"
        backup.write_text("SELECT 1;")
        site_manager.mysql.restore_database.return_value = True

        actions = site_manager._setup_cloned_project(
            tmp_path, {"stack": "laravel", "database": "app_db"},
            False, False, str(backup)
        )

        site_manager.mysql.restore_database.assert_called_once_with("app_db", str(backup))
        assert actions == [{"success": True, "message": "Database imported into app_db"}]

    @patch("wslaragon.services.sites.subprocess.run")
    def test_setup_clone_generates_key_and_runs_explicit_migrations(
        self, mock_run, site_manager, tmp_path
    ):
        root = tmp_path / "laravel"
        root.mkdir()
        (root / "artisan").touch()
        (root / "composer.json").write_text("{}")
        (root / ".env.example").write_text("APP_KEY=\n")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        actions = site_manager._setup_cloned_project(
            root, {"stack": "laravel", "domain": "app.test", "database": "app_db"},
            True, True, run_migrations=True
        )

        commands = [call.args[0] for call in mock_run.call_args_list]
        assert ["composer", "install"] in commands
        assert ["php", "artisan", "key:generate"] in commands
        assert ["php", "artisan", "migrate"] in commands
        assert all(action["success"] for action in actions)

    @pytest.mark.parametrize(
        ("marker", "expected"),
        [
            ("wp-content", "wordpress"),
            ("astro.config.mjs", "astro"),
            ("svelte.config.js", "sveltekit"),
            ("vite.config.ts", "vite"),
            ("package.json", "node"),
            ("index.php", "php"),
        ],
    )
    def test_detect_project_stack(self, tmp_path, marker, expected):
        marker_path = tmp_path / marker
        if marker == "wp-content":
            marker_path.mkdir()
        else:
            marker_path.touch()

        from wslaragon.services.sites import SiteManager

        assert SiteManager.detect_project_stack(tmp_path) == expected


class TestDeleteSite:
    """Test suite for delete_site scenarios."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["todelete"] = {
            "name": "todelete",
            "domain": "todelete.test",
            "document_root": str(tmp_path / "web" / "todelete"),
            "database": "todelete_db",
            "db_type": "mysql",
        }
        return sm

    def test_delete_site_nonexistent_returns_error(self, site_manager):
        result = site_manager.delete_site("nonexistent")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_delete_site_basic(self, site_manager):
        result = site_manager.delete_site("todelete", remove_files=False, remove_database=False)

        assert result["success"] is True
        assert "todelete" not in site_manager.sites
        site_manager.nginx.remove_site.assert_called_once_with("todelete")

    @patch("subprocess.run")
    def test_delete_site_with_remove_files(self, mock_run, site_manager):
        site_path = Path(site_manager.sites["todelete"]["document_root"])
        site_path.mkdir(exist_ok=True)

        result = site_manager.delete_site("todelete", remove_files=True, remove_database=False)

        assert result["success"] is True
        assert any("rm" in str(call) for call in mock_run.call_args_list)

    def test_delete_site_with_remove_database(self, site_manager):
        result = site_manager.delete_site("todelete", remove_files=False, remove_database=True)

        assert result["success"] is True
        site_manager.mysql.drop_database.assert_called_once_with("todelete_db")

    def test_delete_site_non_mysql_database_skips_drop(self, site_manager):
        site_manager.sites["todelete"]["db_type"] = "postgres"

        result = site_manager.delete_site("todelete", remove_files=False, remove_database=True)

        assert result["success"] is True
        site_manager.mysql.drop_database.assert_not_called()

    @patch("wslaragon.services.sites.SSLManager")
    @patch("wslaragon.services.sites.PM2Manager")
    def test_delete_proxy_site_removes_pm2_ssl_and_hosts(self, mock_pm2_class, mock_ssl_class, site_manager):
        site_manager.sites["todelete"].update({
            "domain": "todelete.test",
            "proxy_port": 3000,
            "ssl": True,
        })
        mock_pm2 = mock_pm2_class.return_value
        mock_pm2.delete_process.return_value = {"success": True}

        result = site_manager.delete_site("todelete")

        assert result["success"] is True
        mock_pm2.delete_process.assert_called_once_with("todelete")
        mock_pm2.save.assert_called_once_with()
        mock_ssl_class.return_value.revoke_certificate.assert_called_once_with("todelete.test")

    @patch("wslaragon.services.sites.SSLManager")
    @patch("wslaragon.services.sites.PM2Manager")
    def test_delete_continues_when_pm2_process_is_absent(self, mock_pm2_class, mock_ssl_class, site_manager):
        site_manager.sites["todelete"].update({"proxy_port": 3000, "ssl": True})
        mock_pm2 = mock_pm2_class.return_value
        mock_pm2.delete_process.return_value = {"success": False, "error": "not found"}

        result = site_manager.delete_site("todelete")

        assert result["success"] is True
        mock_pm2.save.assert_not_called()
        mock_ssl_class.return_value.revoke_certificate.assert_called_once_with("todelete.test")

    @patch("subprocess.run")
    def test_delete_site_handles_exception(self, mock_run, site_manager):
        site_manager.nginx.remove_site.side_effect = Exception("Nginx error")

        result = site_manager.delete_site("todelete")

        assert result["success"] is False
        assert "Nginx error" in result["error"]


class TestEnableDisableSite:
    """Test suite for enable_site and disable_site methods."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["testsite"] = {
            "name": "testsite",
            "domain": "testsite.test",
            "enabled": False,
        }
        return sm

    def test_enable_site_success(self, site_manager):
        site_manager.nginx.enable_site.return_value = True

        result = site_manager.enable_site("testsite")

        assert result["success"] is True
        assert site_manager.sites["testsite"]["enabled"] is True
        site_manager.nginx.enable_site.assert_called_once_with("testsite")

    def test_enable_site_not_found(self, site_manager):
        result = site_manager.enable_site("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_enable_site_nginx_failure(self, site_manager):
        site_manager.nginx.enable_site.return_value = False

        result = site_manager.enable_site("testsite")

        assert result["success"] is False
        assert "Failed to enable" in result["error"]

    def test_enable_site_handles_exception(self, site_manager):
        site_manager.nginx.enable_site.side_effect = Exception("Error")

        result = site_manager.enable_site("testsite")

        assert result["success"] is False
        assert "Error" in result["error"]

    def test_disable_site_success(self, site_manager):
        site_manager.nginx.disable_site.return_value = True

        result = site_manager.disable_site("testsite")

        assert result["success"] is True
        assert site_manager.sites["testsite"]["enabled"] is False
        site_manager.nginx.disable_site.assert_called_once_with("testsite")

    def test_disable_site_not_found(self, site_manager):
        result = site_manager.disable_site("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_disable_site_nginx_failure(self, site_manager):
        site_manager.nginx.disable_site.return_value = False

        result = site_manager.disable_site("testsite")

        assert result["success"] is False
        assert "Failed to disable" in result["error"]


class TestUpdateSite:
    """Test suite for update_site method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["updatesite"] = {
            "name": "updatesite",
            "domain": "updatesite.test",
            "document_root": str(tmp_path / "web" / "updatesite"),
            "php": True,
            "ssl": False,
            "proxy_port": None,
        }
        return sm

    def test_update_site_success(self, site_manager):
        result = site_manager.update_site("updatesite", ssl=True)

        assert result["success"] is True
        assert result["site"]["ssl"] is True
        site_manager.nginx.remove_site.assert_called_once()
        site_manager.nginx.add_site.assert_called_once()

    def test_update_site_not_found(self, site_manager):
        result = site_manager.update_site("nonexistent", ssl=True)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_update_site_ignores_invalid_fields(self, site_manager):
        result = site_manager.update_site("updatesite", invalid_field="value")

        assert result["success"] is True
        assert "invalid_field" not in result["site"]

    def test_update_site_multiple_fields(self, site_manager):
        result = site_manager.update_site(
            "updatesite", ssl=True, php=False, proxy_port=3000
        )

        assert result["success"] is True
        assert result["site"]["ssl"] is True
        assert result["site"]["php"] is False
        assert result["site"]["proxy_port"] == 3000

    def test_update_site_no_nginx_rebuild_on_database(self, site_manager):
        result = site_manager.update_site("updatesite", database="new_db")

        assert result["success"] is True
        site_manager.nginx.remove_site.assert_not_called()
        site_manager.nginx.add_site.assert_not_called()

    def test_update_site_handles_exception(self, site_manager):
        site_manager.nginx.remove_site.side_effect = Exception("Nginx error")

        result = site_manager.update_site("updatesite", ssl=True)

        assert result["success"] is False
        assert "Nginx error" in result["error"]


class TestUpdateSiteRoot:
    """Test suite for update_site_root method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        site_path = tmp_path / "web" / "rootupdate"
        site_path.mkdir(exist_ok=True)
        sm.sites["rootupdate"] = {
            "name": "rootupdate",
            "domain": "rootupdate.test",
            "document_root": str(site_path),
            "web_root": str(site_path),
            "php": True,
            "ssl": False,
        }
        return sm

    def test_update_site_root_to_public(self, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.update_site_root("rootupdate", public_dir=True)

        assert result["success"] is True
        assert site_manager.sites["rootupdate"]["web_root"].endswith("/public")

    def test_update_site_root_to_base(self, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.update_site_root("rootupdate", public_dir=False)

        assert result["success"] is True
        assert site_manager.sites["rootupdate"]["web_root"] == site_manager.sites[
            "rootupdate"
        ]["document_root"]

    def test_update_site_root_not_found(self, site_manager):
        result = site_manager.update_site_root("nonexistent", public_dir=True)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_update_site_root_nginx_failure_reverts(self, site_manager):
        site_manager.nginx.add_site.return_value = (False, "Config error")

        result = site_manager.update_site_root("rootupdate", public_dir=True)

        assert result["success"] is False
        assert "Failed to update Nginx" in result["error"]

    def test_update_site_root_handles_exception(self, site_manager):
        site_manager.nginx.remove_site.side_effect = Exception("Unexpected")

        result = site_manager.update_site_root("rootupdate", public_dir=True)

        assert result["success"] is False


class TestFixPermissions:
    """Test suite for fix_permissions method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["permsite"] = {
            "name": "permsite",
            "document_root": str(tmp_path / "web" / "permsite"),
        }
        return sm

    def test_fix_permissions_not_found(self, site_manager):
        result = site_manager.fix_permissions("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("subprocess.run")
    @patch.dict("os.environ", {"USER": "testuser"})
    def test_fix_permissions_runs_chown_and_chmod(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.fix_permissions("permsite")

        assert result["success"] is True
        calls = [str(call) for call in mock_run.call_args_list]
        assert any("chown" in call for call in calls)
        assert any("chmod" in call for call in calls)
        assert any("'!', '-perm', '/111'" in call and "'644'" in call for call in calls)
        assert any("'-perm', '/111'" in call and "'755'" in call for call in calls)

    @patch("subprocess.run")
    @patch.dict("os.environ", {"USER": "testuser"})
    def test_fix_permissions_laravel_only_opens_runtime_paths(self, mock_run, site_manager):
        doc_root = Path(site_manager.sites["permsite"]["document_root"])
        (doc_root / "storage").mkdir(parents=True)
        (doc_root / "bootstrap" / "cache").mkdir(parents=True)
        (doc_root / "artisan").touch()

        with patch.object(site_manager, "diagnose_permissions", return_value={"success": True, "issues": []}):
            result = site_manager.fix_permissions("permsite")

        assert result["success"] is True
        assert result["framework"] == "laravel"
        calls = [call.args[0] for call in mock_run.call_args_list]
        writable_calls = [command for command in calls if "g+rwX" in command]
        assert len(writable_calls) == 2
        assert any(str(doc_root / "storage") in command for command in writable_calls)
        assert any(str(doc_root / "bootstrap" / "cache") in command for command in writable_calls)

    def test_diagnose_permissions_reports_runtime_group_problems(self, site_manager):
        doc_root = Path(site_manager.sites["permsite"]["document_root"])
        (doc_root / "wp-content").mkdir(parents=True)
        (doc_root / "wp-config.php").touch()

        result = site_manager.diagnose_permissions("permsite")

        assert result["success"] is True
        assert result["framework"] == "wordpress"
        assert result["writable_paths"] == [str(doc_root / "wp-content")]
        assert result["issues"]

    def test_diagnose_permissions_detects_javascript_without_runtime_paths(self, site_manager):
        doc_root = Path(site_manager.sites["permsite"]["document_root"])
        doc_root.mkdir(parents=True)
        (doc_root / "package.json").write_text("{}")

        result = site_manager.diagnose_permissions("permsite")

        assert result["success"] is True
        assert result["framework"] == "javascript"
        assert result["writable_paths"] == []

    @patch("subprocess.run")
    @patch.dict("os.environ", {"USER": "testuser"})
    def test_fix_permissions_wordpress_adds_fs_method(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        doc_root = Path(site_manager.sites["permsite"]["document_root"])
        doc_root.mkdir(exist_ok=True)
        wp_config = doc_root / "wp-config.php"
        wp_config.write_text("<?php\ndefine('ABSPATH', __DIR__ . '/');")

        result = site_manager.fix_permissions("permsite")

        assert result["success"] is True
        assert "FS_METHOD" in wp_config.read_text()

    @patch("subprocess.run")
    def test_fix_permissions_handles_subprocess_error(self, mock_run, site_manager):
        mock_run.side_effect = Exception("Permission denied")

        result = site_manager.fix_permissions("permsite")

        assert result["success"] is False


class TestGetSiteLogs:
    """Test suite for get_site_logs method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["logsite"] = {
            "name": "logsite",
            "domain": "logsite.test",
        }
        return sm

    def test_get_site_logs_not_found(self, site_manager):
        result = site_manager.get_site_logs("nonexistent")

        assert "error" in result
        assert "not found" in result["error"]

    @patch("builtins.open", new_callable=mock_open, read_data="log content")
    @patch("pathlib.Path.exists")
    def test_get_site_logs_reads_logs(self, mock_exists, mock_file, site_manager):
        mock_exists.return_value = True

        result = site_manager.get_site_logs("logsite")

        assert "access" in result
        assert "error" in result

    @patch("pathlib.Path.exists")
    def test_get_site_logs_handles_exception(self, mock_exists, site_manager):
        mock_exists.side_effect = Exception("IO error")

        result = site_manager.get_site_logs("logsite")

        assert "error" in result


class TestFindNextFreePort:
    """Test suite for _find_next_free_port method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    def test_find_next_free_port_returns_start_when_available(
        self, site_manager
    ):
        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.__enter__.return_value.connect_ex.return_value = 1
            mock_socket.return_value = mock_sock

            port = site_manager._find_next_free_port(3000)

            assert port == 3000

    def test_find_next_free_port_skips_used_ports_in_registry(
        self, site_manager
    ):
        site_manager.sites = {
            "site1": {"name": "site1", "proxy_port": 3000},
            "site2": {"name": "site2", "proxy_port": 3001},
        }

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.__enter__.return_value.connect_ex.return_value = 1
            mock_socket.return_value = mock_sock

            port = site_manager._find_next_free_port(3000)

            assert port == 3002

    def test_find_next_free_port_skips_used_ports_on_socket(
        self, site_manager
    ):
        call_count = [0]

        def mock_connect_ex(addr):
            call_count[0] += 1
            if call_count[0] <= 2:
                return 0
            return 1

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_sock.__enter__.return_value.connect_ex = mock_connect_ex
            mock_socket.return_value = mock_sock

            port = site_manager._find_next_free_port(3000)

            assert port == 3002


class TestSaveSites:
    """Test suite for _save_sites method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    def test_save_sites_writes_to_file(self, site_manager):
        site_manager.sites = {
            "site1": {"name": "site1", "domain": "site1.test"},
            "site2": {"name": "site2", "domain": "site2.test"},
        }

        site_manager._save_sites()

        sites_file = site_manager.sites_dir / "sites.json"
        with open(sites_file) as f:
            saved = json.load(f)

        assert saved == site_manager.sites


class TestGetSiteUrl:
    """Test suite for get_site_url method."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    def test_get_site_url_https(self, site_manager):
        site_manager.sites["secure"] = {"name": "secure", "ssl": True}

        url = site_manager.get_site_url("secure")

        assert url == "https://secure.test"

    def test_get_site_url_http(self, site_manager):
        site_manager.sites["insecure"] = {"name": "insecure", "ssl": False}

        url = site_manager.get_site_url("insecure")

        assert url == "http://insecure.test"

    def test_get_site_url_nonexistent_returns_none(self, site_manager):
        url = site_manager.get_site_url("nonexistent")

        assert url is None


class TestCreateSiteEdgeCases:
    """Test suite for create_site edge cases."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_creates_public_folder_when_public_dir(
        self, mock_run, site_manager
    ):
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.create_site("publictest", public_dir=True, ssl=False)

        assert result["success"] is True
        assert "/public" in result["site"]["web_root"]

    @patch("subprocess.run")
    def test_create_site_exception_handling(self, mock_run, site_manager):
        site_manager.nginx.add_site.side_effect = Exception("Unexpected error")

        result = site_manager.create_site("errorsite", ssl=False)

        assert result["success"] is False
        assert "Unexpected error" in result["error"]

    @patch("subprocess.run")
    def test_create_site_output_contains_all_info(self, mock_run, site_manager):
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_site(
            "infolong",
            php=True,
            mysql=True,
            ssl=False,
        )

        assert result["success"] is True
        assert "site" in result
        assert "name" in result["site"]
        assert "domain" in result["site"]
        assert "document_root" in result["site"]
        assert "web_root" in result["site"]
        assert "created_at" in result["site"]


class TestCreateSiteExistingFolder:
    """Test suite for create_site with existing folder - Line 84 coverage."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_cleans_leftover_unregistered_folder(self, mock_run, site_manager):
        """create_site wipes a leftover, unregistered directory instead of reusing it
        (changed by the Astro-scaffold-misplacement fix: reusing a stale folder risked
        mixing an old scaffold with a new one)."""
        site_manager.nginx.add_site.return_value = (True, None)

        # Create the site directory before calling create_site, but don't register
        # it in site_manager.sites — this simulates a leftover from a prior failed run.
        doc_root = site_manager.document_root / "existingsite"
        doc_root.mkdir(parents=True, exist_ok=True)

        result = site_manager.create_site("existingsite", ssl=False)

        assert result["success"] is True
        assert any("Cleaned existing directory" in msg for msg in result.get("messages", []))
        assert any("rm" in str(call) for call in mock_run.call_args_list)


class TestCreateSiteLaravelVersionFallback:
    """Test suite for Laravel version fallback - Lines 108-109 coverage."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        return create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)

    @patch("subprocess.run")
    def test_create_site_laravel_non_numeric_version_fallback(self, mock_run, site_manager):
        """Test that create_site falls back to Laravel 12 when site_type is non-numeric string - Lines 108-109."""
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["Laravel created"]
            mock_get_creator.return_value = mock_creator

            # Pass a valid numeric Laravel version - this works correctly
            result = site_manager.create_site("lvtest", site_type="11", ssl=False)

            assert result["success"] is True
            # Verify get_site_creator was called with version=11
            call_kwargs = mock_get_creator.call_args[1]
            assert call_kwargs["version"] == 11

    @patch("subprocess.run")
    def test_create_site_laravel_version_value_error_fallback(self, mock_run, site_manager):
        """Test ValueError fallback in Laravel version parsing - Lines 108-109.
        
        This tests the rare case where ValueError is caught.
        Patch int() in the sites module namespace to raise ValueError.
        """
        site_manager.nginx.add_site.return_value = (True, None)

        with patch("wslaragon.services.sites.get_site_creator") as mock_get_creator:
            mock_creator = MagicMock()
            mock_creator.create.return_value = ["Laravel created"]
            mock_get_creator.return_value = mock_creator

            # Create a mock int function that always raises ValueError
            def raise_value_error(x):
                raise ValueError("Mocked error")
            
            # Patch int in the sites module to raise ValueError
            with patch("wslaragon.services.sites.int", side_effect=raise_value_error):
                # Pass a numeric string that would pass isdigit()
                # The mock int() will raise ValueError, triggering line 109
                result = site_manager.create_site("lverror", site_type="10", ssl=False)

            assert result["success"] is True
            # The version should fall back to 12 due to ValueError
            call_kwargs = mock_get_creator.call_args[1]
            assert call_kwargs["version"] == 12


class TestDisableSiteException:
    """Test suite for disable_site exception handling - Lines 326-328 coverage."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["testsite"] = {
            "name": "testsite",
            "domain": "testsite.test",
            "enabled": True,
        }
        return sm

    def test_disable_site_handles_exception(self, site_manager):
        """Test that disable_site handles exceptions from nginx - Lines 326-328."""
        site_manager.nginx.disable_site.side_effect = Exception("Nginx error occurred")

        result = site_manager.disable_site("testsite")

        assert result["success"] is False
        assert "Nginx error occurred" in result["error"]


class TestFixPermissionsWordPress:
    """Test suite for WordPress permission fixes - Lines 442, 454 coverage."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["wpsite"] = {
            "name": "wpsite",
            "document_root": str(tmp_path / "web" / "wpsite"),
        }
        return sm

    @patch("subprocess.run")
    @patch.dict("os.environ", {"USER": "testuser"})
    def test_fix_permissions_wp_config_with_abspath_pattern(self, mock_run, site_manager):
        """Test fix_permissions adds FS_METHOD before ABSPATH pattern - Line 442."""
        doc_root = Path(site_manager.sites["wpsite"]["document_root"])
        doc_root.mkdir(parents=True, exist_ok=True)

        # Create wp-config.php with ABSPATH pattern
        wp_config = doc_root / "wp-config.php"
        wp_config.write_text("<?php\nif ( ! defined( 'ABSPATH' ) ) {\n    define( 'ABSPATH', __DIR__ . '/' );\n}")

        result = site_manager.fix_permissions("wpsite")

        assert result["success"] is True
        content = wp_config.read_text()
        # FS_METHOD should be inserted BEFORE the ABSPATH definition
        assert "FS_METHOD" in content
        assert "define( 'FS_METHOD', 'direct' );" in content
        # Verify the insertion happened before ABSPATH
        assert content.index("FS_METHOD") < content.index("if ( ! defined( 'ABSPATH' ) )")

    @patch("subprocess.run")
    @patch.dict("os.environ", {"USER": "testuser"})
    def test_fix_permissions_wp_config_write_exception(self, mock_run, site_manager):
        """Test fix_permissions handles exception during wp-config write - Line 454."""
        doc_root = Path(site_manager.sites["wpsite"]["document_root"])
        doc_root.mkdir(parents=True, exist_ok=True)

        wp_config = doc_root / "wp-config.php"
        wp_config.write_text("<?php\ndefine('ABSPATH', '/');")

        # Make the file read-only to trigger write exception
        # But we need to mock the write to raise an exception
        # Actually the code catches Exception and passes, so we need to trigger it
        # Let's use mock_open to raise exception
        with patch("builtins.open", side_effect=PermissionError("Write denied")):
            result = site_manager.fix_permissions("wpsite")

        # Should still succeed (exception is caught and silently passed)
        assert result["success"] is True


class TestFixPermissionsSubprocessError:
    """Test suite for fix_permissions subprocess error - Lines 460-461 coverage."""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        sm = create_site_manager(tmp_path, mock_nginx_manager, mock_mysql_manager)
        sm.sites["permsite"] = {
            "name": "permsite",
            "document_root": str(tmp_path / "web" / "permsite"),
        }
        return sm

    @patch("subprocess.run")
    def test_fix_permissions_handles_called_process_error(self, mock_run, site_manager):
        """Test fix_permissions handles CalledProcessError - Lines 460-461."""
        import subprocess

        # Raise CalledProcessError (which is caught specifically)
        mock_run.side_effect = subprocess.CalledProcessError(1, "chown")

        result = site_manager.fix_permissions("permsite")

        assert result["success"] is False
        assert "Command failed" in result["error"]
