"""Tests for the agent skills system (models, parser, discovery, registry, activate_skill)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import MappingProxyType

import pytest

from agent.skills.models import (
    SkillCatalogEntry,
    SkillContent,
    SkillMetadata,
    validate_skill_name,
)
from agent.skills.parser import parse_frontmatter, parse_skill_md
from agent.skills.discovery import SkillDiscoverer, _scan_directory
from agent.skills.loader import SkillRegistry
from agent.tools.local.activate_skill import ActivateSkill


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestValidateSkillName:
    def test_valid_names(self) -> None:
        assert validate_skill_name("web-research") is True
        assert validate_skill_name("a") is True
        assert validate_skill_name("code-project") is True
        assert validate_skill_name("data-analysis") is True
        assert validate_skill_name("a1b2") is True

    def test_invalid_names(self) -> None:
        assert validate_skill_name("") is False
        assert validate_skill_name("Web-Research") is False
        assert validate_skill_name("web_research") is False
        assert validate_skill_name("-leading-dash") is False
        assert validate_skill_name("trailing-dash-") is False
        assert validate_skill_name("a" * 65) is False
        assert validate_skill_name("has spaces") is False


class TestSkillMetadata:
    def test_frozen(self) -> None:
        meta = SkillMetadata(name="test", description="desc")
        with pytest.raises(AttributeError):
            meta.name = "changed"  # type: ignore[misc]

    def test_description_required_in_constructor(self) -> None:
        meta = SkillMetadata(name="test", description="A test skill")
        assert meta.description == "A test skill"

    def test_no_triggers_field(self) -> None:
        meta = SkillMetadata(name="test", description="desc")
        assert not hasattr(meta, "triggers")

    def test_metadata_field_is_mapping_proxy(self) -> None:
        meta = SkillMetadata(
            name="test",
            description="desc",
            metadata=MappingProxyType({"author": "me"}),
        )
        assert meta.metadata["author"] == "me"
        with pytest.raises(TypeError):
            meta.metadata["new_key"] = "value"  # type: ignore[index]

    def test_compatibility_is_optional_string(self) -> None:
        meta = SkillMetadata(
            name="test", description="desc", compatibility="Requires git"
        )
        assert meta.compatibility == "Requires git"

    def test_allowed_tools_tuple(self) -> None:
        meta = SkillMetadata(
            name="test", description="desc", allowed_tools=("Bash", "Read")
        )
        assert meta.allowed_tools == ("Bash", "Read")

    def test_defaults(self) -> None:
        meta = SkillMetadata(name="test", description="desc")
        assert meta.license == ""
        assert meta.compatibility is None
        assert meta.allowed_tools == ()
        assert meta.metadata == MappingProxyType({})


class TestSkillContent:
    def test_frozen(self) -> None:
        meta = SkillMetadata(name="test", description="desc")
        content = SkillContent(
            metadata=meta,
            instructions="# Test",
            directory_path=Path("/tmp"),
            source_type="bundled",
        )
        with pytest.raises(AttributeError):
            content.instructions = "changed"  # type: ignore[misc]

    def test_directory_path_is_path(self) -> None:
        meta = SkillMetadata(name="test", description="desc")
        content = SkillContent(
            metadata=meta,
            instructions="",
            directory_path=Path("/tmp/skill"),
            source_type="user",
        )
        assert isinstance(content.directory_path, Path)

    def test_source_type_required(self) -> None:
        meta = SkillMetadata(name="test", description="desc")
        content = SkillContent(
            metadata=meta,
            instructions="",
            directory_path=Path("/tmp"),
            source_type="project",
        )
        assert content.source_type == "project"


class TestSkillCatalogEntry:
    def test_no_source_path(self) -> None:
        entry = SkillCatalogEntry(name="test", description="desc")
        assert not hasattr(entry, "source_path")


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        text = "---\nname: test\ndescription: A test\n---\n# Instructions"
        fm, body = parse_frontmatter(text)
        assert fm["name"] == "test"
        assert body == "# Instructions"

    def test_no_frontmatter(self) -> None:
        text = "# Just a markdown file"
        fm, body = parse_frontmatter(text)
        assert fm == {}
        assert body == text

    def test_yaml_containing_triple_dash(self) -> None:
        """Frontmatter with --- inside a YAML string value should not break."""
        text = '---\nname: test\ndescription: "Use --- when needed"\n---\nBody'
        fm, body = parse_frontmatter(text)
        assert fm["name"] == "test"
        assert "---" in fm["description"]
        assert body == "Body"

    def test_empty_frontmatter(self) -> None:
        text = "---\n---\n# Body"
        fm, body = parse_frontmatter(text)
        assert fm == {}
        assert body == text  # falls through since yaml.safe_load returns None

    def test_leading_newlines(self) -> None:
        text = "\n\n---\nname: test\n---\nBody"
        fm, body = parse_frontmatter(text)
        assert fm["name"] == "test"
        assert body == "Body"


class TestParseSkillMd:
    def test_parse_valid_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "my-skill")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write(
                    "---\n"
                    "name: my-skill\n"
                    "description: A test skill for testing\n"
                    "license: MIT\n"
                    "compatibility: Requires Python 3.12+\n"
                    "allowed-tools: Bash Read\n"
                    "metadata:\n"
                    "  author: tester\n"
                    "  version: 2.0\n"
                    "---\n"
                    "# Instructions\n"
                    "Do the thing.\n"
                )

            skill = parse_skill_md(skill_file)
            assert skill.metadata.name == "my-skill"
            assert skill.metadata.description == "A test skill for testing"
            assert skill.metadata.license == "MIT"
            assert skill.metadata.compatibility == "Requires Python 3.12+"
            assert skill.metadata.allowed_tools == ("Bash", "Read")
            assert skill.metadata.metadata["author"] == "tester"
            assert skill.metadata.metadata["version"] == "2.0"  # coerced to str
            assert isinstance(skill.directory_path, Path)
            assert skill.source_type == "unknown"  # parser sets default

    def test_parse_description_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "no-desc")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write("---\nname: no-desc\n---\nBody")

            with pytest.raises(ValueError, match="description"):
                parse_skill_md(skill_file)

    def test_parse_triggers_ignored_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "old-skill")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write(
                    "---\n"
                    "name: old-skill\n"
                    "description: Old style skill\n"
                    "triggers:\n"
                    "  - do stuff\n"
                    "---\nBody"
                )

            skill = parse_skill_md(skill_file)
            assert not hasattr(skill.metadata, "triggers")

    def test_parse_compatibility_list_joined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "compat")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write(
                    "---\n"
                    "name: compat\n"
                    "description: Compat test\n"
                    "compatibility:\n"
                    "  - Python 3.12\n"
                    "  - Node 18\n"
                    "---\nBody"
                )

            skill = parse_skill_md(skill_file)
            assert skill.metadata.compatibility == "Python 3.12, Node 18"

    def test_parse_no_name_falls_back_to_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "fallback-name")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write("---\ndescription: Has description\n---\nBody")

            skill = parse_skill_md(skill_file)
            assert skill.metadata.name == "fallback-name"

    def test_parse_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_skill_md("/nonexistent/SKILL.md")

    def test_parse_metadata_values_coerced_to_str(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "coerce")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write(
                    "---\n"
                    "name: coerce\n"
                    "description: Coerce test\n"
                    "metadata:\n"
                    "  version: 2.0\n"
                    "  count: 42\n"
                    "  active: true\n"
                    "---\nBody"
                )

            skill = parse_skill_md(skill_file)
            assert skill.metadata.metadata["version"] == "2.0"
            assert skill.metadata.metadata["count"] == "42"
            assert skill.metadata.metadata["active"] == "True"

    def test_parse_sandbox_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "ds-skill")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write(
                    "---\n"
                    "name: ds-skill\n"
                    "description: Data science skill\n"
                    "sandbox-template: data_science\n"
                    "---\nBody"
                )

            skill = parse_skill_md(skill_file)
            assert skill.metadata.sandbox_template == "data_science"

    def test_parse_no_sandbox_template_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "plain")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write(
                    "---\n"
                    "name: plain\n"
                    "description: Plain skill\n"
                    "---\nBody"
                )

            skill = parse_skill_md(skill_file)
            assert skill.metadata.sandbox_template is None

    def test_bundled_data_analysis_has_sandbox_template(self) -> None:
        """Verify the bundled data-analysis skill declares data_science template."""
        bundled_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "agent",
            "skills",
            "bundled",
        )
        skill_file = os.path.join(bundled_dir, "data-analysis", "SKILL.md")
        skill = parse_skill_md(skill_file)
        assert skill.metadata.sandbox_template == "data_science"

    def test_bundled_data_analysis_has_allowed_tools(self) -> None:
        """Verify the bundled data-analysis skill declares allowed tools."""
        bundled_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "agent",
            "skills",
            "bundled",
        )
        skill_file = os.path.join(bundled_dir, "data-analysis", "SKILL.md")
        skill = parse_skill_md(skill_file)
        expected = (
            "code_run",
            "code_interpret",
            "file_read",
            "file_write",
            "file_list",
            "file_edit",
            "user_message",
        )
        assert skill.metadata.allowed_tools == expected


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------


class TestSkillDiscoverer:
    def test_discover_bundled(self) -> None:
        bundled_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "agent",
            "skills",
            "bundled",
        )
        discoverer = SkillDiscoverer(bundled_dir=bundled_dir)
        skills = discoverer.discover_all()
        names = {s.metadata.name for s in skills}
        assert "deep-research" in names
        assert "data-analysis" in names
        for s in skills:
            assert s.source_type == "bundled"

    def test_hiagent_path_takes_priority_over_agents_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "project")
            hiagent_dir = os.path.join(project, ".hiagent", "skills", "my-skill")
            agents_dir = os.path.join(project, ".agents", "skills", "my-skill")
            os.makedirs(hiagent_dir)
            os.makedirs(agents_dir)

            with open(os.path.join(hiagent_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: my-skill\ndescription: From hiagent\n---\nHiAgent")
            with open(os.path.join(agents_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: my-skill\ndescription: From agents\n---\nAgents")

            discoverer = SkillDiscoverer(
                project_dir=project, bundled_dir=os.path.join(tmp, "empty")
            )
            skills = discoverer.discover_all()
            skill = next(s for s in skills if s.metadata.name == "my-skill")
            assert skill.metadata.description == "From hiagent"

    def test_source_type_tagging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "project")
            proj_skill = os.path.join(project, ".hiagent", "skills", "proj-skill")
            os.makedirs(proj_skill)
            with open(os.path.join(proj_skill, "SKILL.md"), "w") as f:
                f.write("---\nname: proj-skill\ndescription: Project skill\n---\nBody")

            discoverer = SkillDiscoverer(
                project_dir=project, bundled_dir=os.path.join(tmp, "empty")
            )
            skills = discoverer.discover_all()
            skill = next((s for s in skills if s.metadata.name == "proj-skill"), None)
            assert skill is not None
            assert skill.source_type == "project"

    def test_trust_gating_skips_project_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "project")
            proj_skill = os.path.join(project, ".hiagent", "skills", "untrusted")
            os.makedirs(proj_skill)
            with open(os.path.join(proj_skill, "SKILL.md"), "w") as f:
                f.write("---\nname: untrusted\ndescription: Untrusted\n---\nBody")

            discoverer = SkillDiscoverer(
                project_dir=project,
                bundled_dir=os.path.join(tmp, "empty"),
                trust_project=False,
            )
            skills = discoverer.discover_all()
            names = {s.metadata.name for s in skills}
            assert "untrusted" not in names

    def test_scan_skips_git_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            git_dir = os.path.join(tmp, ".git", "skill")
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: hidden\ndescription: Hidden\n---\nHidden")

            results = _scan_directory(tmp)
            names = {s.metadata.name for s in results}
            assert "hidden" not in names


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


def _make_skill(
    name: str,
    description: str = "Default description for testing",
    source_type: str = "bundled",
) -> SkillContent:
    return SkillContent(
        metadata=SkillMetadata(name=name, description=description),
        instructions=f"# {name} instructions",
        directory_path=Path(f"/tmp/{name}"),
        source_type=source_type,
    )


class TestSkillRegistry:
    def test_find_by_name(self) -> None:
        skill = _make_skill("test")
        registry = SkillRegistry((skill,))
        assert registry.find_by_name("test") is skill
        assert registry.find_by_name("missing") is None

    def test_catalog_no_source_path(self) -> None:
        registry = SkillRegistry((_make_skill("a", "Alpha"), _make_skill("b", "Beta")))
        catalog = registry.catalog()
        assert len(catalog) == 2
        assert catalog[0].name == "a"
        assert not hasattr(catalog[0], "source_path")

    def test_catalog_prompt_section_xml_format(self) -> None:
        registry = SkillRegistry((_make_skill("web-research", "Research things"),))
        section = registry.catalog_prompt_section()
        assert "<available_skills>" in section
        assert "<name>web-research</name>" in section
        assert "<description>Research things</description>" in section
        assert "activate_skill" in section

    def test_catalog_prompt_section_no_triggers(self) -> None:
        registry = SkillRegistry((_make_skill("test", "Test skill"),))
        section = registry.catalog_prompt_section()
        assert "Use when:" not in section
        assert "trigger" not in section.lower()

    def test_catalog_prompt_section_empty(self) -> None:
        registry = SkillRegistry(())
        assert registry.catalog_prompt_section() == ""

    def test_add_and_remove(self) -> None:
        registry = SkillRegistry(())
        new_registry = registry.add_skill(_make_skill("new"))
        assert registry.find_by_name("new") is None
        assert new_registry.find_by_name("new") is not None
        removed = new_registry.remove_skill("new")
        assert removed.find_by_name("new") is None

    def test_add_replaces_existing(self) -> None:
        old = _make_skill("dup", "old")
        new = _make_skill("dup", "new")
        registry = SkillRegistry((old,))
        updated = registry.add_skill(new)
        assert updated.find_by_name("dup").metadata.description == "new"

    def test_names(self) -> None:
        registry = SkillRegistry((_make_skill("a"), _make_skill("b")))
        assert set(registry.names()) == {"a", "b"}

    def test_all_skills(self) -> None:
        skills = (_make_skill("x"), _make_skill("y"))
        registry = SkillRegistry(skills)
        assert registry.all_skills() == skills


# ---------------------------------------------------------------------------
# match_description tests
# ---------------------------------------------------------------------------


class TestMatchDescription:
    def test_no_match_below_threshold(self) -> None:
        skill = _make_skill("web-research", "Deep web research with triangulation")
        registry = SkillRegistry((skill,))
        assert registry.match_description("hello world") is None

    def test_match_with_sufficient_overlap(self) -> None:
        skill = _make_skill(
            "web-research",
            "Deep web research with multi-query triangulation and source credibility",
        )
        registry = SkillRegistry((skill,))
        result = registry.match_description(
            "please research this topic with web sources"
        )
        assert result is not None
        assert result.metadata.name == "web-research"

    def test_case_insensitive(self) -> None:
        skill = _make_skill("web-research", "Deep web RESEARCH methodology")
        registry = SkillRegistry((skill,))
        result = registry.match_description("RESEARCH this DEEP topic on the WEB")
        assert result is not None

    def test_most_overlap_wins(self) -> None:
        web = _make_skill("web-research", "research topics on the web with sources")
        data = _make_skill(
            "data-analysis", "analyze datasets charts statistics research"
        )
        registry = SkillRegistry((web, data))
        result = registry.match_description("analyze these datasets with charts")
        assert result is not None
        assert result.metadata.name == "data-analysis"

    def test_empty_text(self) -> None:
        skill = _make_skill("test", "Some description")
        registry = SkillRegistry((skill,))
        assert registry.match_description("") is None

    def test_no_skills(self) -> None:
        registry = SkillRegistry(())
        assert registry.match_description("research something") is None

    def test_data_analysis_matches_csv_request(self) -> None:
        """data-analysis skill should match 'analyze this CSV data'."""
        bundled_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "agent",
            "skills",
            "bundled",
        )
        from agent.skills.discovery import SkillDiscoverer

        discoverer = SkillDiscoverer(bundled_dir=bundled_dir)
        skills = discoverer.discover_all()
        registry = SkillRegistry(tuple(skills))
        result = registry.match_description("analyze this CSV data")
        assert result is not None
        assert result.metadata.name == "data-analysis"

    def test_tie_breaks_by_insertion_order(self) -> None:
        a = _make_skill("skill-a", "analyze data charts")
        b = _make_skill("skill-b", "analyze data charts")
        registry = SkillRegistry((a, b))
        result = registry.match_description("analyze data charts")
        assert result is not None
        assert result.metadata.name == "skill-a"


# ---------------------------------------------------------------------------
# ActivateSkill tool tests
# ---------------------------------------------------------------------------


class TestActivateSkill:
    def test_definition(self) -> None:
        registry = SkillRegistry(())
        tool = ActivateSkill(skill_registry=registry)
        defn = tool.definition()
        assert defn.name == "activate_skill"
        assert "name" in defn.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_activate_existing_skill(self) -> None:
        skill = _make_skill("test-skill")
        registry = SkillRegistry((skill,))
        tool = ActivateSkill(skill_registry=registry)

        result = await tool.execute(name="test-skill")
        assert result.success is True
        assert "<skill_content " in result.output
        assert "test-skill" in result.output
        assert "Skill directory:" in result.output

    @pytest.mark.asyncio
    async def test_activate_missing_skill(self) -> None:
        registry = SkillRegistry((_make_skill("other"),))
        tool = ActivateSkill(skill_registry=registry)

        result = await tool.execute(name="missing")
        assert result.success is False
        assert "not found" in result.error
        assert "other" in result.error

    @pytest.mark.asyncio
    async def test_activate_already_active_skill(self) -> None:
        skill = _make_skill("data-analysis")
        registry = SkillRegistry((skill,))
        tool = ActivateSkill(
            skill_registry=registry,
            active_skill_name="data-analysis",
        )

        result = await tool.execute(name="data-analysis")
        assert result.success is True
        assert "already active" in result.output

    def test_no_mutable_setter(self) -> None:
        """active_skill_name should be read-only (no setter)."""
        registry = SkillRegistry(())
        tool = ActivateSkill(skill_registry=registry)
        with pytest.raises(AttributeError):
            tool.active_skill_name = "should-fail"  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_categorized_resources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "rich-skill")
            os.makedirs(os.path.join(skill_dir, "scripts"))
            os.makedirs(os.path.join(skill_dir, "references"))
            os.makedirs(os.path.join(skill_dir, "assets"))
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: rich-skill\ndescription: Has everything\n---\nBody")
            with open(os.path.join(skill_dir, "scripts", "run.py"), "w") as f:
                f.write("print('run')")
            with open(os.path.join(skill_dir, "references", "guide.md"), "w") as f:
                f.write("# Guide")
            with open(os.path.join(skill_dir, "assets", "template.html"), "w") as f:
                f.write("<html/>")

            skill = parse_skill_md(os.path.join(skill_dir, "SKILL.md"))
            registry = SkillRegistry((skill,))
            tool = ActivateSkill(skill_registry=registry)

            result = await tool.execute(name="rich-skill")
            assert result.success is True
            assert "<scripts>" in result.output
            assert "scripts/run.py" in result.output
            assert "<references>" in result.output
            assert "references/guide.md" in result.output
            assert "<assets>" in result.output
            assert "assets/template.html" in result.output


# ---------------------------------------------------------------------------
# Installer tests
# ---------------------------------------------------------------------------


class TestSkillInstaller:
    def test_list_installed_empty(self) -> None:
        from agent.skills.installer import SkillInstaller

        with tempfile.TemporaryDirectory() as tmp:
            installer = SkillInstaller(install_dir=tmp)
            assert installer.list_installed() == ()

    def test_uninstall_nonexistent(self) -> None:
        from agent.skills.installer import SkillInstaller

        with tempfile.TemporaryDirectory() as tmp:
            installer = SkillInstaller(install_dir=tmp)
            assert installer.uninstall("nonexistent") is False

    def test_install_and_list(self) -> None:
        from agent.skills.installer import SkillInstaller

        with tempfile.TemporaryDirectory() as tmp:
            installer = SkillInstaller(install_dir=os.path.join(tmp, "installed"))

            # Create a source skill
            source_dir = os.path.join(tmp, "source", "test-skill")
            os.makedirs(source_dir)
            with open(os.path.join(source_dir, "SKILL.md"), "w") as f:
                f.write("---\nname: test-skill\ndescription: Test\n---\nBody")

            skill = parse_skill_md(os.path.join(source_dir, "SKILL.md"))
            installed = installer._install_skill_dir(source_dir, skill)

            assert installed.metadata.name == "test-skill"

            listed = installer.list_installed()
            assert len(listed) == 1
            assert listed[0].name == "test-skill"

            # Uninstall
            assert installer.uninstall("test-skill") is True
            assert installer.list_installed() == ()

    @pytest.mark.asyncio
    async def test_install_from_git_invalid_url(self) -> None:
        from agent.skills.installer import SkillInstaller

        with tempfile.TemporaryDirectory() as tmp:
            installer = SkillInstaller(install_dir=tmp)
            with pytest.raises(ValueError, match="HTTPS"):
                await installer.install_from_git("http://example.com/repo.git")

    @pytest.mark.asyncio
    async def test_install_from_url_invalid_url(self) -> None:
        from agent.skills.installer import SkillInstaller

        with tempfile.TemporaryDirectory() as tmp:
            installer = SkillInstaller(install_dir=tmp)
            with pytest.raises(ValueError, match="HTTPS"):
                await installer.install_from_url("http://example.com/SKILL.md")


# ---------------------------------------------------------------------------
# ToolRegistry replace_tool tests
# ---------------------------------------------------------------------------


class TestToolRegistryReplaceSkill:
    """Test that ToolRegistry supports replacing an existing tool."""

    def test_replace_tool(self) -> None:
        from agent.tools.registry import ToolRegistry as ToolReg

        skill_a = _make_skill("test")
        registry_a = SkillRegistry((skill_a,))
        tool_a = ActivateSkill(skill_registry=registry_a, active_skill_name=None)

        tool_reg = ToolReg()
        tool_reg = tool_reg.register(tool_a)
        assert tool_reg.get("activate_skill") is tool_a

        # Replace with new instance
        tool_b = ActivateSkill(skill_registry=registry_a, active_skill_name="test")
        tool_reg2 = tool_reg.replace_tool(tool_b)
        assert tool_reg2.get("activate_skill") is tool_b
        # Original unchanged
        assert tool_reg.get("activate_skill") is tool_a


class TestToolRegistryFilterByNames:
    """Test that ToolRegistry.filter_by_names returns only requested tools."""

    def test_filter_by_names_keeps_matching(self) -> None:
        from agent.tools.registry import ToolRegistry as ToolReg

        skill = _make_skill("test")
        reg = SkillRegistry((skill,))
        tool_a = ActivateSkill(skill_registry=reg)
        tool_b = ActivateSkill(skill_registry=reg, active_skill_name="test")

        tool_reg = ToolReg()
        tool_reg = tool_reg.register(tool_a)
        # replace_tool to add a second tool with a different name is not possible
        # with ActivateSkill (same name), so test with just the single tool
        filtered = tool_reg.filter_by_names({"activate_skill"})
        assert filtered.get("activate_skill") is tool_a

    def test_filter_by_names_excludes_non_matching(self) -> None:
        from agent.tools.registry import ToolRegistry as ToolReg

        skill = _make_skill("test")
        reg = SkillRegistry((skill,))
        tool = ActivateSkill(skill_registry=reg)

        tool_reg = ToolReg()
        tool_reg = tool_reg.register(tool)
        filtered = tool_reg.filter_by_names({"nonexistent"})
        assert filtered.get("activate_skill") is None

    def test_filter_by_names_returns_new_registry(self) -> None:
        from agent.tools.registry import ToolRegistry as ToolReg

        skill = _make_skill("test")
        reg = SkillRegistry((skill,))
        tool = ActivateSkill(skill_registry=reg)

        tool_reg = ToolReg()
        tool_reg = tool_reg.register(tool)
        filtered = tool_reg.filter_by_names({"activate_skill"})
        # Original is unchanged — immutable style
        assert filtered is not tool_reg
        assert tool_reg.get("activate_skill") is tool
