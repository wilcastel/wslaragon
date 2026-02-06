from pathlib import Path
import os
import shutil
import yaml
from typing import Dict, List, Optional
import urllib.request
import re

class AgentManager:
    def __init__(self, config):
        self.config = config
        
    def get_presets(self) -> Dict[str, Dict]:
        """Get available agent skill presets"""
        return {
            "default": {
                "name": "Standard Development",
                "description": "Base roles for standard full-stack development",
                "skills": ["product_analyst", "architect", "git_manager", "librarian", "ui_designer"]
            },
            "laravel": {
                "name": "Laravel Specialist",
                "description": "Specialized roles for Laravel development",
                "skills": ["product_analyst", "laravel_architect", "test_engineer", "git_manager", "ui_designer"]
            },
            "wordpress": {
                "name": "WordPress Expert",
                "description": "Specialized roles for WordPress development",
                "skills": ["wordpress_developer", "theme_designer", "plugin_auditor"]
            },
            "javascript": {
                "name": "JavaScript/Node Stack",
                "description": "Roles for React, Vue, Svelte, and Node.js backend",
                "skills": ["frontend_architect", "node_specialist", "test_engineer", "ui_designer"]
            },
            "python": {
                "name": "Python Data/Web",
                "description": "Roles for Python, Flask, FastAPI or Data Science",
                "skills": ["python_expert", "data_engineer", "qa_specialist"]
            },
            "meta": {
                "name": "Meta Skills",
                "description": "Tools for creating and managing other agents",
                "skills": ["skill_creator"]
            }
        }
        
    def init_agent_structure(self, target_dir: str = ".", preset: str = "default") -> Dict:
        """Initialize .agent structure in the target directory"""
        try:
            root_path = Path(target_dir).resolve()
            agent_dir = root_path / ".agent"
            skills_dir = agent_dir / "skills"
            workflows_dir = agent_dir / "workflows"
            memory_dir = agent_dir / "memory"
            
            # Create directories
            ui_dir = agent_dir / "ui"
            ui_assets_dir = ui_dir / "assets"
            specs_dir = agent_dir / "specs"
            qa_dir = agent_dir / "qa"
            
            for path in [agent_dir, skills_dir, workflows_dir, memory_dir, ui_assets_dir, specs_dir, qa_dir]:
                path.mkdir(exist_ok=True, parents=True)
                
            # Create .gitignore for agent if not exists
            gitignore_path = agent_dir / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, 'w') as f:
                    f.write("# Ignore agent memory and logs\n")
                    f.write("memory/*.md\n")
                    f.write("!memory/README.md\n")
                    f.write("logs/\n")
            
            # Create memory readme
            memory_readme = memory_dir / "README.md"
            if not memory_readme.exists():
                with open(memory_readme, 'w') as f:
                    f.write("# Project Memory\n\nActive context and long-term memory for agents.")
            
            # Create default memory files
            memory_templates = {
                "active_context.md": "# Active Context\n\n## Current Focus\n- Initial setup\n\n## Recent Accomplishments\n- Project initialized\n",
                "architecture.md": "# Architecture\n\n## Overview\n[High level description]\n\n## Patterns\n- [Design patterns used]\n",
                "decisions.md": "# Decision Log\n\n## Records\n- [Date] Initial Setup: Project structure created.\n"
            }
            
            for filename, content in memory_templates.items():
                mem_file = memory_dir / filename
                if not mem_file.exists():
                    with open(mem_file, 'w') as f:
                        f.write(content)
            
            # Install preset skills
            available_presets = self.get_presets()
            selected_preset = available_presets.get(preset, available_presets['default'])
            
            installed_skills = []
            
            for skill_name in selected_preset['skills']:
                self._create_skill_template(skills_dir, skill_name)
                installed_skills.append(skill_name)
                
            return {
                'success': True,
                'path': str(agent_dir),
                'preset': selected_preset['name'],
                'skills': installed_skills
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _create_skill_template(self, skills_dir: Path, skill_name: str):
        """Create a basic template for a skill"""
        skill_path = skills_dir / skill_name
        skill_path.mkdir(exist_ok=True)
        
        md_file = skill_path / "SKILL.md"
        
        content = self._get_skill_content(skill_name)
            
        if not md_file.exists():
            with open(md_file, 'w') as f:
                f.write(content)

    def _get_skill_content(self, skill_name: str) -> str:
        """Get the content for a specific skill. Returns generic template if no specific content exists."""
        
        if skill_name == "skill_creator":
            return f"""---
name: Skill Creator
description: A meta-agent that helps design and generate new AI skills.
created_by: WSLaragon
---

# Skill Creator Instructions

## Role
You are an expert AI Agent Architect. Your goal is to help the user design high-quality, robust "Skills" for other AI agents to be used within the .agent/skills ecosystem.

## Process
1. **Interview**: Ask the user what kind of skill they need.
   - What is the role name? (e.g., "Database Optimizer")
   - What are the responsibilities?
   - Any specific output formats, rules, or constraints?
2. **Drafting**: Propose a structure for the SKILL.md file.
3. **Refinement**: Incorporate user feedback.
4. **Final Output**: Generate the complete `SKILL.md` file content in a code block.

## Standard Skill Format
You must ensure the generated skill follows this exact Markdown structure:

```markdown
---
name: [Skill Name]
description: [Short description]
---

# [Skill Name] Instructions

## Role
[Description of the agent's persona]

## Capabilities
- [Capability 1]
- [Capability 2]

## Rules
1. [Critical rule]
2. [Critical rule]

## Workflow
(Optional: Describe how this agent should approach problems)
```

## Best Practices
- Keep descriptions concise.
- Rules should be enforceable and clear.
- Encourage the use of "Context" or "Memory" if the skill requires saving state.
"""

        if skill_name == "librarian":
            return f"""---
name: Librarian
description: Manages project memory and documentation.
created_by: WSLaragon
---

# Librarian Instructions

## Role
You are the Project Librarian. Your responsibility is to ensure the project's "Long Term Memory" files in `.agent/memory/` are accurate, up-to-date, and useful for other agents.

## Context Files
You manage these primary files:
- `memory/active_context.md`: The current state of development (what we are working on *now*).
- `memory/architecture.md`: The high-level design, patterns, and structure.
- `memory/decisions.md`: A log of effectively "Architecture Decision Records" (ADRs).

## Capabilities
- **Update Context**: When a task is finished, summarize it in `active_context.md` and clear the "Current Focus".
- **Document Architecture**: If you see a new pattern (e.g., a new Service class strategy), capture it in `architecture.md`.
- **Record Decisions**: if the user or Architect makes a major decision (e.g., "Use PostgreSQL instead of MySQL"), log it in `decisions.md`.

## Rules
1. **Be Concise**: Other agents have token limits. Direct, bulleted summaries are better than prose.
2. **No Hallucinations**: Only document what exists or what was explicitly decided.
3. **Standard Structure**: Keep the files organized so they are machine-readable (Markdown headers).
"""

        if skill_name == "ui_designer":
            return f"""---
name: UI Designer
description: Specialist in converting visual designs (images) into code.
created_by: WSLaragon
---

# UI Designer Instructions

## Role
You are an expert UI/UX Engineer and Frontend Developer. You excel at taking visual inputs (screenshots, mockups, Figma exports) provided by the user and translating them into pixel-perfect, responsive code.

## Workflow: Image to Code
1.  **Analysis**: When the user provides an image or design reference (check `.agent/ui/assets/` if referenced):
    *   Analyze the layout structure (Headers, Sidebars, Grids).
    *   Identify the Color Palette (Primary, Secondary, Backgrounds).
    *   Identify Typography characteristics (Serif/Sans, Weights).
    *   Identify Components (Buttons, Cards, Inputs).

2.  **Strategy**:
    *   Determine the best CSS approach (Tailwind, Bootstrap, or Vanilla CSS) based on the project context.
    *   Plan the HTML semantic structure.

3.  **Implementation**:
    *   Write the code.
    *   Use comments to explain complex layout decisions.

## Rules
1.  **Responsiveness**: Always write code that works on Mobile and Desktop.
2.  **Accessibility**: Ensure contrast ratios and semantic HTML.
3.  **Fidelity**: Try to match the visual reference as closely as possible within the constraints of the framework.
"""

        # Generic Template
        return f"""---
name: {skill_name.replace('_', ' ').title()}
description: {self._get_skill_description(skill_name)}
---

# {skill_name.replace('_', ' ').title()} Instructions

## Role
You are an expert acting as a {skill_name.replace('_', ' ')}.

## Capabilities
- Analyze requirements
- Propose solutions
- Review code

## Rules
1. Always follow project standards.
2. Verify output before confirming.
"""

    def _get_skill_description(self, skill_name: str) -> str:
        """Helper to get a basic description for standard skills"""
        descriptions = {
            "product_analyst": "Analyzes user requirements and translates them into technical specs.",
            "architect": "Designs software structure and makes high-level decisions.",
            "git_manager": "Manages version control, commits, and branching strategy.",
            "laravel_architect": "Specialized architectural decisions for Laravel ecosystem.",
            "wordpress_developer": "Expert in WP core, themes, and plugins.",
            "frontend_architect": "Expert in modern JS frameworks (React, Vue, Svelte) and UI design.",
            "node_specialist": "Backend expert for Node.js, Express, and NestJS.",
            "python_expert": "Expert in Python best practices and ecosystem.",
            "test_engineer": "Ensures code quality through automated testing.",
            "librarian": "Manages project memory and keeps documentation up to date.",
            "ui_designer": "Converts visual designs and images into code."
        }
        return descriptions.get(skill_name, "Specialized agent skill.")

    def install_skill_from_url(self, url: str) -> Dict:
        """Download and install a skill from a URL"""
        try:
            # Basic validation
            if not url.startswith(('http://', 'https://')):
                return {'success': False, 'error': 'Invalid URL format'}

            # Download content
            try:
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode('utf-8')
            except Exception as e:
                return {'success': False, 'error': f"Failed to download: {str(e)}"}

            # Parse Frontmatter to find name
            # Looks for:
            # ---
            # name: Skill Name
            # ...
            name_match = re.search(r'^---\s*\n.*?name:\s*(.*?)\n', content, re.DOTALL | re.MULTILINE)
            
            if name_match:
                skill_name = name_match.group(1).strip()
                # Sanitize for folder name (spaces to underscores, lowercase)
                folder_name = "".join(x for x in skill_name if x.isalnum() or x in (' ', '_', '-')).strip().replace(' ', '_').lower()
            else:
                # Fallback: prompt user or use filename from URL? 
                # For now let's derive from URL or throw error if not standard format
                # But to be safe, let's try to infer from last part of URL
                filename = url.split('/')[-1].replace('.md', '').replace('.txt', '')
                folder_name = "".join(x for x in filename if x.isalnum() or x in ('_', '-')).lower()
                if not folder_name:
                    folder_name = "imported_skill"
                
                # If content doesn't have frontmatter, we might want to wrap it? 
                # But for now assume raw markdown import active
                # Let's add simple frontmatter if missing
                if not content.strip().startswith('---'):
                    content = f"---\nname: {folder_name.replace('_', ' ').title()}\ndescription: Imported from {url}\n---\n\n{content}"

            # Ensure .agent exists in current dir
            root_path = Path(".").resolve()
            agent_dir = root_path / ".agent"
            skills_dir = agent_dir / "skills"
            
            if not agent_dir.exists():
                return {'success': False, 'error': '.agent directory not found. Run "wslaragon agent init" first.'}
                
            skill_path = skills_dir / folder_name
            skill_path.mkdir(exist_ok=True, parents=True)
            
            target_file = skill_path / "SKILL.md"
            
            with open(target_file, 'w') as f:
                f.write(content)
                
            return {
                'success': True, 
                'name': folder_name, 
                'path': str(target_file)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
