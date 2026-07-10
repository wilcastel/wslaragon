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
        mock_run.assert_called_once_with(
            ["wslaragon", "agent", "init", "--preset", "default", "--path", "/home/user/project"]
        )

    @patch("wslaragon.mcp.server._run")
    def test_agent_init_returns_failure(self, mock_run, mock_mcp_module):
        """Test agent_init reports failure from the CLI without a broken positional fallback"""
        from wslaragon.mcp.server import agent_init

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "Agent init failed"}

        result = agent_init("/home/user/project")

        assert "agent init failed" in result
        mock_run.assert_called_once_with(
            ["wslaragon", "agent", "init", "--preset", "default", "--path", "/home/user/project"]
        )


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


class TestMain:
    """Test suite for main entry point"""

    def test_main_calls_mcp_run(self, mock_mcp_module):
        """Test main() calls mcp.run()"""
        from wslaragon.mcp.server import mcp

        # Import the module to get the main function
        import wslaragon.mcp.server as server_module

        # The test verifies that main() exists and calls mcp.run()
        assert hasattr(server_module, 'main'), "main function should exist"

        # Verify mcp has run method
        assert hasattr(mcp, 'run'), "mcp object should have run method"

    @patch("wslaragon.mcp.server.mcp")
    def test_main_calls_run_correctly(self, mock_mcp, mock_mcp_module):
        """Test that main() correctly invokes mcp.run()"""
        from wslaragon.mcp.server import main

        main()

        mock_mcp.run.assert_called_once()


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


class TestRunInteractive:
    """Test suite for _run_interactive helper"""

    @patch("subprocess.run")
    def test_run_interactive_returns_success(self, mock_run, mock_mcp_module):
        """Test _run_interactive returns successful result and forwards input"""
        from wslaragon.mcp.server import _run_interactive

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "done\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = _run_interactive(["wslaragon", "site", "delete", "foo"], "y\ny\n")

        assert result["success"] is True
        assert result["stdout"] == "done"
        mock_run.assert_called_once_with(
            ["wslaragon", "site", "delete", "foo"],
            input="y\ny\n",
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_run_interactive_returns_failure(self, mock_run, mock_mcp_module):
        """Test _run_interactive returns failed result"""
        from wslaragon.mcp.server import _run_interactive

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error\n"
        mock_run.return_value = mock_result

        result = _run_interactive(["wslaragon", "mysql", "drop-db", "foo"], "y\n")

        assert result["success"] is False
        assert result["stderr"] == "error"


class TestCreateSiteExtras:
    """Test suite for create_site's phpmyadmin and astro_template support"""

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_phpmyadmin_type(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --phpmyadmin flag"""
        from wslaragon.mcp.server import create_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}

        create_site("testsite", site_type="phpmyadmin")

        call_args = mock_run.call_args[0][0]
        assert "--phpmyadmin" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_with_astro_template(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site with --astro=<template> flag"""
        from wslaragon.mcp.server import create_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}

        create_site("testsite", astro_template="blog")

        call_args = mock_run.call_args[0][0]
        assert "--astro=blog" in call_args

    @patch("wslaragon.mcp.server._run")
    @patch("wslaragon.mcp.server._load_sites")
    def test_create_site_without_astro_template(self, mock_load, mock_run, mock_mcp_module):
        """Test create_site omits --astro when astro_template is not given"""
        from wslaragon.mcp.server import create_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}
        mock_load.return_value = {"testsite": {}}

        create_site("testsite")

        call_args = mock_run.call_args[0][0]
        assert not any(arg.startswith("--astro") for arg in call_args)


class TestCreateHeadlessSite:
    """Test suite for create_headless_site tool"""

    @patch("wslaragon.mcp.server._run")
    def test_create_headless_site_success(self, mock_run, mock_mcp_module):
        """Test create_headless_site returns success message with both URLs"""
        from wslaragon.mcp.server import create_headless_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = create_headless_site("misitio", backend="wordpress", frontend="astro")

        assert "created successfully" in result
        assert "https://misitio.test" in result
        assert "https://api.misitio.test" in result
        call_args = mock_run.call_args[0][0]
        assert call_args == [
            "wslaragon", "site", "create",
            "--headless", "--backend=wordpress", "--frontend=astro", "--url=misitio",
        ]

    @patch("wslaragon.mcp.server._run")
    def test_create_headless_site_failure(self, mock_run, mock_mcp_module):
        """Test create_headless_site returns failure message"""
        from wslaragon.mcp.server import create_headless_site

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "already exists"}

        result = create_headless_site("misitio", backend="laravel", frontend="sveltekit")

        assert "Failed to create headless site" in result
        assert "already exists" in result

    @patch("wslaragon.mcp.server._run")
    def test_create_headless_site_no_ssl(self, mock_run, mock_mcp_module):
        """Test create_headless_site with ssl=False adds --no-ssl"""
        from wslaragon.mcp.server import create_headless_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        create_headless_site("misitio", backend="wordpress", frontend="astro", ssl=False)

        call_args = mock_run.call_args[0][0]
        assert "--no-ssl" in call_args

    @patch("wslaragon.mcp.server._run")
    def test_create_headless_site_with_database(self, mock_run, mock_mcp_module):
        """Test create_headless_site with custom database name"""
        from wslaragon.mcp.server import create_headless_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        create_headless_site("misitio", backend="wordpress", frontend="astro", database="customdb")

        call_args = mock_run.call_args[0][0]
        assert "--database" in call_args
        assert "customdb" in call_args

    @patch("wslaragon.mcp.server._run")
    def test_create_headless_site_with_force(self, mock_run, mock_mcp_module):
        """Test create_headless_site with force=True adds --force"""
        from wslaragon.mcp.server import create_headless_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        create_headless_site("misitio", backend="wordpress", frontend="astro", force=True)

        call_args = mock_run.call_args[0][0]
        assert "--force" in call_args


class TestDeleteSite:
    """Test suite for delete_site tool"""

    @patch("wslaragon.mcp.server._run_interactive")
    def test_delete_site_success_remove_files(self, mock_run_interactive, mock_mcp_module):
        """Test delete_site with remove_files=True confirms both prompts"""
        from wslaragon.mcp.server import delete_site

        mock_run_interactive.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = delete_site("oldsite")

        assert "deleted successfully" in result
        mock_run_interactive.assert_called_once_with(
            ["wslaragon", "site", "delete", "oldsite", "--keep-database"],
            "y\ny\n",
        )

    @patch("wslaragon.mcp.server._run_interactive")
    def test_delete_site_keep_files(self, mock_run_interactive, mock_mcp_module):
        """Test delete_site with remove_files=False sends 'n' for the files prompt"""
        from wslaragon.mcp.server import delete_site

        mock_run_interactive.return_value = {"success": True, "stdout": "", "stderr": ""}

        delete_site("oldsite", remove_files=False)

        call_args = mock_run_interactive.call_args[0]
        assert call_args[1] == "n\ny\n"

    @patch("wslaragon.mcp.server._run_interactive")
    def test_delete_site_remove_database(self, mock_run_interactive, mock_mcp_module):
        """Test delete_site with remove_database=True passes --remove-database"""
        from wslaragon.mcp.server import delete_site

        mock_run_interactive.return_value = {"success": True, "stdout": "", "stderr": ""}

        delete_site("oldsite", remove_database=True)

        call_args = mock_run_interactive.call_args[0][0]
        assert "--remove-database" in call_args

    @patch("wslaragon.mcp.server._run_interactive")
    def test_delete_site_failure(self, mock_run_interactive, mock_mcp_module):
        """Test delete_site returns failure message"""
        from wslaragon.mcp.server import delete_site

        mock_run_interactive.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = delete_site("missing")

        assert "Failed to delete site" in result
        assert "not found" in result


class TestEnableDisableSite:
    """Test suite for enable_site and disable_site tools"""

    @patch("wslaragon.mcp.server._run")
    def test_enable_site_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import enable_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = enable_site("mysite")

        assert "enabled" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "enable", "mysite"])

    @patch("wslaragon.mcp.server._run")
    def test_enable_site_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import enable_site

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = enable_site("mysite")

        assert "Failed to enable site" in result

    @patch("wslaragon.mcp.server._run")
    def test_disable_site_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import disable_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = disable_site("mysite")

        assert "disabled" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "disable", "mysite"])

    @patch("wslaragon.mcp.server._run")
    def test_disable_site_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import disable_site

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = disable_site("mysite")

        assert "Failed to disable site" in result


class TestSetSitePublic:
    """Test suite for set_site_public tool"""

    @patch("wslaragon.mcp.server._run")
    def test_set_site_public_enable(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_site_public

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = set_site_public("mysite")

        assert "public/" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "public", "mysite", "--enable"])

    @patch("wslaragon.mcp.server._run")
    def test_set_site_public_disable(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_site_public

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = set_site_public("mysite", enable=False)

        assert "./" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "public", "mysite", "--disable"])

    @patch("wslaragon.mcp.server._run")
    def test_set_site_public_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_site_public

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = set_site_public("mysite")

        assert "Failed to update site" in result


class TestFixSitePermissions:
    """Test suite for fix_site_permissions tool"""

    @patch("wslaragon.mcp.server._run")
    def test_fix_site_permissions_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import fix_site_permissions

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = fix_site_permissions("mysite")

        assert "Permissions fixed" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "fix-permissions", "mysite"])

    @patch("wslaragon.mcp.server._run")
    def test_fix_site_permissions_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import fix_site_permissions

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "denied"}

        result = fix_site_permissions("mysite")

        assert "Failed to fix permissions" in result


class TestExportImportSite:
    """Test suite for export_site and import_site tools"""

    @patch("wslaragon.mcp.server._run")
    def test_export_site_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import export_site

        mock_run.return_value = {"success": True, "stdout": "File: backup.tar.gz", "stderr": ""}

        result = export_site("mysite")

        assert "exported successfully" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "export", "mysite"])

    @patch("wslaragon.mcp.server._run")
    def test_export_site_with_output(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import export_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        export_site("mysite", output="/tmp/backup.tar.gz")

        call_args = mock_run.call_args[0][0]
        assert "--output" in call_args
        assert "/tmp/backup.tar.gz" in call_args

    @patch("wslaragon.mcp.server._run")
    def test_export_site_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import export_site

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = export_site("missing")

        assert "Failed to export site" in result

    @patch("wslaragon.mcp.server._run")
    def test_import_site_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import import_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = import_site("backup.tar.gz")

        assert "imported successfully" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "import", "backup.tar.gz"])

    @patch("wslaragon.mcp.server._run")
    def test_import_site_with_name(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import import_site

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        import_site("backup.tar.gz", name="newsite")

        call_args = mock_run.call_args[0][0]
        assert "--name" in call_args
        assert "newsite" in call_args

    @patch("wslaragon.mcp.server._run")
    def test_import_site_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import import_site

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "corrupt archive"}

        result = import_site("bad.tar.gz")

        assert "Failed to import site" in result


class TestEnableSiteSsl:
    """Test suite for enable_site_ssl tool"""

    @patch("wslaragon.mcp.server._run")
    def test_enable_site_ssl_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import enable_site_ssl

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = enable_site_ssl("mysite")

        assert "SSL enabled" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "ssl", "mysite"])

    @patch("wslaragon.mcp.server._run")
    def test_enable_site_ssl_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import enable_site_ssl

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "already enabled"}

        result = enable_site_ssl("mysite")

        assert "Failed to enable SSL" in result


class TestApiProxies:
    """Test suite for add_api_proxy, remove_api_proxy and list_api_proxies tools"""

    @patch("wslaragon.mcp.server._run")
    def test_add_api_proxy_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import add_api_proxy

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = add_api_proxy("dash", "/api", "https://api.dash.test")

        assert "API proxy added" in result
        mock_run.assert_called_once_with(
            ["wslaragon", "site", "api", "add", "dash", "/api", "https://api.dash.test"]
        )

    @patch("wslaragon.mcp.server._run")
    def test_add_api_proxy_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import add_api_proxy

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = add_api_proxy("dash", "/api", "https://api.dash.test")

        assert "Failed to add API proxy" in result

    @patch("wslaragon.mcp.server._run")
    def test_remove_api_proxy_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import remove_api_proxy

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = remove_api_proxy("dash", "/api")

        assert "API proxy removed" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "api", "remove", "dash", "/api"])

    @patch("wslaragon.mcp.server._run")
    def test_remove_api_proxy_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import remove_api_proxy

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = remove_api_proxy("dash", "/api")

        assert "Failed to remove API proxy" in result

    @patch("wslaragon.mcp.server._run")
    def test_list_api_proxies_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_api_proxies

        mock_run.return_value = {"success": True, "stdout": "/api -> https://api.dash.test", "stderr": ""}

        result = list_api_proxies("dash")

        assert "https://api.dash.test" in result
        mock_run.assert_called_once_with(["wslaragon", "site", "api", "list", "dash"])

    @patch("wslaragon.mcp.server._run")
    def test_list_api_proxies_empty(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_api_proxies

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_api_proxies("dash")

        assert "No API proxies configured" in result

    @patch("wslaragon.mcp.server._run")
    def test_list_api_proxies_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_api_proxies

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "site not found"}

        result = list_api_proxies("missing")

        assert "Failed to list API proxies" in result


class TestPhpTools:
    """Test suite for PHP management tools"""

    @patch("wslaragon.mcp.server._run")
    def test_list_php_versions_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_php_versions

        mock_run.return_value = {"success": True, "stdout": "8.3\n8.1", "stderr": ""}

        result = list_php_versions()

        assert "8.3" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "versions"])

    @patch("wslaragon.mcp.server._run")
    def test_list_php_versions_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_php_versions

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_php_versions()

        assert "No PHP versions found" in result

    @patch("wslaragon.mcp.server._run")
    def test_switch_php_version_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import switch_php_version

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = switch_php_version("8.3")

        assert "Switched to PHP 8.3" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "switch", "8.3"])

    @patch("wslaragon.mcp.server._run")
    def test_switch_php_version_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import switch_php_version

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not installed"}

        result = switch_php_version("9.9")

        assert "Failed to switch to PHP 9.9" in result

    @patch("wslaragon.mcp.server._run")
    def test_list_php_extensions_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_php_extensions

        mock_run.return_value = {"success": True, "stdout": "gd\nredis", "stderr": ""}

        result = list_php_extensions()

        assert "gd" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "extensions"])

    @patch("wslaragon.mcp.server._run")
    def test_list_php_extensions_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_php_extensions

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_php_extensions()

        assert "No PHP extensions found" in result

    @patch("wslaragon.mcp.server._run")
    def test_enable_php_extension_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import enable_php_extension

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = enable_php_extension("gd")

        assert "enabled" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "enable-ext", "gd"])

    @patch("wslaragon.mcp.server._run")
    def test_enable_php_extension_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import enable_php_extension

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = enable_php_extension("bogus")

        assert "Failed to enable PHP extension" in result

    @patch("wslaragon.mcp.server._run")
    def test_disable_php_extension_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import disable_php_extension

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = disable_php_extension("gd")

        assert "disabled" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "disable-ext", "gd"])

    @patch("wslaragon.mcp.server._run")
    def test_disable_php_extension_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import disable_php_extension

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = disable_php_extension("bogus")

        assert "Failed to disable PHP extension" in result

    @patch("wslaragon.mcp.server._run")
    def test_list_php_config_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_php_config

        mock_run.return_value = {"success": True, "stdout": "memory_limit = 256M", "stderr": ""}

        result = list_php_config()

        assert "memory_limit" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "config", "list"])

    @patch("wslaragon.mcp.server._run")
    def test_list_php_config_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_php_config

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_php_config()

        assert "No PHP configuration found" in result

    @patch("wslaragon.mcp.server._run")
    def test_get_php_config_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import get_php_config

        mock_run.return_value = {"success": True, "stdout": "memory_limit = 256M", "stderr": ""}

        result = get_php_config("memory_limit")

        assert "256M" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "config", "get", "memory_limit"])

    @patch("wslaragon.mcp.server._run")
    def test_get_php_config_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import get_php_config

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = get_php_config("bogus_key")

        assert "not found" in result

    @patch("wslaragon.mcp.server._run")
    def test_set_php_config_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_php_config

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = set_php_config("memory_limit", "256M")

        assert "updated to '256M'" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "config", "set", "memory_limit", "256M"])

    @patch("wslaragon.mcp.server._run")
    def test_set_php_config_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_php_config

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "denied"}

        result = set_php_config("memory_limit", "256M")

        assert "Failed to update PHP setting" in result

    @patch("wslaragon.mcp.server._run")
    def test_set_php_upload_limit_default(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_php_upload_limit

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = set_php_upload_limit()

        assert "512M" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "upload-limit", "512M"])

    @patch("wslaragon.mcp.server._run")
    def test_set_php_upload_limit_custom(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_php_upload_limit

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = set_php_upload_limit("1G")

        assert "1G" in result
        mock_run.assert_called_once_with(["wslaragon", "php", "upload-limit", "1G"])

    @patch("wslaragon.mcp.server._run")
    def test_set_php_upload_limit_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_php_upload_limit

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "no php installed"}

        result = set_php_upload_limit()

        assert "Failed to set upload limits" in result


class TestMysqlTools:
    """Test suite for MySQL management tools"""

    @patch("wslaragon.mcp.server._run")
    def test_list_mysql_databases_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_mysql_databases

        mock_run.return_value = {"success": True, "stdout": "site1\nsite2", "stderr": ""}

        result = list_mysql_databases()

        assert "site1" in result
        mock_run.assert_called_once_with(["wslaragon", "mysql", "databases"])

    @patch("wslaragon.mcp.server._run")
    def test_list_mysql_databases_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_mysql_databases

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_mysql_databases()

        assert "No MySQL databases found" in result

    @patch("wslaragon.mcp.server._run")
    def test_create_mysql_database_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import create_mysql_database

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = create_mysql_database("mydb")

        assert "created" in result
        mock_run.assert_called_once_with(["wslaragon", "mysql", "create-db", "mydb"])

    @patch("wslaragon.mcp.server._run")
    def test_create_mysql_database_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import create_mysql_database

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "already exists"}

        result = create_mysql_database("mydb")

        assert "Failed to create MySQL database" in result

    @patch("wslaragon.mcp.server._run_interactive")
    def test_drop_mysql_database_success(self, mock_run_interactive, mock_mcp_module):
        from wslaragon.mcp.server import drop_mysql_database

        mock_run_interactive.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = drop_mysql_database("mydb")

        assert "dropped" in result
        mock_run_interactive.assert_called_once_with(
            ["wslaragon", "mysql", "drop-db", "mydb"], "y\n"
        )

    @patch("wslaragon.mcp.server._run_interactive")
    def test_drop_mysql_database_failure(self, mock_run_interactive, mock_mcp_module):
        from wslaragon.mcp.server import drop_mysql_database

        mock_run_interactive.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = drop_mysql_database("missing")

        assert "Failed to drop MySQL database" in result


class TestNginxConfigTools:
    """Test suite for Nginx configuration tools"""

    @patch("wslaragon.mcp.server._run")
    def test_list_nginx_config_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_nginx_config

        mock_run.return_value = {"success": True, "stdout": "client_max_body_size = 128M", "stderr": ""}

        result = list_nginx_config()

        assert "client_max_body_size" in result
        mock_run.assert_called_once_with(["wslaragon", "nginx", "config", "list"])

    @patch("wslaragon.mcp.server._run")
    def test_list_nginx_config_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_nginx_config

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_nginx_config()

        assert "No Nginx configuration found" in result

    @patch("wslaragon.mcp.server._run")
    def test_set_nginx_config_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_nginx_config

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = set_nginx_config("client_max_body_size", "256M")

        assert "updated to '256M'" in result
        mock_run.assert_called_once_with(
            ["wslaragon", "nginx", "config", "set", "client_max_body_size", "256M"]
        )

    @patch("wslaragon.mcp.server._run")
    def test_set_nginx_config_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import set_nginx_config

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "invalid key"}

        result = set_nginx_config("bogus", "1")

        assert "Failed to update Nginx setting" in result


class TestSslManagementTools:
    """Test suite for setup_ssl, delete_ssl_cert and list_ssl_certs tools"""

    @patch("wslaragon.mcp.server._run")
    def test_setup_ssl_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import setup_ssl

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = setup_ssl()

        assert "root CA created" in result
        mock_run.assert_called_once_with(["wslaragon", "ssl", "setup"])

    @patch("wslaragon.mcp.server._run")
    def test_setup_ssl_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import setup_ssl

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "permission denied"}

        result = setup_ssl()

        assert "Failed to create SSL root CA" in result

    @patch("wslaragon.mcp.server._run_interactive")
    def test_delete_ssl_cert_success(self, mock_run_interactive, mock_mcp_module):
        from wslaragon.mcp.server import delete_ssl_cert

        mock_run_interactive.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = delete_ssl_cert("myproject.test")

        assert "deleted" in result
        mock_run_interactive.assert_called_once_with(
            ["wslaragon", "ssl", "delete", "myproject.test"], "y\n"
        )

    @patch("wslaragon.mcp.server._run_interactive")
    def test_delete_ssl_cert_failure(self, mock_run_interactive, mock_mcp_module):
        from wslaragon.mcp.server import delete_ssl_cert

        mock_run_interactive.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = delete_ssl_cert("missing.test")

        assert "Failed to delete SSL certificate" in result

    @patch("wslaragon.mcp.server._run")
    def test_list_ssl_certs_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_ssl_certs

        mock_run.return_value = {"success": True, "stdout": "myproject.test", "stderr": ""}

        result = list_ssl_certs()

        assert "myproject.test" in result
        mock_run.assert_called_once_with(["wslaragon", "ssl", "list"])

    @patch("wslaragon.mcp.server._run")
    def test_list_ssl_certs_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_ssl_certs

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_ssl_certs()

        assert "No SSL certificates found" in result


class TestNodeProcessTools:
    """Test suite for Node.js/PM2 process management tools"""

    @patch("wslaragon.mcp.server._run")
    def test_list_node_processes_stdout(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_node_processes

        mock_run.return_value = {"success": True, "stdout": "myapp online", "stderr": ""}

        result = list_node_processes()

        assert "myapp" in result
        mock_run.assert_called_once_with(["wslaragon", "node", "list"])

    @patch("wslaragon.mcp.server._run")
    def test_list_node_processes_fallback(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import list_node_processes

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = list_node_processes()

        assert "No running Node processes found" in result

    @patch("wslaragon.mcp.server._run")
    def test_start_node_process_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import start_node_process

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = start_node_process("myapp")

        assert "started" in result
        mock_run.assert_called_once_with(["wslaragon", "node", "start", "myapp"])

    @patch("wslaragon.mcp.server._run")
    def test_start_node_process_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import start_node_process

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "no entry point"}

        result = start_node_process("myapp")

        assert "Failed to start process" in result

    @patch("wslaragon.mcp.server._run")
    def test_stop_node_process_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import stop_node_process

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = stop_node_process("myapp")

        assert "stopped" in result
        mock_run.assert_called_once_with(["wslaragon", "node", "stop", "myapp"])

    @patch("wslaragon.mcp.server._run")
    def test_stop_node_process_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import stop_node_process

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not running"}

        result = stop_node_process("myapp")

        assert "Failed to stop process" in result

    @patch("wslaragon.mcp.server._run")
    def test_restart_node_process_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import restart_node_process

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = restart_node_process("myapp")

        assert "restarted" in result
        mock_run.assert_called_once_with(["wslaragon", "node", "restart", "myapp"])

    @patch("wslaragon.mcp.server._run")
    def test_restart_node_process_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import restart_node_process

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = restart_node_process("myapp")

        assert "Failed to restart process" in result

    @patch("wslaragon.mcp.server._run")
    def test_delete_node_process_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import delete_node_process

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = delete_node_process("myapp")

        assert "deleted" in result
        mock_run.assert_called_once_with(["wslaragon", "node", "delete", "myapp"])

    @patch("wslaragon.mcp.server._run")
    def test_delete_node_process_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import delete_node_process

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "not found"}

        result = delete_node_process("myapp")

        assert "Failed to delete process" in result


class TestImportSkill:
    """Test suite for import_skill tool"""

    @patch("wslaragon.mcp.server._run")
    def test_import_skill_success(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import import_skill

        mock_run.return_value = {"success": True, "stdout": "", "stderr": ""}

        result = import_skill("https://example.com/skill.zip")

        assert "imported successfully" in result
        mock_run.assert_called_once_with(
            ["wslaragon", "agent", "import", "https://example.com/skill.zip"]
        )

    @patch("wslaragon.mcp.server._run")
    def test_import_skill_failure(self, mock_run, mock_mcp_module):
        from wslaragon.mcp.server import import_skill

        mock_run.return_value = {"success": False, "stdout": "", "stderr": "404 not found"}

        result = import_skill("https://example.com/bad.zip")

        assert "Failed to import skill" in result