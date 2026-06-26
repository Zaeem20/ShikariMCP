# ShikariMCP — Reporting Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="pandoc_convert",
    category="reporting",
    scope=ToolScope.LOCAL,
    binary="pandoc",
    description="Convert documents between formats using Pandoc",
)
async def pandoc_convert(input: str, output: str, pdf_engine: str = "") -> str:
    """
    Convert a document from one format to another using Pandoc.

    Generates a table of contents with depth 2 by default.

    Args:
        input: Path to the input file
        output: Path to the output file (extension determines format)
        pdf_engine: PDF engine to use (e.g. 'weasyprint', 'pdflatex', 'wkhtmltopdf')
    """
    cmd = ["pandoc", input, "-o", output, "--toc", "--toc-depth=2"]
    if pdf_engine:
        cmd.extend(["--pdf-engine", pdf_engine])
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"pandoc error: {result.stderr}"


@shikari_tool(
    name="weasyprint_pdf",
    category="reporting",
    scope=ToolScope.LOCAL,
    binary="weasyprint",
    description="Convert an HTML document to PDF using WeasyPrint",
)
async def weasyprint_pdf(input_html: str, output_pdf: str) -> str:
    """
    Render an HTML file to a PDF document using WeasyPrint.

    Args:
        input_html: Path to the input HTML file
        output_pdf: Path for the generated PDF file
    """
    cmd = ["weasyprint", input_html, output_pdf]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"weasyprint error: {result.stderr}"


@shikari_tool(
    name="wkhtmltopdf_render",
    category="reporting",
    scope=ToolScope.LOCAL,
    binary="wkhtmltopdf",
    description="Render an HTML file to PDF using wkhtmltopdf",
)
async def wkhtmltopdf_render(input: str, output: str) -> str:
    """
    Convert an HTML file to PDF using wkhtmltopdf with local file access enabled.

    Args:
        input: Path to the input HTML file
        output: Path for the generated PDF file
    """
    cmd = ["wkhtmltopdf", "--enable-local-file-access", input, output]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"wkhtmltopdf error: {result.stderr}"


@shikari_tool(
    name="nmap_xml_to_html",
    category="reporting",
    scope=ToolScope.LOCAL,
    binary="xsltproc",
    description="Convert an Nmap XML report to HTML using xsltproc",
)
async def nmap_xml_to_html(xml: str, output_html: str) -> str:
    """
    Transform an Nmap XML output file into an HTML report using xsltproc.

    Args:
        xml: Path to the Nmap XML file
        output_html: Path for the generated HTML report
    """
    cmd = ["xsltproc", xml, "-o", output_html]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"xsltproc error: {result.stderr}"
