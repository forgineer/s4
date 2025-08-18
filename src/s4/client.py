import logging
import requests


class s4:
    def __init__(self, 
                 url: str,
                 secret_key: str = 's4'
                ):
        """
        Initialize the s4 API client.

        :param s4_url: The base URL of the s4 server.
        :param secret_key: The secret key for authentication with the s4 server.
        :return: None.
        """
        self.s4_url: str = url.rstrip('/')
        self.secret_key: str = secret_key
        self.session: requests.Session = requests.Session()

        # Set up the session headers
        self.session.headers.update({
            's4-Secret-Key': self.secret_key,
            'Content-Type': 'application/json'
        })

        # Construct base URLs
        self.sql_url: str = f'{self.s4_url}/api/sql'

        # Verify the connection to the s4 server
        self.verify_connection()


    def _response_handler(self, response: requests.Response) -> dict:
        """
        Handle the response from s4.

        :param response: The response object returned from the request.
        :return: The response data as a dictionary.
        """
        pass


    def verify_connection(self) -> None:
        """
        Verify the connection to the s4 server.

        :return: None.
        """
        _response = self.session.get(self.s4_url)

        if _response.status_code != 200:
            raise ConnectionError(f'Failed to connect to s4 server: {_response.text}')
        
        logging.debug(f'Connected to s4 server at {self.s4_url}: {_response.text}')


    def sql(self, sql: str) -> dict:
        """
        Execute an SQL query on the s4 server.

        :param sql_query: The SQL query to execute.
        :param method: The HTTP method to use for the request (GET, POST, PUT, DELETE, PATCH).
        :return: The response data as a dictionary.
        """
        _response: requests.Response = self.session.post(self.sql_url, json={'sql': sql})

        logging.debug(f'Response Status Code: {_response.status_code}')
        logging.debug(f'Response JSON: {_response.json()}')