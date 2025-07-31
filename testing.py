# import json

# # Example: Load and print data from a JSON file named 'data.json'
# with open('blog_output_before.json', 'r') as file:
#     data = json.load(file)

# # print(data.get("blog_data", {}).get("content"))
# print(data.get("content"))

# from ddgs import DDGS

# with DDGS() as ddgs:
#   results = ddgs.text('imran khan pakistan 2025', max_results=10)
#   urls = []
#   for item in results:
#       if "href" in item:
#           urls.append(item["href"])
#   current_urls = urls

# from featuredimage import FeaturedImageExtractor

# # url = ['https://en.wikipedia.org/wiki/The_Hobbit:_The_Battle_of_the_Five_Armies',
# #        'https://www.warnerbros.com/movies/hobbit-battle-five-armies'
# # 'https://www.youtube.com/watch?v=_kvjKaTqX4c'
# # 'https://www.rottentomatoes.com/m/the_hobbit_the_battle_of_the_five_armies'
# # 'https://tolkiengateway.net/wiki/Battle_of_Five_Armies']

# extractor = FeaturedImageExtractor()

# featured_image = extractor.get_featured_image(urls)

# print(featured_image)




# import markdown
# import re

# text = """
# """
# def fix_markdown_lists(md: str) -> str:
#     # Add a blank line before any line starting with * or - if not already preceded by a blank line
#     fixed = re.sub(r'([^\n])\n([ \t]*[\*\-] )', r'\1\n\n\2', md)
#     return fixed

# # Fix markdown
# fixed_md = fix_markdown_lists(text)
# html = markdown.markdown(fixed_md)

# print(html)


# from Tools.search import Search

# search = Search()
# urls = search.search('imran khan pakistan 2025', 10)

# print(urls)