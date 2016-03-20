from unittest import TestCase


class LoadingModulesTests(TestCase):

    def test_class_oebbook_loaded_properly(self):
        # try:
        from calibre.ebooks.oeb.base import OEBBook
        oeb_book = OEBBook
        print(oeb_book)
        # except Exception as e:
        #     self.fail(str(e))
