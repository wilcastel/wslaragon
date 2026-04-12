"""Tests for the MCP Server module"""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest


@pytest.fixture(autouse=True)
def mock_mcp_module():
    """Mock the MCP module before importing server"""
    mock_mcp = Mock()
    mock_mcp.resource = lambda *args, **kwargs: lambda f: f
    mock_mcp.tool = lambda *args, **kwargs: lambda f: f
    mock_mcp.prompt = lambda *args, **kwargs: lambda f: f
    
    mcp_module = Mock()
    mcp_module.server = Mock()
    mcp_module.server.fastmcp = Mock()
    mcp_module.server.fastmcp.FastMCP = Mock(return_value=mock_mcp)
    
    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.server"] = mcp_module.server
    sys.modules["mcp.server.fastmcp"] = mcp_module.server.fastmcp
    
    yield
    
    for mod in ["mcp", "mcp.server", "mcp.server.fastmcp"]:
        if mod in sys.modules:
            del sys.modules[mod]


class TestSitesFile:
    """Test suite for _sites_file helper"""

    def test_sites_file_returns_correct_path(self, mock_mcp_module):
        """Test _sites_file returns expected path structure"""
        from wslaragon.mcp.server import _sites_file
        
        result = _sites_file()
        
        assert result.name == "sites.json"
        assert ".wslaragon" in str(result)
        assert "sites" in str(result)

    @patch("wslaragon.mcp.server.Path.home")
    def test_sites_file_uses_home_directory(self, mock_home, mock_mcp_module):
        """Test _sites_file uses Path.home() correctly"""
        from wslaragon.mcp.server import _sites_file
        
        mock_home.return_value = Path("/home/testuser")
        
        result = _sites_file()
        
        assert str(result) == "/home/testuser/.wslaragon/sites/sites.json"


class TestLoadSites:
    """Test suite for _load_sites helper"""

    @patch("wslaragon.mcp.server._sites_file")
    def test_load_sites_returns_empty_dict_when_file_missing(self, mock_sites_file, mock_mcp_module):
        """Test _load_sites returns empty dict when sites.json doesn't exist"""
        from wslaragon.mcp.server import _load_sites
        
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_sites_file.return_value = mock_path
        
        result = _load_sites()
        
        assert result == {}

    @patch("wslaragon.mcp.server._sites_file")
    def test_load_sites_parses_existing_file(self, mock_sites_file, mock_mcp_module):
        """Test _load_sites parses valid sites.json"""
        from wslaragon.mcp.server import _load_sites
        
        sites_data = {
            "site1": {"name": "site1", "domain": "site1.test"},
            "site2": {"name": "site2", "domain": "site2.test"},
        }
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(sites_data)
        mock_sites_file.return_value = mock_path
        
        result = _load_sites()
        
        assert result == sites_data
        assert "site1" in result
        assert "site2" in result

    @patch("wslaragon.mcp.server._sites_file")
    def test_load_sites_handles_empty_file(self, mock_sites_file, mock_mcp_module):
        """Test _load_sites handles empty JSON file"""
        from wslaragon.mcp.server import _load_sites
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "{}"
        mock_sites_file.return_value = mock_path
        
        result = _load_sites()
        
        assert result == {}

    @patch("wslaragon.mcp.server._sites_file")
    def test_load_sites_handles_complex_site_data(self, mock_sites_file, mock_mcp_module):
        """Test _load_sites handles complex site configuration"""
        from wslaragon.mcp.server import _load_sites
        
        sites_data = {
            "mysite": {
                "name": "mysite",
                "domain": "mysite.test",
                "document_root": "/home/user/web/mysite",
                "php": True,
                "mysql": True,
                "ssl": True,
                "proxy_port": None,
                "site_type": "laravel",
            }
        }
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(sites_data)
        mock_sites_file.return_value = mock_path
        
        result = _load_sites()
        
        assert result["mysite"]["php"] is True
        assert result["mysite"]["mysql"] is True
        assert result["mysite"]["ssl"] is True


class TestRun:
    """Test suite for _run helper"""

    @patch("subprocess.run")
    def test_run_returns_success_with_output(self, mock_run, mock_mcp_module):
        """Test _run returns successful result"""
        from wslaragon.mcp.server import _run
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output text\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = _run(["echo", "test"])
        
        assert result["success"] is True
        assert result["stdout"] == "output text"
        assert result["stderr"] == ""

    @patch("subprocess.run")
    def test_run_returns_failure_with_error(self, mock_run, mock_mcp_module):
        """Test _run returns failed result"""
        from wslaragon.mcp.server import _run
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message\n"
        mock_run.return_value = mock_result
        
        result = _run(["false"])
        
        assert result["success"] is False
        assert result["stderr"] == "error message"
        assert result["stdout"] == ""

    @patch("subprocess.run")
    def test_run_strips_whitespace_from_output(self, mock_run, mock_mcp_module):
        """Test _run strips whitespace from stdout and stderr"""
        from wslaragon.mcp.server import _run
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  output with spaces  \n"
        mock_result.stderr = "  error  \n"
        mock_run.return_value = mock_result
        
        result = _run(["test"])
        
        assert result["stdout"] == "output with spaces"
        assert result["stderr"] == "error"

    @patch("subprocess.run")
    def test_run_handles_both_stdout_and_stderr(self, mock_run, mock_mcp_module):
        """Test _run captures both stdout and stderr"""
        from wslaragon.mcp.server import _run
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "stdout content\n"
        mock_result.stderr = "stderr content\n"
        mock_run.return_value = mock_result
        
        result = _run(["test"])
        
        assert result["stdout"] == "stdout content"
        assert result["stderr"] == "stderr content"


class TestServiceStatus:
    """Test suite for _service_status helper"""

    @patch("subprocess.run")
    def test_service_status_returns_active(self, mock_run, mock_mcp_module):
        """Test _service_status returns 'active' for running service"""
        from wslaragon.mcp.server import _service_status
        
        mock_result = MagicMock()
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result
        
        result = _service_status("nginx")
        
        assert result == "active"
        mock_run.assert_called_once_with(
            ["systemctl", "is-active", "nginx"],
            capture_output=True,
            text=True
        )

    @patch("subprocess.run")
    def test_service_status_returns_inactive(self, mock_run, mock_mcp_module):
        """Test _service_status returns 'inactive' for stopped service"""
        from wslaragon.mcp.server import _service_status
        
        mock_result = MagicMock()
        mock_result.stdout = "inactive\n"
        mock_run.return_value = mock_result
        
        result = _service_status("nginx")
        
        assert result == "inactive"

    @patch("subprocess.run")
    def test_service_status_returns_failed(self, mock_run, mock_mcp_module):
        """Test _service_status handles failed service status"""
        from wslaragon.mcp.server import _service_status
        
        mock_result = MagicMock()
        mock_result.stdout = "failed\n"
        mock_run.return_value = mock_result
        
        result = _service_status("nginx")
        
        assert result == "failed"

    @patch("subprocess.run")
    def test_service_status_strips_output(self, mock_run, mock_mcp_module):
        """Test _service_status strips output"""
        from wslaragon.mcp.server import _service_status
        
        mock_result = MagicMock()
        mock_result.stdout = "  active  \n"
        mock_run.return_value = mock_result
        
        result = _service_status("nginx")
        
        assert result == "active"


class TestResourceSites:
    """Test suite for resource_sites resource"""

    @patch("wslaragon.mcp.server._load_sites")
    def test_resource_sites_returns_empty_message(self, mock_load, mock_mcp_module):
        """Test resource_sites returns message when no sites exist"""
        from wslaragon.mcp.server import resource_sites
        
        mock_load.return_value = {}
        
        result = resource_sites()
        
        assert result == "No sites registered yet."

    @patch("wslaragon.mcp.server._load_sites")
    def test_resource_sites_formats_single_site(self, mock_load, mock_mcp_module):
        """Test resource_sites correctly formats a single site"""
        from wslaragon.mcp.server import resource_sites
        
        mock_load.return_value = {
            "mysite": {
                "name": "mysite",
                "domain": "mysite.test",
                "document_root": "/home/user/web/mysite",
                "php": True,
                "mysql": True,
                "ssl": True,
            }
        }
        
        result = resource_sites()
        
        assert "# WSLaragon sites" in result
        assert "## mysite" in result
        assert "Domain: mysite.test" in result
        assert "Document root: /home/user/web/mysite" in result
        assert "PHP: yes" in result
        assert "MySQL: yes" in result
        assert "SSL: yes" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_resource_sites_formats_multiple_sites(self, mock_load, mock_mcp_module):
        """Test resource_sites correctly formats multiple sites"""
        from wslaragon.mcp.server import resource_sites
        
        mock_load.return_value = {
            "site1": {"name": "site1", "php": False, "mysql": False, "ssl": True},
            "site2": {"name": "site2", "php": True, "mysql": True, "ssl": False},
        }
        
        result = resource_sites()
        
        assert "## site1" in result
        assert "## site2" in result
        assert "PHP: no" in result
        assert "MySQL: yes" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_resource_sites_includes_optional_fields(self, mock_load, mock_mcp_module):
        """Test resource_sites includes optional fields when present"""
        from wslaragon.mcp.server import resource_sites
        
        mock_load.return_value = {
            "nodeapp": {
                "name": "nodeapp",
                "php": False,
                "mysql": False,
                "ssl": True,
                "proxy_port": 3000,
                "site_type": "node",
            }
        }
        
        result = resource_sites()
        
        assert "Proxy port: 3000" in result
        assert "Type: node" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_resource_sites_handles_missing_optional_fields(self, mock_load, mock_mcp_module):
        """Test resource_sites handles sites with missing optional fields"""
        from wslaragon.mcp.server import resource_sites
        
        mock_load.return_value = {
            "simplesite": {
                "name": "simplesite",
            }
        }
        
        result = resource_sites()
        
        assert "Domain: simplesite.test" in result
        assert "PHP: no" in result
        assert "MySQL: no" in result
        assert "SSL: no" in result


class TestResourceServices:
    """Test suite for resource_services resource"""

    @patch("wslaragon.mcp.server._service_status")
    def test_resource_services_all_active(self, mock_status, mock_mcp_module):
        """Test resource_services shows all services as active"""
        from wslaragon.mcp.server import resource_services
        
        mock_status.return_value = "active"
        
        result = resource_services()
        
        assert "# Service status" in result
        assert "✓ nginx: active" in result
        assert "✓ php-fpm: active" in result
        assert "✓ mariadb: active" in result
        assert "✓ redis: active" in result

    @patch("wslaragon.mcp.server._service_status")
    def test_resource_services_mixed_status(self, mock_status, mock_mcp_module):
        """Test resource_services shows mixed service status"""
        from wslaragon.mcp.server import resource_services
        
        def side_effect(service):
            return {"nginx": "active", "php8.3-fpm": "inactive", "mariadb": "active", "redis-server": "failed"}[service]
        
        mock_status.side_effect = side_effect
        
        result = resource_services()
        
        assert "✓ nginx: active" in result
        assert "✗ php-fpm: inactive" in result
        assert "✓ mariadb: active" in result
        assert "✗ redis: failed" in result

    @patch("wslaragon.mcp.server._service_status")
    def test_resource_services_all_inactive(self, mock_status, mock_mcp_module):
        """Test resource_services shows all services as inactive"""
        from wslaragon.mcp.server import resource_services
        
        mock_status.return_value = "inactive"
        
        result = resource_services()
        
        assert "✗ nginx: inactive" in result
        assert "✗ php-fpm: inactive" in result


class TestResourceConfig:
    """Test suite for resource_config resource"""

    @patch("wslaragon.mcp.server.Path")
    def test_resource_config_returns_content(self, mock_path_class, mock_mcp_module):
        """Test resource_config returns config file content"""
        from wslaragon.mcp.server import resource_config
        
        mock_home = MagicMock()
        mock_config_dir = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        mock_config_file.read_text.return_value = "tld: .test\nphp_version: '8.3'\n"
        
        mock_home.__truediv__ = MagicMock(return_value=mock_config_dir)
        mock_config_dir.__truediv__ = MagicMock(return_value=mock_config_file)
        mock_path_class.home.return_value = mock_home
        
        result = resource_config()
        
        assert "Config file not found" in result or ".test" in result

    @patch("wslaragon.mcp.server.Path")
    def test_resource_config_returns_not_found(self, mock_path_class, mock_mcp_module):
        """Test resource_config returns not found message"""
        from wslaragon.mcp.server import resource_config
        
        mock_home = MagicMock()
        mock_config_dir = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        
        mock_home.__truediv__ = MagicMock(return_value=mock_config_dir)
        mock_config_dir.__truediv__ = MagicMock(return_value=mock_config_file)
        mock_path_class.home.return_value = mock_home
        
        result = resource_config()
        
        assert result == "Config file not found at ~/.wslaragon/config.yaml"


class TestListSites:
    """Test suite for list_sites tool"""

    @patch("wslaragon.mcp.server._load_sites")
    def test_list_sites_empty(self, mock_load, mock_mcp_module):
        """Test list_sites returns message when no sites exist"""
        from wslaragon.mcp.server import list_sites
        
        mock_load.return_value = {}
        
        result = list_sites()
        
        assert "No sites registered yet" in result
        assert "create_site" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_list_sites_single_site(self, mock_load, mock_mcp_module):
        """Test list_sites returns formatted single site"""
        from wslaragon.mcp.server import list_sites
        
        mock_load.return_value = {
            "mysite": {
                "name": "mysite",
                "domain": "mysite.test",
                "php": True,
                "ssl": True,
            }
        }
        
        result = list_sites()
        
        assert "mysite" in result
        assert "https://mysite.test" in result
        assert "[php]" in result
        assert "[ssl]" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_list_sites_multiple_sites(self, mock_load, mock_mcp_module):
        """Test list_sites returns formatted multiple sites"""
        from wslaragon.mcp.server import list_sites
        
        mock_load.return_value = {
            "site1": {"name": "site1", "php": True, "ssl": True},
            "site2": {"name": "site2", "php": False, "ssl": False, "proxy_port": 3000},
        }
        
        result = list_sites()
        
        assert "site1" in result
        assert "site2" in result
        assert "[php]" in result
        assert "[proxy:3000]" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_list_sites_proxy_port_formatting(self, mock_load, mock_mcp_module):
        """Test list_sites correctly formats proxy port sites"""
        from wslaragon.mcp.server import list_sites
        
        mock_load.return_value = {
            "nodeapp": {
                "name": "nodeapp",
                "php": False,
                "ssl": True,
                "proxy_port": 3000,
            }
        }
        
        result = list_sites()
        
        assert "[proxy:3000]" in result
        assert "[ssl]" in result

    @patch("wslaragon.mcp.server._load_sites")
    def test_list_sites_no_ssl_formatting(self, mock_load, mock_mcp_module):
        """Test list_sites correctly formats sites without SSL"""
        from wslaragon.mcp.server import list_sites
        
        mock_load.return_value = {
            "insecure": {
                "name": "insecure",
                "domain": "insecure.test",
                "php": True,
                "ssl": False,
            }
        }
        
        result = list_sites()
        
        assert "[no-ssl]" in result


class TestGetServicesStatus:
    """Test suite for get_services_status tool"""

    @patch("wslaragon.mcp.server.resource_services")
    def test_get_services_status_returns_resource(self, mock_resource, mock_mcp_module):
        """Test get_services_status returns resource_services result"""
        from wslaragon.mcp.server import get_services_status
        
        mock_resource.return_value = "Service status output"
        
        result = get_services_status()
        
        assert result == "Service status output"
        mock_resource.assert_called_once()


class TestCreateSite:
    """Test suite for create_site tool"""

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_success(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site returns success result"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "Site created", "stderr": ""}
        mock_load.return_value = {"testsite": {"domain": "testsite.test", "document_root": "/home/user/web/testsite"}}
        
        result = create_site("testsite")
        
        assert "created successfully" in result
        assert "testsite" in result
        mock_run.assert_called_once()

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_failure(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site returns failure message"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Error: site already exists"}
        mock_load.return_value = {}
        
        result = create_site("existing")
        
        assert "Failed to create site" in result
        assert "Error: site already exists" in result

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_html_type(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --html flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", site_type="html")
        
        call_args = mock_run.call_args[0][0]
        assert "--html" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_wordpress_type(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --wordpress flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", site_type="wordpress")
        
        call_args = mock_run.call_args[0][0]
        assert "--wordpress" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_node_type(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --node flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", site_type="node")
        
        call_args = mock_run.call_args[0][0]
        assert "--node" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_python_type(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --python flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", site_type="python")
        
        call_args = mock_run.call_args[0][0]
        assert "--python" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_laravel_version(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with Laravel version flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", laravel_version="12")
        
        call_args = mock_run.call_args[0][0]
        assert "--laravel=12" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_vite_template(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with Vite template flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", vite_template="react")
        
        call_args = mock_run.call_args[0][0]
        assert "--vite" in call_args
        assert "react" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_mysql(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --mysql flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", mysql=True)
        
        call_args = mock_run.call_args[0][0]
        assert "--mysql" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_without_ssl(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --no-ssl flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", ssl=False)
        
        call_args = mock_run.call_args[0][0]
        assert "--no-ssl" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_without_php(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --no-php flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", php=False)
        
        call_args = mock_run.call_args[0][0]
        assert "--no-php" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_proxy_port(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --proxy flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", proxy_port=3000)
        
        call_args = mock_run.call_args[0][0]
        assert "--proxy" in call_args
        assert "3000" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_postgres(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --postgres flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", db_type="postgres")
        
        call_args = mock_run.call_args[0][0]
        assert "--postgres" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_supabase(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --supabase flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", db_type="supabase")
        
        call_args = mock_run.call_args[0][0]
        assert "--supabase" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_public_dir(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --public flag"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", public_dir=True)
        
        call_args = mock_run.call_args[0][0]
        assert "--public" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_no_php_for_node_python(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site does not add --no-php for node/python"""
        from wslaragon.mcp.server import create_site
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}
        
        create_site("testsite", site_type="node", php=False)
        
        call_args = mock_run.call_args[0][0]
        assert "--no-php" not in call_args


class TestStartService:
    """Test suite for start_service tool"""

    @patch("wslaragon.mcp.server._run")
    def test_start_single_service_success(self, mock_run, mock_mcp_module):
        """Test start_service for single service success"""
        from wslaragon.mcp.server import start_service
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = start_service("nginx")
        
        assert "nginx: started" in result
        mock_run.assert_called_once_with(["wslaragon", "service", "start", "nginx"])

    @patch("wslaragon.mcp.server._run")
    def test_start_single_service_failure(self, mock_run, mock_mcp_module):
        """Test start_service for single service failure"""
        from wslaragon.mcp.server import start_service
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Permission denied"}
        
        result = start_service("nginx")
        
        assert "nginx: failed" in result
        assert "Permission denied" in result

    @patch("wslaragon.mcp.server._run")
    def test_start_all_services(self, mock_run, mock_mcp_module):
        """Test start_service for all services"""
        from wslaragon.mcp.server import start_service
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = start_service("all")
        
        assert "nginx: started" in result
        assert "php: started" in result
        assert "mysql: started" in result
        assert mock_run.call_count == 3

    @patch("wslaragon.mcp.server._run")
    def test_start_all_services_mixed_results(self, mock_run, mock_mcp_module):
        """Test start_service for all services with mixed results"""
        from wslaragon.mcp.server import start_service
        
        results = [
            {"success": True, "stdout": "", "stderr": ""},
            {"success": False, "stdout": "", "stderr": "Failed"},
            {"success": True, "stdout": "", "stderr": ""},
        ]
        mock_run.side_effect = results
        
        result = start_service("all")
        
        assert "nginx: started" in result
        assert "php: failed" in result
        assert "mysql: started" in result


class TestStopService:
    """Test suite for stop_service tool"""

    @patch("wslaragon.mcp.server._run")
    def test_stop_single_service_success(self, mock_run, mock_mcp_module):
        """Test stop_service for single service success"""
        from wslaragon.mcp.server import stop_service
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = stop_service("nginx")
        
        assert "nginx: stopped" in result
        mock_run.assert_called_once_with(["wslaragon", "service", "stop", "nginx"])

    @patch("wslaragon.mcp.server._run")
    def test_stop_single_service_failure(self, mock_run, mock_mcp_module):
        """Test stop_service for single service failure"""
        from wslaragon.mcp.server import stop_service
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Not running"}
        
        result = stop_service("nginx")
        
        assert "nginx: failed" in result
        assert "Not running" in result

    @patch("wslaragon.mcp.server._run")
    def test_stop_all_services(self, mock_run, mock_mcp_module):
        """Test stop_service for all services"""
        from wslaragon.mcp.server import stop_service
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = stop_service("all")
        
        assert "nginx: stopped" in result
        assert "php: stopped" in result
        assert "mysql: stopped" in result
        assert mock_run.call_count == 3


class TestRestartService:
    """Test suite for restart_service tool"""

    @patch("wslaragon.mcp.server._run")
    def test_restart_single_service_success(self, mock_run, mock_mcp_module):
        """Test restart_service for single service success"""
        from wslaragon.mcp.server import restart_service
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = restart_service("nginx")
        
        assert "nginx: restarted" in result
        mock_run.assert_called_once_with(["wslaragon", "service", "restart", "nginx"])

    @patch("wslaragon.mcp.server._run")
    def test_restart_single_service_failure(self, mock_run, mock_mcp_module):
        """Test restart_service for single service failure"""
        from wslaragon.mcp.server import restart_service
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Failed to restart"}
        
        result = restart_service("nginx")
        
        assert "nginx: failed" in result
        assert "Failed to restart" in result

    @patch("wslaragon.mcp.server._run")
    def test_restart_all_services(self, mock_run, mock_mcp_module):
        """Test restart_service for all services"""
        from wslaragon.mcp.server import restart_service
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = restart_service("all")
        
        assert "nginx: restarted" in result
        assert "php: restarted" in result
        assert "mysql: restarted" in result
        assert mock_run.call_count == 3


class TestGenerateSsl:
    """Test suite for generate_ssl tool"""

    @patch("wslaragon.mcp.server._run")
    def test_generate_ssl_success(self, mock_run, mock_mcp_module):
        """Test generate_ssl returns success message"""
        from wslaragon.mcp.server import generate_ssl
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = generate_ssl("myproject.test")
        
        assert "SSL certificate generated" in result
        assert "myproject.test" in result
        mock_run.assert_called_once_with(["wslaragon", "ssl", "generate", "myproject.test"])

    @patch("wslaragon.mcp.server._run")
    def test_generate_ssl_failure(self, mock_run, mock_mcp_module):
        """Test generate_ssl returns failure message"""
        from wslaragon.mcp.server import generate_ssl
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Certificate error"}
        
        result = generate_ssl("myproject.test")
        
        assert "SSL generation failed" in result
        assert "Certificate error" in result

    @patch("wslaragon.mcp.server._run")
    def test_generate_ssl_failure_with_stdout(self, mock_run, mock_mcp_module):
        """Test generate_ssl returns failure with stdout fallback"""
        from wslaragon.mcp.server import generate_ssl
        
        mock_run.return_value = {"success": False, "stdout": "mkcert not found", "stderr": ""}
        
        result = generate_ssl("test.test")
        
        assert "mkcert not found" in result


class TestAgentInit:
    """Test suite for agent_init tool"""

    @patch("wslaragon.mcp.server._run")
    def test_agent_init_success_with_path_flag(self, mock_run, mock_mcp_module):
        """Test agent_init returns success message"""
        from wslaragon.mcp.server import agent_init
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = agent_init("/home/user/project", preset="laravel")
        
        assert ".agent structure initialised" in result
        assert "/home/user/project" in result
        assert "laravel" in result

    @patch("wslaragon.mcp.server._run")
    def test_agent_init_uses_default_preset(self, mock_run, mock_mcp_module):
        """Test agent_init uses default preset"""
        from wslaragon.mcp.server import agent_init
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = agent_init("/home/user/project")
        
        assert "default" in result
        mock_run.assert_called_once_with(["wslaragon", "agent", "init", "default", "--path", "/home/user/project"])

    @patch("wslaragon.mcp.server._run")
    @patch("subprocess.run")
    def test_agent_init_fallback_on_failure(self, mock_subprocess, mock_run, mock_mcp_module):
        """Test agent_init falls back to cwd-based approach"""
        from wslaragon.mcp.server import agent_init
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": ""}
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        result = agent_init("/home/user/project", preset="wordpress")
        
        assert ".agent structure initialised" in result
        mock_subprocess.assert_called_once()

    @patch("wslaragon.mcp.server._run")
    @patch("subprocess.run")
    def test_agent_init_complete_failure(self, mock_subprocess, mock_run, mock_mcp_module):
        """Test agent_init returns failure after both attempts"""
        from wslaragon.mcp.server import agent_init
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": ""}
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Agent init failed"
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        result = agent_init("/home/user/project")
        
        assert "agent init failed" in result


class TestRunDoctor:
    """Test suite for run_doctor tool"""

    @patch("wslaragon.mcp.server._run")
    def test_run_doctor_returns_stdout(self, mock_run, mock_mcp_module):
        """Test run_doctor returns stdout output"""
        from wslaragon.mcp.server import run_doctor
        
        mock_run.return_value = {"success": True, "stdout": "All checks passed", "stderr": ""}
        
        result = run_doctor()
        
        assert result == "All checks passed"

    @patch("wslaragon.mcp.server._run")
    def test_run_doctor_returns_stderr_on_failure(self, mock_run, mock_mcp_module):
        """Test run_doctor returns stderr when available"""
        from wslaragon.mcp.server import run_doctor
        
        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Issues found"}
        
        result = run_doctor()
        
        assert result == "Issues found"

    @patch("wslaragon.mcp.server._run")
    def test_run_doctor_returns_fallback_message(self, mock_run, mock_mcp_module):
        """Test run_doctor returns fallback message when no output"""
        from wslaragon.mcp.server import run_doctor
        
        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        
        result = run_doctor()
        
        assert "Doctor finished" in result


class TestNewProjectPrompt:
    """Test suite for new_project prompt"""

    def test_new_project_returns_formatted_prompt(self, mock_mcp_module):
        """Test new_project returns properly formatted prompt"""
        from wslaragon.mcp.server import new_project
        
        result = new_project("myapp")
        
        assert "myapp" in result
        assert "**laravel**" in result
        assert "Database needed: yes" in result
        assert "get_services_status" in result
        assert "create_site" in result

    def test_new_project_custom_stack(self, mock_mcp_module):
        """Test new_project with custom stack"""
        from wslaragon.mcp.server import new_project
        
        result = new_project("myapp", stack="wordpress")
        
        assert "**wordpress**" in result

    def test_new_project_without_database(self, mock_mcp_module):
        """Test new_project without database"""
        from wslaragon.mcp.server import new_project
        
        result = new_project("myapp", with_database=False)
        
        assert "Database needed: no" in result

    def test_new_project_includes_next_steps(self, mock_mcp_module):
        """Test new_project includes next steps guidance"""
        from wslaragon.mcp.server import new_project
        
        result = new_project("myapp", stack="laravel")
        
        assert "composer install" in result
        assert "npm install" in result