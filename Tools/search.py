from ddgs import DDGS

class Search:
    def __init__(self):
        pass
    def search(self, topic, max_results=10) -> list:
        """ 
        Perform a DuckDuckGo search for the given topic and return list of urls.

        Args:
            topic (str): The search topic.
            max_results (int): The maximum number of results to return.

        Returns:
            List[str]: A list of URLs related to the search topic.
        """
        with DDGS() as ddgs:
          results = ddgs.text(topic, max_results=max_results)
          urls = []
          for item in results:
              if "href" in item and not item["href"].lower().endswith(".pdf"):
                  urls.append(item["href"])
        return urls
    
    def search_complete(self, topic, max_results=10) -> list[dict]:
        """
        Perform a DuckDuckGo search for the given topic and return the complete search results.

        Args:
            topic (str): The search topic.
            max_results (int): The maximum number of results to return.

        Returns:
            dict: A list of dictionaries, each containing detailed information about a search result, such as title, href, and body, as provided by DDGS.
        """

        with DDGS() as ddgs:
            results = ddgs.text(topic, max_results=max_results)
            filtered_results = [
                item for item in results
                if "href" in item and not item["href"].lower().endswith(".pdf")
            ]
            return filtered_results
        
    def search_list(self, topic:list, max_results_per_topic=2 ) -> list:
        """
        Perform a DuckDuckGo search on a list of topics and return unique list of urls.

        Args:
            topic (list): A list of search topics.

        Returns:
            List[str]: A list of URLs related to the search topics.
               
        """

        urls = []
        for t in topic:
            urls.extend(self.search(t, max_results_per_topic))
        return list(set(urls))