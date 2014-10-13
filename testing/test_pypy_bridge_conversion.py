from testing.test_interpreter import MockInterpreter, BaseTestInterpreter

import pytest

class TestPyPyBridgeConversions(BaseTestInterpreter):
    """ Interpreter level conversion code tests """

    def new_interp(self):
        return self.engine.new_interp(None, None)

    def test_py_int_of_ph_integer(self):
        interp = self.new_interp()
        w_php_integer = interp.space.newint(666)
        py_int = w_php_integer.to_py(interp)
        assert interp.py_space.int_w(py_int) == 666

    def test_py_none_of_ph_null(self):
        interp = self.new_interp()
        w_py_none = interp.space.w_Null.to_py(interp)
        assert w_py_none is interp.py_space.w_None

    def test_py_str_of_ph_string(self):
        interp = self.new_interp()
        w_php_string = interp.space.wrap("smeg")
        w_py_str = w_php_string.to_py(interp)
        assert interp.py_space.str_w(w_py_str) == "smeg"

    def test_py_str_of_ph_string2(self):
        interp = self.new_interp()
        w_php_string = interp.space.wrap("123") # can be interpreted as int
        w_py_str = w_php_string.to_py(interp)
        assert interp.py_space.str_w(w_py_str) == "123"

    def test_py_float_of_ph_float(self):
        interp = self.new_interp()
        w_php_float = interp.space.wrap(1.337)
        w_py_float = w_php_float.to_py(interp)
        assert interp.py_space.float_w(w_py_float) == 1.337

    def test_py_bool_of_ph_boolean(self):
        interp = self.new_interp()
        for polarity in [True, False]:
            w_php_boolean = interp.space.wrap(polarity)
            w_py_bool = w_php_boolean.to_py(interp)
            assert interp.py_space.bool_w(w_py_bool) == polarity

    def test_unwrap_php(self):
        php_space = self.space
        output = self.run('''
        $src = <<<EOD
        def dummy(x):
            return x
        EOD;
        $dummy = embed_py_func($src);

        class C { }
        $x = new C();
        echo($dummy($x) === $x);
        ''')
        assert php_space.is_true(output[0])

    def test_ph_integer_of_py_int(self):
        interp = self.new_interp()
        py_int = interp.py_space.newint(666)
        w_php_integer = py_int.to_php(interp)
        assert interp.space.int_w(w_php_integer) == 666
        assert w_php_integer.tp == interp.space.tp_int

    def test_ph_float_of_py_float(self):
        interp = self.new_interp()
        py_float = interp.py_space.newfloat(3.1415)
        w_php_float = py_float.to_php(interp)
        assert interp.space.float_w(w_php_float) == 3.1415
        assert w_php_float.tp == interp.space.tp_float

    def test_ph_null_of_py_none(self):
        interp = self.new_interp()
        w_php_null = interp.py_space.w_None.to_php(interp)
        assert w_php_null is interp.space.w_Null
        assert w_php_null.tp == interp.space.tp_null

    def test_ph_string_of_py_str(self):
        interp = self.new_interp()
        w_py_str = interp.py_space.wrap("transmogrification")
        w_php_string = w_py_str.to_php(interp)
        assert interp.space.str_w(w_php_string) == "transmogrification"
        assert w_php_string.tp == interp.space.tp_str

    def test_ph_boolean_of_py_bool(self):
        interp = self.new_interp()
        for b in [True, False]:
            w_py_bool = interp.py_space.wrap(b)
            w_php_boolean = w_py_bool.to_php(interp)
            assert w_php_boolean.boolval == b
            assert w_php_boolean.tp == interp.space.tp_bool

    # XXX List slices
    # XXX Test mutating the list.

    def test_unwrap_py(self):
        php_space = self.space
        output = self.run('''
        function dummy($x) {
            return $x;
        }

        $src = <<<EOD
        def tst():
            class C: pass
            x = C()
            print x, dummy(x)
            return x is dummy(x)
        EOD;
        $tst = embed_py_func($src);

        echo($tst());
        ''')
        assert php_space.is_true(output[0])

    def test_php_null(self):
        php_space = self.space
        output = self.run('''
        $src = <<<EOD
        def n():
            return None
        EOD;
        $n = embed_py_func($src);

        echo(null === $n());
        ''')
        assert php_space.is_true(output[0])

    def test_wrapped_php_instance_attributeerror(self):
        php_space = self.space
        output = self.run('''
        class A {};

        $src = <<<EOD
        def f(a):
            try:
                x = a.no_exist
            except BridgeError as e:
                return e.message
            return "test failed"
        EOD;
        $f = embed_py_func($src);

        $inst = new A();
        echo $f($inst);
        ''')
        err_s = "Wrapped PHP instance has no attribute 'no_exist'"
        assert php_space.str_w(output[0]) == err_s

    def test_using_kwargs_to_a_php_func_raises(self):
        php_space = self.space
        output = self.run('''
        function php_func($a) {
        }

        $src = <<<EOD
        def py_func():
            try:
                php_func(a=1)
                return "test fail"
            except BridgeError as e:
                return e.message
        EOD;
        $py_func = embed_py_func($src);
        echo($py_func());
        ''')
        err_s = "Cannot use kwargs when calling PHP functions"
        assert php_space.str_w(output[0]) == err_s

    def test_calling_callable_php_inst_in_py(self):
        php_space = self.space
        output = self.run('''
        class A {
                function __invoke() {
                    return "invoked";
                }
        };

        $src = <<<EOD
        def py_func(inst):
            return inst()
        EOD;
        $py_func = embed_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        assert php_space.str_w(output[0]) == "invoked"

    def test_calling_callable_php_inst_with_args_in_py(self):
        php_space = self.space
        output = self.run('''
        class A {
                function __invoke($x, $y) {
                    return $x . $y;
                }
        };

        $src = <<<EOD
        def py_func(inst):
            return inst("abc", "123")
        EOD;
        $py_func = embed_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        assert php_space.str_w(output[0]) == "abc123"

    def test_calling_a_non_callable_php_instance_in_py_raises(self):
        php_space = self.space
        output = self.run('''
        class A {
                // has no __invoke
        };

        $src = <<<EOD
        def py_func(inst):
            try:
                return inst()
                return "fail"
            except BridgeError as e:
                return e.message
        EOD;
        $py_func = embed_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        err_s = "Wrapped PHP instance is not callable"
        assert php_space.str_w(output[0]) == err_s


    def test_calling_a_callable_php_instance_with_kwargs_in_py_raises(self):
        php_space = self.space
        output = self.run('''
        class A {
                function __invoke($x) { }
        };

        $src = <<<EOD
        def py_func(inst):
            try:
                return inst(x=1)
                return "fail"
            except BridgeError as e:
                return e.message
        EOD;
        $py_func = embed_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        err_s = "Cannot use kwargs with callable PHP instances"
        assert php_space.str_w(output[0]) == err_s

    @pytest.mark.xfail
    def test_py_module_is_stringable(self):
        php_space = self.space
        output = self.run('''
        $m = import_py_mod("os");
        echo($m); // crashes
        ''')
        err_s = "XXX" # decide what it should say XXX
        assert php_space.str_w(output[0]) == err_s
