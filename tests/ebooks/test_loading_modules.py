from unittest import TestCase


class LoadingModulesTests(TestCase):

    def test_class_oebbook_loaded_properly(self):
        try:
            from calibre.ebooks.oeb.base import OEBBook
            oeb_book = OEBBook
            self.assertEqual("<class 'calibre.ebooks.oeb.base.OEBBook'>", str(oeb_book))
        except Exception as e:
            self.fail(str(e))

    def test_method_get_metadata_loaded_properly(self):
        # try:
        from calibre.ebooks.metadata.html import get_metadata
        method = get_metadata
        print(method)
        # except Exception as e:
        #     self.fail(str(e))
