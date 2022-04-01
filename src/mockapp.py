"""
Mockapp is  a mock service that can mock any http service.
"""
from flask import Flask
import requests
from multiprocessing import Process
import time


class MockApp(Flask):
    """
    to create new Mockapp you need to :
    1. call the Mockapp as context manager "with MockApp(__name__, 'localhost', 5050) as snapping:"
    2. add the mock url with the response.
    3. start the mock app .
    this must be in this order .
    in the end of the test the context manger will terminate the mock service via __exit__
    todo : be able to change the url dynamically in run time (hopping it possible)

    test example :
    lets assume that there service_1 (the service under test) is calling service_2 via ep "/api/v1/are_you_ok"
    and we want to mock service_2
    def snapping_test(expected ,val ):
        with MockApp(__name__, 'localhost', 5050) as service_2:

        service_2.add_mock_url('/api/v1/status', dict(data=dict(status="iam_good")))
        service_2.start_mock()
        service_1.is_service_2_ok(expected)

    to use more then one mock service you can create several context manager in the test as example below :

    def snapping_test(expected ,val ):
        with MockApp(__name__, 'localhost', 5050) as service_2, MockApp(__name__, 'localhost', 6060) as service_3:

        service_2.add_mock_url('api/v1/price', dict(data=dict(price=200)))
        service_2.start_mock()

        service_3.add_mock_url('api/v1/status', dict(data=dict(status="all_good")))
        service_3.start_mock()


    """
    def __init__(self, file_name, host, port):
        """

        :param file_name: the file name that the app was init
        :param host: host name for the mock service
        :param port: port name for the mock service
        """
        super().__init__(file_name)
        self.host = host
        self.port = port
        #runnig the flask app in process to be able to run it in parallel via context manager
        self.process = Process(target=self.run, args=(self.host, self.port))
        #for now this is the only way i found to add the return response .
        self.mock_response = None

    def __enter__(self):
        """
        Each time we create new instance in the context manager convention ("with MockApp as a"). this step will run
        :return: app
        """
        return self

    def start_mock(self):
        """
        Starting the mock service. adding the mock url can be done only before this step
        :return: new Mockurl instance to define each mock process.
        """
        _alive = False
        count = 0
        self.process.start()
        while _alive and count < 30:
            if self.process.is_alive():
                break
            time.sleep(0.4)
            count += 1
        return self.process

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.process.terminate()

    def add_mock_url(self, url, json_response):
        """
        Instead of using app.route('/foo')  as a decorator .this func will add the route and the func to the mock service

        :param url: the  mock url path. this will be the url that will be add to the mock service route
        :param json_response: the response that the mock service will return
        :return: None
        """
        return _Mockurl(self).add_mock_url(url, json_response)


class _Mockurl(object):

    def __init__(self, app):
        """

        :param app:
        """
        self.app = app
        self.json_response = None

    def add_mock_url(self, url, json_response):

        self.mock_response = json_response
        self.app.add_url_rule(url, '_return_response', self._return_response, methods=['POST'])

    def _return_response(self):
        # it is working but it is not perfect. need to change the way of how the context service add func and route .
        return self.mock_response


if __name__ == "__main__":

    with MockApp(__name__, 'localhost', 5050) as service_2:

        service_2.add_mock_url('/api/v1/status', dict(data=dict(status="all_good")))
        service_2.start_mock()
      # a.set_mock_url('/api/b', dict(distance=700))
        print(requests.post('http://localhost:5050/api/v1/status').content)
