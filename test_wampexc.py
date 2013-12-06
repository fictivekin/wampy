import unittest
from wampexc import WAMPError


class TestWAMPException(unittest.TestCase):

    def test_exceptions(self):
        with self.assertRaises(WAMPError) as context:
            raise WAMPError('uri', 'description', {'detail': 42})
        exc = context.exception
        self.assertTrue(isinstance(exc, WAMPError))
        self.assertEqual(exc.args, ('uri', 'description', {'detail': 42}))
        self.assertEqual(exc.error_uri, 'uri')
        self.assertEqual(exc.error_desc, 'description')
        self.assertEqual(exc.error_details, {'detail': 42})


if __name__ == '__main__':
    unittest.main()
