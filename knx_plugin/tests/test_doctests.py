import doctest
import unittest
import knx_plugin


tests = list()
tests.append(doctest.DocTestSuite("knx_plugin.gateway"))
tests.append(doctest.DocTestSuite("knx_plugin.message"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.mean"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.custom_clima"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_wsp"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_temp"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_power"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_lux"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_lux.balance"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_power.consumption"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_value_power.production"))
tests.append(doctest.DocTestSuite("knx_plugin.trigger.dpt_control_dimming"))
tests.append(doctest.DocTestSuite("knx_plugin.command.custom_clima"))
tests.append(doctest.DocTestSuite("knx_plugin.command.dpt_brightness"))
tests.append(doctest.DocTestSuite("knx_plugin.command.dpt_switch"))

tests.append(doctest.DocFileSuite("../docs/source/index.rst", package=knx_plugin))


def load_tests(loader, suite, ignore):
    for test in tests:
        suite.addTests(test)
    return suite


suite = unittest.TestSuite()
[suite.addTests(test) for test in tests]
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
