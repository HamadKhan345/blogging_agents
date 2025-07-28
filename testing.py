import json

# Example: Load and print data from a JSON file named 'data.json'
with open('blog_output.json', 'r') as file:
    data = json.load(file)

print(data.get("blog_data", {}).get("content"))


# from featuredimage import FeaturedImageExtractor

# url = ['https://en.wikipedia.org/wiki/The_Hobbit:_The_Battle_of_the_Five_Armies',
#        'https://www.warnerbros.com/movies/hobbit-battle-five-armies'
# 'https://www.youtube.com/watch?v=_kvjKaTqX4c'
# 'https://www.rottentomatoes.com/m/the_hobbit_the_battle_of_the_five_armies'
# 'https://tolkiengateway.net/wiki/Battle_of_Five_Armies']

# extractor = FeaturedImageExtractor()

# featured_image = extractor.get_featured_image(url)

# print(featured_image)