import re
import bleach
import mistune

class MarkdownToHTMLConverter:
    def __init__(self):
        pass
    
    # Function to add blank line before any line starting with * or - if not already preceded by a blank line
    def fix_markdown_lists(self, md: str) -> str:
        fixed = re.sub(r'([^\n])\n([ \t]*[\*\-] )', r'\1\n\n\2', md)
        return fixed


    # Function to convert Markdown content to HTML and clean it
    def convert_to_html(self, output):
        # Fix markdown lists
        fixed_md = self.fix_markdown_lists(output.content)


        markdown = mistune.create_markdown(plugins=[
            'strikethrough',
            'footnotes',
            'table',
            'url',
            'task_lists',
            'def_list',
            'math',
        ])
        html_content = markdown(fixed_md)        
        allowed_tags = [
            'p', 'strong', 'em', 'u', 's', 'br', 'span',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'a', 'blockquote', 'code', 'pre',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'img', 'figure', 'figcaption',
            'iframe', 'video', 'div'
        ]
        
        clean_html = bleach.clean(
            html_content, 
            tags=allowed_tags, 
            strip=True
        )
        
        output.content = clean_html
        return output