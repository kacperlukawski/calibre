from unittest import TestCase


class LoadingModulesTests(TestCase):
    """
    A suite of tests checking if the modules can be loaded properly
    """

    def test_class_htmlinput_loaded_properly(self):
        try:
            from calibre.ebooks.conversion.plugins.html_input import HTMLInput
            html_input = HTMLInput
            self.assertEqual("<class 'calibre.ebooks.conversion.plugins.html_input.HTMLInput'>", str(html_input))
        except Exception as e:
            self.fail(str(e))

    def test_class_mobioutput_loaded_properly(self):
        try:
            from calibre.ebooks.conversion.plugins.mobi_output import MOBIOutput
            mobi_output = MOBIOutput
            self.assertEqual("<class 'calibre.ebooks.conversion.plugins.mobi_output.MOBIOutput'>", str(mobi_output))
        except Exception as e:
            self.fail(str(e))
