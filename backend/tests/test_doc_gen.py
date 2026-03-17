"""Tests for document generation tools."""

from __future__ import annotations

import pytest

from agent.tools.base import ExecutionContext
from agent.tools.sandbox.doc_gen import (
    DocCreateDOCX,
    DocCreatePDF,
    DocCreatePPTX,
    DocCreateXLSX,
    _PDF_SCRIPT_TEMPLATE,
    _CONTENT_PATH,
    _TEMPLATE_DIR,
    _validate_output_path,
    _validate_pdf_params,
)


# ---------------------------------------------------------------------------
# Output path validation
# ---------------------------------------------------------------------------


class TestValidateOutputPath:
    def test_valid_paths(self) -> None:
        assert _validate_output_path("/workspace/output.pdf") is None
        assert _validate_output_path("/workspace/docs/report.pdf") is None
        assert _validate_output_path("/workspace/my-file_v2.pdf") is None

    def test_path_traversal_rejected(self) -> None:
        err = _validate_output_path("/workspace/../etc/passwd")
        assert err is not None
        assert ".." in err

    def test_outside_workspace_rejected(self) -> None:
        err = _validate_output_path("/tmp/output.pdf")
        assert err is not None
        assert "workspace" in err.lower()

    def test_shell_injection_rejected(self) -> None:
        err = _validate_output_path("/workspace/out.pdf; rm -rf /")
        assert err is not None

    def test_empty_rejected(self) -> None:
        err = _validate_output_path("")
        assert err is not None


# ---------------------------------------------------------------------------
# PDF parameter validation
# ---------------------------------------------------------------------------


class TestValidatePdfParams:
    def test_valid_params(self) -> None:
        assert _validate_pdf_params("default", "A4", "portrait") is None
        assert _validate_pdf_params("report", "letter", "landscape") is None
        assert _validate_pdf_params("article", "legal", "portrait") is None
        assert _validate_pdf_params("minimal", "A4", "landscape") is None

    def test_invalid_style(self) -> None:
        err = _validate_pdf_params("fancy", "A4", "portrait")
        assert err is not None
        assert "style" in err.lower()

    def test_invalid_page_size(self) -> None:
        err = _validate_pdf_params("default", "tabloid", "portrait")
        assert err is not None
        assert "page_size" in err.lower()

    def test_invalid_orientation(self) -> None:
        err = _validate_pdf_params("default", "A4", "diagonal")
        assert err is not None
        assert "orientation" in err.lower()


# ---------------------------------------------------------------------------
# PDF script template generation
# ---------------------------------------------------------------------------


class TestPdfScriptGeneration:
    """Verify the generated Python script is syntactically valid."""

    def _make_script(self, **overrides: str) -> str:
        defaults = {
            "content_path": _CONTENT_PATH,
            "template_dir": _TEMPLATE_DIR,
            "output_path": "/workspace/out.pdf",
            "style": "default",
            "page_size": "A4",
            "orientation": "portrait",
            "title": "",
            "custom_css_path": "/tmp/_doc_custom.css",
        }
        defaults.update(overrides)
        return _PDF_SCRIPT_TEMPLATE.format(**defaults)

    def test_basic_script_is_valid_python(self) -> None:
        script = self._make_script()
        compile(script, "<string>", "exec")

    def test_title_with_double_quotes(self) -> None:
        script = self._make_script(title='My \\"Report\\"')
        compile(script, "<string>", "exec")

    def test_title_with_backslashes(self) -> None:
        script = self._make_script(title="path\\\\to\\\\file")
        compile(script, "<string>", "exec")

    def test_all_styles(self) -> None:
        for style in ("default", "report", "article", "minimal"):
            script = self._make_script(style=style)
            compile(script, "<string>", "exec")


# ---------------------------------------------------------------------------
# DocCreatePDF
# ---------------------------------------------------------------------------


class TestDocCreatePDF:
    def test_definition(self) -> None:
        tool = DocCreatePDF()
        defn = tool.definition()
        assert defn.name == "document_create_pdf"
        assert defn.execution_context == ExecutionContext.SANDBOX
        assert "content" in defn.input_schema["required"]

    def test_definition_has_style_enum(self) -> None:
        tool = DocCreatePDF()
        defn = tool.definition()
        style_prop = defn.input_schema["properties"]["style"]
        assert set(style_prop["enum"]) == {"default", "report", "article", "minimal"}

    def test_definition_has_page_size_enum(self) -> None:
        tool = DocCreatePDF()
        defn = tool.definition()
        page_prop = defn.input_schema["properties"]["page_size"]
        assert set(page_prop["enum"]) == {"A4", "letter", "legal"}

    def test_definition_has_orientation_enum(self) -> None:
        tool = DocCreatePDF()
        defn = tool.definition()
        orient_prop = defn.input_schema["properties"]["orientation"]
        assert set(orient_prop["enum"]) == {"portrait", "landscape"}

    @pytest.mark.asyncio
    async def test_empty_content_fails(self) -> None:
        tool = DocCreatePDF()
        result = await tool.execute(session=None, content="  ")
        assert not result.success
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_style_fails(self) -> None:
        tool = DocCreatePDF()
        result = await tool.execute(session=None, content="hello", style="fancy")
        assert not result.success
        assert "Invalid style" in result.error

    @pytest.mark.asyncio
    async def test_invalid_page_size_fails(self) -> None:
        tool = DocCreatePDF()
        result = await tool.execute(session=None, content="hello", page_size="tabloid")
        assert not result.success
        assert "Invalid page_size" in result.error

    @pytest.mark.asyncio
    async def test_invalid_orientation_fails(self) -> None:
        tool = DocCreatePDF()
        result = await tool.execute(
            session=None, content="hello", orientation="diagonal"
        )
        assert not result.success
        assert "Invalid orientation" in result.error

    @pytest.mark.asyncio
    async def test_path_traversal_fails(self) -> None:
        tool = DocCreatePDF()
        result = await tool.execute(
            session=None, content="hello", output_path="/workspace/../etc/passwd"
        )
        assert not result.success
        assert ".." in result.error

    @pytest.mark.asyncio
    async def test_path_outside_workspace_fails(self) -> None:
        tool = DocCreatePDF()
        result = await tool.execute(
            session=None, content="hello", output_path="/tmp/evil.pdf"
        )
        assert not result.success


# ---------------------------------------------------------------------------
# DocCreateDOCX
# ---------------------------------------------------------------------------


class TestDocCreateDOCX:
    def test_definition(self) -> None:
        tool = DocCreateDOCX()
        defn = tool.definition()
        assert defn.name == "document_create_docx"

    @pytest.mark.asyncio
    async def test_empty_content_fails(self) -> None:
        tool = DocCreateDOCX()
        result = await tool.execute(session=None, content="")
        assert not result.success

    @pytest.mark.asyncio
    async def test_path_traversal_fails(self) -> None:
        tool = DocCreateDOCX()
        result = await tool.execute(
            session=None, content="hello", output_path="/workspace/../etc/passwd"
        )
        assert not result.success


# ---------------------------------------------------------------------------
# DocCreateXLSX
# ---------------------------------------------------------------------------


class TestDocCreateXLSX:
    def test_definition(self) -> None:
        tool = DocCreateXLSX()
        defn = tool.definition()
        assert defn.name == "document_create_xlsx"

    @pytest.mark.asyncio
    async def test_empty_data_fails(self) -> None:
        tool = DocCreateXLSX()
        result = await tool.execute(session=None, data="")
        assert not result.success

    @pytest.mark.asyncio
    async def test_path_traversal_fails(self) -> None:
        tool = DocCreateXLSX()
        result = await tool.execute(
            session=None, data='[["a"]]', output_path="/workspace/../etc/passwd"
        )
        assert not result.success


# ---------------------------------------------------------------------------
# DocCreatePPTX
# ---------------------------------------------------------------------------


class TestDocCreatePPTX:
    def test_definition(self) -> None:
        tool = DocCreatePPTX()
        defn = tool.definition()
        assert defn.name == "document_create_pptx"

    @pytest.mark.asyncio
    async def test_empty_slides_fails(self) -> None:
        tool = DocCreatePPTX()
        result = await tool.execute(session=None, slides="")
        assert not result.success

    @pytest.mark.asyncio
    async def test_path_traversal_fails(self) -> None:
        tool = DocCreatePPTX()
        result = await tool.execute(
            session=None, slides="Slide 1\nContent", output_path="/workspace/../x"
        )
        assert not result.success
