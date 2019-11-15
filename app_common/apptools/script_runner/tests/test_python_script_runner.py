from unittest import TestCase

from app_common.apptools.script_runner.python_script_runner import \
    PythonScriptRunner


class TestPythonScriptRunner(TestCase):
    def test_create_run_empty_no_app(self):
        runner = PythonScriptRunner()
        with self.assertRaises(ValueError):
            # Fail because no application was provided
            runner.run()

    def test_create_run_empty_default_app(self):
        app = instantiate_app()
        runner = PythonScriptRunner(app=app)
        runner.run()

    def test_create_run_trivial_default_app(self):
        app = instantiate_app()
        runner = PythonScriptRunner(app=app, code="print('foo')")
        runner.run()

    def test_create_run_access_app_in_context(self):
        app = instantiate_app()
        runner = PythonScriptRunner(app=app, code="print(app)")
        runner.run()
        self.assertIs(runner.context["app"], app)

    def test_create_run_add_to_context(self):
        app = instantiate_app()
        runner = PythonScriptRunner(app=app, code="x = 1")
        runner.run()
        self.assertEqual(runner.context["x"], 1)


def instantiate_app():
    class FakeApp(object):
        pass
    app = FakeApp()
    return app
