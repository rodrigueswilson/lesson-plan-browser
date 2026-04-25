from weasyprint import HTML
import os

html_content = """
<html>
<head><style>body { font-family: sans-serif; }</style></head>
<body>
<h1>Test PDF</h1>
<p>This is a test of WeasyPrint in the current environment.</p>
</body>
</html>
"""

output_path = r"d:\LP\tools\worksheets\test.pdf"
HTML(string=html_content).write_pdf(output_path)
print(f"Test PDF generated at: {output_path}")
