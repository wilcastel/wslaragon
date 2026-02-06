from pathlib import Path
import os
import shutil
import yaml
from typing import Dict, List, Optional

class AgentManager:
    def __init__(self, config):
        self.config = config
        
    def get_presets(self) -> Dict[str, Dict]:
        """Get available agent skill presets"""
        return {
            "default": {
                "name": "Standard Development",
                "description": "Base roles for standard full-stack development",
                "skills": ["product_analyst", "architect", "git_manager"]
            },
            "laravel": {
                "name": "Laravel Specialist",
                "description": "Specialized roles for Laravel development",
                "skills": ["product_analyst", "laravel_architect", "test_engineer", "git_manager"]
            },
            "wordpress": {
                "name": "WordPress Expert",
                "description": "Specialized roles for WordPress development",
                "skills": ["wordpress_developer", "theme_designer", "plugin_auditor"]
            },
            "javascript": {
                "name": "JavaScript/Node Stack",
                "description": "Roles for React, Vue, Svelte, and Node.js backend",
                "skills": ["frontend_architect", "node_specialist", "test_engineer"]
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
            for path in [agent_dir, skills_dir, workflows_dir, memory_dir]:
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
            "test_engineer": "Ensures code quality through automated testing."
        }
        return descriptions.get(skill_name, "Specialized agent skill.")
