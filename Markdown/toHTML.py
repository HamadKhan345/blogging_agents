import re
import markdown
import bleach

class MarkdownToHTMLConverter:
    def __init__(self):
        pass
    
    # Function to add blank line before any line starting with * or - if not already preceded by a blank line
    def fix_markdown_lists(self, md: str) -> str:
        fixed = re.sub(r'([^\n])\n([ \t]*[\*\-] )', r'\1\n\n\2', md)
        return fixed

    # Function to convert Markdown content to HTML and clean it
    def convert_to_html(self, output):
        # Fix markdown
        fixed_md = self.fix_markdown_lists(output.content)
        html_content = markdown.markdown(fixed_md)
        allowed_tags = [
        'p', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'blockquote', 'a', 'br',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'code', 'pre', 's', 'img', 'video', 'div'
        ]
        clean_html = bleach.clean(html_content, tags=allowed_tags, strip=True)
        output.content = clean_html
        return output
