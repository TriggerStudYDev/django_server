from rest_framework.test import APITestCase
from rest_framework import status

class ExampleAPITest(APITestCase):
    def test_example_list(self):
        response = self.client.get('/api/example/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)