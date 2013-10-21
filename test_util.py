import unittest
import util


class TestUtil(unittest.TestCase):

    def test_terablate(self):
        class FancyList(list):
            pass

        self.assertEqual(util.iterablate(None), ())
        self.assertEqual(util.iterablate(None, wrapper_cls=list), [])
        self.assertEqual(util.iterablate([]), [])
        self.assertEqual(util.iterablate([], also_wrap=list), ([],))
        self.assertEqual(util.iterablate(FancyList()), FancyList())
        self.assertEqual(util.iterablate(FancyList(), also_wrap=list),
                         (FancyList(),))
        self.assertEqual(util.iterablate(FancyList(), also_wrap=FancyList),
                         (FancyList(),))
        self.assertEqual(util.iterablate([], also_wrap=FancyList), [])
        self.assertEqual(util.iterablate(1), (1,))
        self.assertEqual(util.iterablate('foo'), ('foo',))
        self.assertEqual(util.iterablate(('foo', 'bar')), ('foo', 'bar'))


if __name__ == '__main__':
    unittest.main()
