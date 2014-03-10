import gc
import unittest
import weakref
import inspect

from wamputil import (none_or_equal, iterablate, check_signature,
                      WeaklyBoundCallable, AttributeFactoryMixin,
                      _EnumishMixin, EnumishStr, EnumishInt)


class TestNoneOrEual(unittest.TestCase):

    def test_none_or_equal(self):
        self.assertTrue(none_or_equal(None, True))
        self.assertTrue(none_or_equal(None, False))
        self.assertTrue(none_or_equal(None, None))
        self.assertFalse(none_or_equal(False, True))
        self.assertTrue(none_or_equal(False, False))
        self.assertFalse(none_or_equal(False, None))
        self.assertTrue(none_or_equal(True, True))
        self.assertFalse(none_or_equal(True, False))
        self.assertFalse(none_or_equal(True, None))


class TestIterablate(unittest.TestCase):

    def test_terablate(self):
        class FancyList(list):
            pass

        self.assertEqual(iterablate(None), ())
        self.assertEqual(iterablate(None, wrapper_cls=list), [])
        self.assertEqual(iterablate([]), [])
        self.assertEqual(iterablate([], also_wrap=list), ([],))
        self.assertEqual(iterablate(FancyList()), FancyList())
        self.assertEqual(iterablate(FancyList(), also_wrap=list),
                         (FancyList(),))
        self.assertEqual(iterablate(FancyList(), also_wrap=FancyList),
                         (FancyList(),))
        self.assertEqual(iterablate([], also_wrap=FancyList), [])
        self.assertEqual(iterablate(1), (1,))
        self.assertEqual(iterablate('foo'), ('foo',))
        self.assertEqual(iterablate(('foo', 'bar')), ('foo', 'bar'))


class TestCheckUnboundCallableSignature(unittest.TestCase):

    def test_min_less_than_max(self):
        try:
            check_signature((lambda *args: None), min_args=0, max_args=2)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(ValueError):
            check_signature((lambda *args: None), min_args=3, max_args=2)

    def test_min_args_sufficient(self):
        c = lambda x, y, z=None, *args: None
        try:
            check_signature(c, min_args=2)
            check_signature(c, min_args=3)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature(c, min_args=0)
        with self.assertRaises(TypeError):
            check_signature(c, min_args=1)

    def test_max_args_fit(self):
        c = lambda x=None, y=None, z=None: None
        try:
            check_signature(c, max_args=0)
            check_signature(c, max_args=1)
            check_signature(c, max_args=2)
            check_signature(c, max_args=3)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature(c, max_args=4)
        with self.assertRaises(TypeError):
            check_signature(c)

    def test_num_args_values(self):
        try:
            check_signature((lambda x: None), num_args=1)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature((lambda x: None), min_args=1)
        with self.assertRaises(TypeError):
            check_signature((lambda x: None), max_args=1)
        with self.assertRaises(TypeError):
            check_signature((lambda x, y: None), num_args=1)
        with self.assertRaises(TypeError):
            check_signature((lambda: None), num_args=1)

    def test_min_default(self):
        try:
            check_signature((lambda: None), max_args=0)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature((lambda x: None), max_args=1)

    def test_max_default(self):
        try:
            check_signature((lambda *args: None), min_args=0)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature((lambda: None), min_args=0)


class TestCheckBoundCallableSignature(unittest.TestCase):

    def method_0(self):
        pass

    def method_1(self, arg1):
        pass

    def method_2(self, arg1, arg2):
        pass

    @classmethod
    def classmethod_0(cls):
        pass

    @classmethod
    def classmethod_1(cls, arg1):
        pass

    @classmethod
    def classmethod_2(cls, arg1, arg2):
        pass

    @staticmethod
    def staticmethod_0():
        pass

    @staticmethod
    def staticmethod_1(arg1):
        pass

    @staticmethod
    def staticmethod_2(arg1, arg2):
        pass

    def test_instance_methods(self):
        try:
            check_signature(self.method_0, num_args=0)
            check_signature(self.method_1, num_args=1)
            check_signature(self.method_2, num_args=2)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature(self.method_0, min_args=1)
        with self.assertRaises(TypeError):
            check_signature(self.method_1, min_args=2)
        with self.assertRaises(TypeError):
            check_signature(self.method_2, min_args=3)

    def test_class_methods(self):
        try:
            check_signature(self.classmethod_0, num_args=0)
            check_signature(self.classmethod_1, num_args=1)
            check_signature(self.classmethod_2, num_args=2)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature(self.classmethod_0, min_args=1)
        with self.assertRaises(TypeError):
            check_signature(self.classmethod_1, min_args=2)
        with self.assertRaises(TypeError):
            check_signature(self.classmethod_2, min_args=3)

    def test_static_methods(self):
        try:
            check_signature(self.staticmethod_0, num_args=0)
            check_signature(self.staticmethod_1, num_args=1)
            check_signature(self.staticmethod_2, num_args=2)
        except (TypeError, ValueError):
            self.fail()
        with self.assertRaises(TypeError):
            check_signature(self.staticmethod_0, min_args=1)
        with self.assertRaises(TypeError):
            check_signature(self.staticmethod_1, min_args=2)
        with self.assertRaises(TypeError):
            check_signature(self.staticmethod_2, min_args=3)


class AlwaysOne(object):

    def __call__(self, arg):
        pass


class ThreeToFive(object):

    def __call__(self, arg1, arg2, arg3, arg4=None, arg5=None):
        pass


class TestCheckCallableClassSignature(unittest.TestCase):

    def test_callable_objects(self):
        always_one = AlwaysOne()
        always_one('arg')
        with self.assertRaises(TypeError):
            check_signature(always_one)
        with self.assertRaises(TypeError):
            check_signature(always_one, min_args=2)
        with self.assertRaises(TypeError):
            check_signature(always_one, min_args=1, max_args=2)
        try:
            check_signature(always_one, num_args=1)
        except (TypeError, ValueError, AttributeError) as e:
            self.fail(e)

        three_to_five = ThreeToFive()
        with self.assertRaises(TypeError):
            check_signature(three_to_five)
        with self.assertRaises(TypeError):
            check_signature(three_to_five, min_args=2)
        with self.assertRaises(TypeError):
            check_signature(three_to_five, min_args=3, max_args=6)
        try:
            check_signature(three_to_five, num_args=3)
            check_signature(three_to_five, num_args=4)
            check_signature(three_to_five, num_args=5)
        except (TypeError, ValueError, AttributeError) as e:
            self.fail(e)


class TestWeaklyBoundCallable(unittest.TestCase):

    def setUp(self):
        self.dictionary = dict()

    def test_unbound(self):
        def my_func(arg):
            self.dictionary['my_func'] = arg
        my_lambda = lambda arg: arg

        weakly = WeaklyBoundCallable(my_func)
        weakly('arg')
        self.assertEqual(self.dictionary['my_func'], 'arg')
        weakly = WeaklyBoundCallable(my_lambda)
        self.assertEqual(weakly('arg'), 'arg')

    def test_bound(self):

        class MyClass(object):

            def my_method(iself, arg):
                self.dictionary['my_method'] = (iself, arg)
                return (iself, arg)

        my_instance = MyClass()
        my_ref = weakref.ref(my_instance)
        my_weakly_bound = WeaklyBoundCallable(my_instance.my_method)
        result = my_weakly_bound('arg')
        self.assertEqual(self.dictionary['my_method'], (my_instance, 'arg'))
        self.assertEqual(result, (my_instance, 'arg'))
        self.assertEqual(my_ref(), my_instance)
        del my_instance
        del self.dictionary['my_method']
        del result
        gc.collect()
        self.assertEqual(my_ref(), None)

    def test_reverted(self):

        class MyClass(object):

            def my_method(self):
                return self

            @classmethod
            def my_classmethod(cls):
                return cls

        def my_function(arg=None):
            return arg

        instance1 = MyClass()
        instance2 = MyClass()
        wbm1 = WeaklyBoundCallable(instance1.my_method)
        wbm2 = WeaklyBoundCallable(instance2.my_method)
        wbc0 = WeaklyBoundCallable(MyClass.my_classmethod)
        wbc1 = WeaklyBoundCallable(instance1.my_classmethod)
        wbc2 = WeaklyBoundCallable(instance2.my_classmethod)
        wbf0 = WeaklyBoundCallable(my_function)
        self.assertEqual(wbm1(), instance1)
        self.assertEqual(wbm2(), instance2)
        self.assertEqual(wbc0(), MyClass)
        self.assertEqual(wbc1(), MyClass)
        self.assertEqual(wbc2(), MyClass)
        self.assertEqual(my_function(), None)
        rvm1 = wbm1.reverted()
        rvm2 = wbm2.reverted()
        rvc0 = wbc1.reverted()
        rvc1 = wbc1.reverted()
        rvc2 = wbc2.reverted()
        rvf0 = wbf0.reverted()
        self.assertEqual(rvm1(), instance1)
        self.assertEqual(rvm2(), instance2)
        self.assertEqual(rvc0(), MyClass)
        self.assertEqual(rvc1(), MyClass)
        self.assertEqual(rvc2(), MyClass)
        self.assertEqual(rvf0(), None)
        self.assertEqual(rvm1, instance1.my_method)
        self.assertEqual(rvm2, instance2.my_method)
        self.assertEqual(rvc0, MyClass.my_classmethod)
        self.assertEqual(rvc1, instance1.my_classmethod)
        self.assertEqual(rvc2, instance2.my_classmethod)
        self.assertEqual(rvf0, my_function)

    def test_equality(self):

        class MyClass(object):

            def method_1(this):
                pass

            def method_2(this):
                pass

        instance_1 = MyClass()
        instance_2 = MyClass()
        wb_1_1 = WeaklyBoundCallable(instance_1.method_1)
        wb_1_2 = WeaklyBoundCallable(instance_1.method_2)
        wb_2_1 = WeaklyBoundCallable(instance_2.method_1)
        wb_2_2 = WeaklyBoundCallable(instance_2.method_2)
        self.assertFalse(wb_1_1 == wb_1_2)
        self.assertFalse(wb_1_1 == wb_2_1)
        self.assertFalse(wb_1_1 == wb_2_2)
        self.assertFalse(wb_2_1 == wb_1_2)
        self.assertFalse(wb_2_1 == wb_2_2)
        self.assertFalse(wb_2_2 == wb_1_2)
        self.assertTrue(wb_1_1 != wb_1_2)
        self.assertTrue(wb_1_1 != wb_2_1)
        self.assertTrue(wb_1_1 != wb_2_2)
        self.assertTrue(wb_2_1 != wb_1_2)
        self.assertTrue(wb_2_1 != wb_2_2)
        self.assertTrue(wb_2_2 != wb_1_2)
        wb_1_1_b = WeaklyBoundCallable(instance_1.method_1)
        self.assertTrue(wb_1_1 == wb_1_1_b)
        self.assertFalse(wb_1_1 != wb_1_1_b)
        wb_1_1_c = WeaklyBoundCallable(wb_1_1_b)
        self.assertTrue(wb_1_1 == wb_1_1_c)
        self.assertFalse(wb_1_1 != wb_1_1_c)
        dictionary = dict()
        dictionary[wb_1_1] = 'wb_1_1'
        dictionary[wb_1_1_b] = 'wb_1_1_b'
        dictionary[wb_1_1_c] = 'wb_1_1_c'
        self.assertEqual(len(dictionary), 1)
        self.assertEqual(dictionary[wb_1_1], 'wb_1_1_c')
        self.assertEqual(dictionary[wb_1_1_b], 'wb_1_1_c')
        self.assertEqual(dictionary[wb_1_1_c], 'wb_1_1_c')


class TestAttributeFactoryMixin(unittest.TestCase):

    def test_attribute_factory(self):

        class BaseMeta(type):

            def __getattribute__(cls, name):
                name = ('' if name[0] == '_' else 'b') + name
                return super(BaseMeta, cls).__getattribute__(name)

        class MidMeta(AttributeFactoryMixin, BaseMeta):

            def __getattribute__(cls, name):
                name = ('' if name[0] == '_' else 'm') + name
                return super(MidMeta, cls).__getattribute__(name)

        class FinMeta(MidMeta):

            def __getattribute__(cls, name):
                name = ('' if name[0] == '_' else 'f') + name
                return super(FinMeta, cls).__getattribute__(name)

        instances = {'count': 0}

        class MyClass(object):

            __metaclass__ = FinMeta

            def __new__(cls, name):
                instances['count'] += 1
                obj = super(MyClass, cls).__new__(cls)
                obj.value = name
                return obj

        foo = MyClass.foo
        self.assertEqual(instances['count'], 1)
        self.assertEqual(foo.value, "bmffoo")
        self.assertTrue(isinstance(foo, MyClass))
        self.assertIn('bmffoo', dir(MyClass))
        self.assertNotIn('foo', dir(MyClass))

        bar = MyClass.bar
        self.assertNotEqual(id(bar), id(foo))
        self.assertEqual(instances['count'], 2)
        self.assertEqual(bar.value, "bmfbar")
        self.assertTrue(isinstance(bar, MyClass))
        self.assertIn('bmfbar', dir(MyClass))
        self.assertNotIn('bar', dir(MyClass))

        new_foo = MyClass.foo
        self.assertEqual(id(new_foo), id(foo))
        self.assertEqual(instances['count'], 2)
        self.assertEqual(new_foo.value, "bmffoo")
        self.assertTrue(isinstance(new_foo, MyClass))
        self.assertIn('bmffoo', dir(MyClass))
        self.assertNotIn('new_foo', dir(MyClass))


class TestEnumishMixins(unittest.TestCase):

    def test_enumish_str_mixin(self):

        instances = {'count': 0}

        class MyStrEnum(EnumishStr):
            _values = ["ADAM", "EVE", "CAIN"]
            newcount = 0

        adam = MyStrEnum.ADAM
        self.assertEqual(adam, "ADAM")
        self.assertEqual(adam.str, "ADAM")
        self.assertEqual(adam.int, 0)
        self.assertTrue(isinstance(adam, MyStrEnum))
        self.assertIn('ADAM', dir(MyStrEnum))

        eve = MyStrEnum(u"EVE")
        self.assertEqual(eve, "EVE")
        self.assertEqual(eve.str, "EVE")
        self.assertEqual(eve.int, 1)
        self.assertTrue(isinstance(eve, MyStrEnum))
        self.assertIn('EVE', dir(MyStrEnum))

        cain = MyStrEnum(2)
        self.assertEqual(cain, "CAIN")
        self.assertEqual(cain.str, "CAIN")
        self.assertEqual(cain.int, 2)
        self.assertTrue(isinstance(cain, MyStrEnum))
        self.assertIn('CAIN', dir(MyStrEnum))

        self.assertEqual(MyStrEnum.values, [MyStrEnum.ADAM, MyStrEnum.EVE,
                                            MyStrEnum.CAIN])
        self.assertTrue(all(type(v) == MyStrEnum for v in MyStrEnum.values))

        with self.assertRaises(AttributeError):
            abel = MyStrEnum.ABEL
        with self.assertRaises(AttributeError):
            abel = MyStrEnum("ABEL")
        with self.assertRaises(AttributeError):
            abel = MyStrEnum(3)
        MyStrEnum._add_value_("ABEL")
        with self.assertRaises(ValueError):
            MyStrEnum._add_value_("ABEL")
        abel = MyStrEnum.ABEL
        self.assertEqual(abel, "ABEL")
        self.assertEqual(abel.str, "ABEL")
        self.assertEqual(abel.int, 3)
        self.assertTrue(isinstance(abel, MyStrEnum))
        self.assertIn('ABEL', dir(MyStrEnum))

        self.assertEqual(MyStrEnum.values, [MyStrEnum.ADAM, MyStrEnum.EVE,
                                            MyStrEnum.CAIN, MyStrEnum.ABEL])
        self.assertTrue(all(type(v) == MyStrEnum for v in MyStrEnum.values))

        MyStrEnum._remove_value_("ABEL")
        with self.assertRaises(ValueError):
            MyStrEnum._remove_value_("ABEL")
        with self.assertRaises(AttributeError):
            abel = MyStrEnum.ABEL
        with self.assertRaises(AttributeError):
            abel = MyStrEnum("ABEL")
        with self.assertRaises(AttributeError):
            abel = MyStrEnum(3)
        self.assertNotIn('ABEL', dir(MyStrEnum))

        self.assertEqual(MyStrEnum.values, [MyStrEnum.ADAM, MyStrEnum.EVE,
                                            MyStrEnum.CAIN])
        self.assertTrue(all(type(v) == MyStrEnum for v in MyStrEnum.values))



        new_adam = MyStrEnum("ADAM")
        self.assertEqual(id(new_adam), id(adam))
        new_adam = MyStrEnum(0)
        self.assertEqual(id(new_adam), id(adam))

    def test_enumish_int_mixin(self):

        instances = {'count': 0}

        class MyIntEnum(EnumishInt):
            _values = ["ADAM", "EVE", "CAIN"]
            newcount = 0

        adam = MyIntEnum.ADAM
        self.assertEqual(adam, 0)
        self.assertEqual(adam.str, "ADAM")
        self.assertEqual(adam.int, 0)
        self.assertTrue(isinstance(adam, MyIntEnum))
        self.assertIn('ADAM', dir(MyIntEnum))

        eve = MyIntEnum(u"EVE")
        self.assertEqual(eve, 1)
        self.assertEqual(eve.str, "EVE")
        self.assertEqual(eve.int, 1)
        self.assertTrue(isinstance(eve, MyIntEnum))
        self.assertIn('EVE', dir(MyIntEnum))

        cain = MyIntEnum(2)
        self.assertEqual(cain, 2)
        self.assertEqual(cain.str, "CAIN")
        self.assertEqual(cain.int, 2)
        self.assertTrue(isinstance(cain, MyIntEnum))
        self.assertIn('CAIN', dir(MyIntEnum))

        self.assertEqual(MyIntEnum.values, [MyIntEnum.ADAM, MyIntEnum.EVE,
                                            MyIntEnum.CAIN])
        self.assertTrue(all(type(v) == MyIntEnum for v in MyIntEnum.values))

        with self.assertRaises(AttributeError):
            abel = MyIntEnum.ABEL
        with self.assertRaises(AttributeError):
            abel = MyIntEnum("ABEL")
        with self.assertRaises(AttributeError):
            abel = MyIntEnum(3)
        MyIntEnum._add_value_("ABEL")
        with self.assertRaises(ValueError):
            MyIntEnum._add_value_("ABEL")
        abel = MyIntEnum.ABEL
        self.assertEqual(abel, 3)
        self.assertEqual(abel.str, "ABEL")
        self.assertEqual(abel.int, 3)
        self.assertTrue(isinstance(abel, MyIntEnum))
        self.assertIn('ABEL', dir(MyIntEnum))

        self.assertEqual(MyIntEnum.values, [MyIntEnum.ADAM, MyIntEnum.EVE,
                                            MyIntEnum.CAIN, MyIntEnum.ABEL])
        self.assertTrue(all(type(v) == MyIntEnum for v in MyIntEnum.values))

        MyIntEnum._remove_value_("ABEL")
        with self.assertRaises(ValueError):
            MyIntEnum._remove_value_("ABEL")
        with self.assertRaises(AttributeError):
            abel = MyIntEnum.ABEL
        with self.assertRaises(AttributeError):
            abel = MyIntEnum("ABEL")
        with self.assertRaises(AttributeError):
            abel = MyIntEnum(3)
        self.assertNotIn('ABEL', dir(MyIntEnum))

        self.assertEqual(MyIntEnum.values, [MyIntEnum.ADAM, MyIntEnum.EVE,
                                            MyIntEnum.CAIN])
        self.assertTrue(all(type(v) == MyIntEnum for v in MyIntEnum.values))

        new_adam = MyIntEnum("ADAM")
        self.assertEqual(id(new_adam), id(adam))
        new_adam = MyIntEnum(0)
        self.assertEqual(id(new_adam), id(adam))


if __name__ == '__main__':
    unittest.main()
