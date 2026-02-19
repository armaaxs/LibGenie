import httpx

class LibgenClient:
    def __init__(self, mirror_url, query, search_columns, search_topics, limit):
        self.query = query
        self.mirror_url = mirror_url.rstrip('/')
        self.columns = search_columns
        self.topics = search_topics
        self.limit = limit
        
        # 1. Define Browser-like headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # 2. Configure Limits and Transport
        # We limit the number of connections and force HTTP/1.1 for stability
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        
        self.session = httpx.Client(
            timeout=httpx.Timeout(200, connect=10.0), # Give it more time to connect
            headers=headers,
            limits=limits,
            http2=False, # FORCE HTTP/1.1 (Crucial for older mirrors)
            follow_redirects=True
        )
        
        print(f"[DEBUG] Client initialized with Stability Mode (HTTP/1.1)")
    def get_html(self):
        url = f"{self.mirror_url}/index.php"
        params = self._craft_params()
        
        print(f"\n[DEBUG] GET_HTML: Requesting {url}")
        print(f"[DEBUG] Params: {params}")
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status() 
            
            print(f"[DEBUG] Status Code: {response.status_code}")
            # Printing a snippet of the HTML to verify we actually got the table
            print(f"[DEBUG] HTML Response Snippet: {response.text[:500]}...") 
            
            return response.text
        except Exception as e:
            print(f"[ERROR] Failed to fetch HTML: {e}")
            raise

    def _craft_params(self):
        params = {
            "req": self.query,
            "columns[]": self.columns, 
            # "objects[]": ["f", "e", "s", "a", "p", "w"], 
            "objects[]": [ "e","f"], 
            "topics[]": self.topics, 
            "res": str(self.limit),
            "filesuns": "all",
        }
        return params

    def get_upload_info(self, book_ids: list) -> dict:
        if not book_ids:
            print("[DEBUG] GET_UPLOAD_INFO: No book IDs provided.")
            return {}
            
        url = f"{self.mirror_url}/json.php"
        params = {
            "ids": ",".join(str(id) for id in book_ids),
            "object": "e",
            "addkeys": "*"
        }
        
        print(f"\n[DEBUG] GET_UPLOAD_INFO: Requesting JSON for IDs: {book_ids}")
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] JSON received. Items found: {len(data)}")
            return data
            
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] Server error {e.response.status_code} while fetching JSON.")
            return {}
        except Exception as e:
            print(f"[ERROR] Unexpected error during JSON fetch: {e}")
            return {}

    def close(self):
        """Manually close the session."""
        self.session.close()
        print("[DEBUG] Session closed.")

    def __del__(self):
        """Cleanup session on object destruction."""
        try:
            self.session.close()
        except:
            pass