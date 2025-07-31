from ddgs import DDGS

class Search:
    def __init__(self):
        pass
    def search(self, topic, max_results):
        with DDGS() as ddgs:
          results = ddgs.text(topic, max_results=max_results)
          urls = []
          for item in results:
              if "href" in item:
                  urls.append(item["href"])
        return urls