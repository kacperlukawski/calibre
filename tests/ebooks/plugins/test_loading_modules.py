from unittest import TestCase


class LoadingModulesTests(TestCase):
    """
    A suite of tests checking if the modules can be loaded properly
    """

    def test_class_htmlinput_loaded_properly(self):
        try:
            from calibre.ebooks.conversion.plugins.html_input import HTMLInput
            html_input = HTMLInput
            print(html_input)
        except Exception as e:
            self.fail(str(e))

    def test_class_mobioutput_loaded_properly(self):
        try:
            from calibre.ebooks.conversion.plugins.mobi_output import MOBIOutput
            mobi_output = MOBIOutput
            print(mobi_output)
        except Exception as e:
            self.fail(str(e))
