#!/usr/bin/env python2
# vim:fileencoding=utf-8
# License: GPLv3 Copyright: 2015, Kovid Goyal <kovid at kovidgoyal.net>

from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

from collections import OrderedDict
from functools import partial

from PyQt5.Qt import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QIcon,
    QSize, QComboBox, QLineEdit, QListWidgetItem, QStyledItemDelegate,
    QStaticText, Qt, QStyle, QToolButton, QInputDialog, QMenu
)

from calibre.ebooks.metadata.tag_mapper import map_tags, compile_pat
from calibre.gui2 import error_dialog, elided_text, Application, question_dialog
from calibre.gui2.widgets2 import Dialog
from calibre.utils.config import JSONConfig

tag_maps = JSONConfig('tag-map-rules')

class RuleEdit(QWidget):

    ACTION_MAP = OrderedDict((
                ('remove', _('Remove')),
                ('replace', _('Replace')),
                ('keep', _('Keep')),
                ('capitalize', _('Capitalize')),
                ('lower', _('Lower-case')),
                ('upper', _('Upper-case')),
    ))

    MATCH_TYPE_MAP = OrderedDict((
                ('one_of', _('is one of')),
                ('not_one_of', _('is not one of')),
                ('matches', _('matches pattern')),
                ('not_matches', _('does not match pattern'))
    ))

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.l = l = QVBoxLayout(self)
        self.h = h = QHBoxLayout()

        self.la = la = QLabel(_(
            'Create the rule below, the rule can be used to remove or replace tags'))
        la.setWordWrap(True)
        l.addWidget(la)
        l.addLayout(h)
        self.action = a = QComboBox(self)
        h.addWidget(a)
        for action, text in self.ACTION_MAP.iteritems():
            a.addItem(text, action)
        a.currentIndexChanged.connect(self.update_state)
        self.la1 = la = QLabel('\xa0' + _('the tag, if it') + '\xa0')
        h.addWidget(la)
        self.match_type = q = QComboBox(self)
        h.addWidget(q)
        for action, text in self.MATCH_TYPE_MAP.iteritems():
            q.addItem(text, action)
        q.currentIndexChanged.connect(self.update_state)
        self.la2 = la = QLabel(':\xa0')
        h.addWidget(la)
        self.query = q = QLineEdit(self)
        h.addWidget(q)
        self.h2 = h = QHBoxLayout()
        l.addLayout(h)
        self.la3 = la = QLabel(_('with the tag:') + '\xa0')
        h.addWidget(la)
        self.replace = r = QLineEdit(self)
        h.addWidget(r)
        l.addStretch(10)
        self.update_state()

    def sizeHint(self):
        a = QWidget.sizeHint(self)
        a.setHeight(a.height() + 75)
        a.setWidth(a.width() + 100)
        return a

    def update_state(self):
        replace = self.action.currentData() == 'replace'
        self.la3.setVisible(replace), self.replace.setVisible(replace)
        tt = _('A comma separated list of tags')
        if 'matches' in self.match_type.currentData():
            tt = _('A regular expression')
        self.query.setToolTip(tt)

    @property
    def rule(self):
        return {
            'action': self.action.currentData(),
            'match_type': self.match_type.currentData(),
            'query': self.query.text().strip(),
            'replace': self.replace.text().strip(),
        }

    @rule.setter
    def rule(self, rule):
        def sc(name):
            c = getattr(self, name)
            idx = c.findData(unicode(rule.get(name, '')))
            if idx < 0:
                idx = 0
            c.setCurrentIndex(idx)
        sc('action'), sc('match_type')
        self.query.setText(unicode(rule.get('query', '')).strip())
        self.replace.setText(unicode(rule.get('replace', '')).strip())

    def validate(self):
        rule = self.rule
        if not rule['query']:
            error_dialog(self, _('Query required'), _(
                'You must provide a value for the tag to match'), show=True)
            return False
        if 'matches' in rule['match_type']:
            try:
                compile_pat(rule['query'])
            except Exception:
                error_dialog(self, _('Query invalid'), _(
                    '%s is not a valid regular expression') % rule['query'], show=True)
                return False
        return True

class RuleEditDialog(Dialog):

    def __init__(self, parent=None):
        Dialog.__init__(self, _('Edit rule'), 'edit-tag-mapper-rule', parent=None)

    def setup_ui(self):
        self.l = l = QVBoxLayout(self)
        self.edit_widget = w = RuleEdit(self)
        l.addWidget(w)
        l.addWidget(self.bb)

    def accept(self):
        if self.edit_widget.validate():
            Dialog.accept(self)

DATA_ROLE = Qt.UserRole
RENDER_ROLE = DATA_ROLE + 1

class RuleItem(QListWidgetItem):

    @staticmethod
    def text_from_rule(rule, parent):
        query = elided_text(rule['query'], font=parent.font(), width=200, pos='right')
        text = _(
            '<b>{action}</b> the tag, if it <i>{match_type}</i>: <b>{query}</b>').format(
                action=RuleEdit.ACTION_MAP[rule['action']], match_type=RuleEdit.MATCH_TYPE_MAP[rule['match_type']], query=query)
        if rule['action'] == 'replace':
            text += '<br>' + _('with the tag:') + ' <b>%s</b>' % rule['replace']
        return text

    def __init__(self, rule, parent):
        QListWidgetItem.__init__(self, '', parent)
        st = self.text_from_rule(rule, parent)
        self.setData(RENDER_ROLE, st)
        self.setData(DATA_ROLE, rule)

class Delegate(QStyledItemDelegate):

    MARGIN = 16

    def sizeHint(self, option, index):
        st = QStaticText(index.data(RENDER_ROLE))
        st.prepare(font=self.parent().font())
        width = max(option.rect.width(), self.parent().width() - 50)
        if width and width != st.textWidth():
            st.setTextWidth(width)
        br = st.size()
        return QSize(br.width(), br.height() + self.MARGIN)

    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)
        pal = option.palette
        color = pal.color(pal.HighlightedText if option.state & QStyle.State_Selected else pal.Text).name()
        text = '<div style="color:%s">%s</div>' % (color, index.data(RENDER_ROLE))
        st = QStaticText(text)
        st.setTextWidth(option.rect.width())
        painter.drawStaticText(option.rect.left() + self.MARGIN // 2, option.rect.top() + self.MARGIN // 2, st)


class Rules(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.l = l = QVBoxLayout(self)

        self.msg_label = la = QLabel(
            '<p>' + _('You can specify rules to filter/transform tags here. Click the "Add Rule" button'
            ' below to get started. The rules will be processed in order for every tag until either a'
            ' "remove" or a "keep" rule matches.') + '<p>' + _(
            'You can <b>change an existing rule</b> by double clicking it')
        )
        la.setWordWrap(True)
        l.addWidget(la)
        self.h = h = QHBoxLayout()
        l.addLayout(h)
        self.add_button = b = QPushButton(QIcon(I('plus.png')), _('&Add rule'), self)
        b.clicked.connect(self.add_rule)
        h.addWidget(b)
        self.remove_button = b = QPushButton(QIcon(I('minus.png')), _('&Remove rule(s)'), self)
        b.clicked.connect(self.remove_rules)
        h.addWidget(b)
        self.h3 = h = QHBoxLayout()
        l.addLayout(h)
        self.rule_list = r = QListWidget(self)
        self.delegate = Delegate(self)
        r.setSelectionMode(r.ExtendedSelection)
        r.setItemDelegate(self.delegate)
        r.doubleClicked.connect(self.edit_rule)
        h.addWidget(r)
        r.setDragEnabled(True)
        r.viewport().setAcceptDrops(True)
        r.setDropIndicatorShown(True)
        r.setDragDropMode(r.InternalMove)
        r.setDefaultDropAction(Qt.MoveAction)
        self.l2 = l = QVBoxLayout()
        h.addLayout(l)
        self.up_button = b = QToolButton(self)
        b.setIcon(QIcon(I('arrow-up.png'))), b.setToolTip(_('Move current rule up'))
        b.clicked.connect(self.move_up)
        l.addWidget(b)
        self.down_button = b = QToolButton(self)
        b.setIcon(QIcon(I('arrow-down.png'))), b.setToolTip(_('Move current rule down'))
        b.clicked.connect(self.move_down)
        l.addStretch(10), l.addWidget(b)

    def sizeHint(self):
        return QSize(800, 600)

    def add_rule(self):
        d = RuleEditDialog(self)
        if d.exec_() == d.Accepted:
            i = RuleItem(d.edit_widget.rule, self.rule_list)
            self.rule_list.scrollToItem(i)

    def edit_rule(self):
        i = self.rule_list.currentItem()
        if i is not None:
            d = RuleEditDialog(self)
            d.edit_widget.rule = i.data(Qt.UserRole)
            if d.exec_() == d.Accepted:
                rule = d.edit_widget.rule
                i.setData(DATA_ROLE, rule)
                i.setData(RENDER_ROLE, RuleItem.text_from_rule(rule, self.rule_list))

    def remove_rules(self):
        for item in self.rule_list.selectedItems():
            self.rule_list.takeItem(self.rule_list.row(item))

    def move_up(self):
        i = self.rule_list.currentItem()
        if i is not None:
            row = self.rule_list.row(i)
            if row > 0:
                self.rule_list.takeItem(row)
                self.rule_list.insertItem(row - 1, i)
                self.rule_list.setCurrentItem(i)

    def move_down(self):
        i = self.rule_list.currentItem()
        if i is not None:
            row = self.rule_list.row(i)
            if row < self.rule_list.count() - 1:
                self.rule_list.takeItem(row)
                self.rule_list.insertItem(row + 1, i)
                self.rule_list.setCurrentItem(i)

    @property
    def rules(self):
        ans = []
        for r in xrange(self.rule_list.count()):
            ans.append(self.rule_list.item(r).data(DATA_ROLE))
        return ans

    @rules.setter
    def rules(self, rules):
        self.rule_list.clear()
        for rule in rules:
            if 'action' in rule and 'match_type' in rule and 'query' in rule:
                RuleItem(rule, self.rule_list)

class Tester(Dialog):

    def __init__(self, rules, parent=None):
        self.rules = rules
        Dialog.__init__(self, _('Test tag mapper rules'), 'test-tag-mapper-rules', parent=parent)

    def setup_ui(self):
        self.l = l = QVBoxLayout(self)
        self.bb.setStandardButtons(self.bb.Close)
        self.la = la = QLabel(_(
            'Enter a comma separated list of &tags to test:'))
        l.addWidget(la)
        self.tags = t = QLineEdit(self)
        la.setBuddy(t)
        t.setPlaceholderText(_('Enter tags and click the Test button'))
        self.h = h = QHBoxLayout()
        l.addLayout(h)
        h.addWidget(t)
        self.test_button = b = QPushButton(_('&Test'), self)
        b.clicked.connect(self.do_test)
        h.addWidget(b)
        self.result = la = QLabel(self)
        la.setWordWrap(True)
        la.setText('<p>&nbsp;<br>&nbsp;</p>')
        l.addWidget(la)
        l.addWidget(self.bb)

    def do_test(self):
        tags = [x.strip() for x in self.tags.text().split(',')]
        tags = map_tags(tags, self.rules)
        self.result.setText(_('<b>Resulting tags:</b> %s') % ', '.join(tags))


class RulesDialog(Dialog):

    def __init__(self, parent=None):
        self.loaded_ruleset = None
        Dialog.__init__(self, _('Edit tag mapper rules'), 'edit-tag-mapper-rules', parent=parent)

    def setup_ui(self):
        self.l = l = QVBoxLayout(self)
        self.edit_widget = w = Rules(self)
        l.addWidget(w)
        l.addWidget(self.bb)
        self.save_button = b = self.bb.addButton(_('&Save'), self.bb.ActionRole)
        b.setToolTip(_('Save this ruleset for later re-use'))
        b.clicked.connect(self.save_ruleset)
        self.load_button = b = self.bb.addButton(_('&Load'), self.bb.ActionRole)
        b.setToolTip(_('Load a previously saved ruleset'))
        self.load_menu = QMenu(self)
        b.setMenu(self.load_menu)
        self.build_load_menu()
        self.test_button = b = self.bb.addButton(_('&Test rules'), self.bb.ActionRole)
        b.clicked.connect(self.test_rules)

    @property
    def rules(self):
        return self.edit_widget.rules

    @rules.setter
    def rules(self, rules):
        self.edit_widget.rules = rules

    def save_ruleset(self):
        if not self.rules:
            error_dialog(self, _('No rules'), _(
                'Cannot save as no rules have been created'), show=True)
            return
        text, ok = QInputDialog.getText(self, _('Save ruleset as'), _(
            'Enter a name for this ruleset:'), text=self.loaded_ruleset or '')
        if ok and text:
            if self.loaded_ruleset and text == self.loaded_ruleset:
                if not question_dialog(self, _('Are you sure?'), _(
                        'A ruleset with the name "%s" already exists, do you want to replace it?') % text):
                    return
                self.loaded_ruleset = text
            rules = self.rules
            if rules:
                tag_maps[text] = self.rules
            elif text in tag_maps:
                del tag_maps[text]
            self.build_load_menu()

    def build_load_menu(self):
        self.load_menu.clear()
        if len(tag_maps):
            for name, rules in tag_maps.iteritems():
                self.load_menu.addAction(name).triggered.connect(partial(self.load_ruleset, name))
            self.load_menu.addSeparator()
            m = self.load_menu.addMenu(_('Delete saved rulesets'))
            for name, rules in tag_maps.iteritems():
                m.addAction(name).triggered.connect(partial(self.delete_ruleset, name))
        else:
            self.load_menu.addAction(_('No saved rulesets available'))

    def load_ruleset(self, name):
        self.rules = tag_maps[name]
        self.loaded_ruleset = name

    def delete_ruleset(self, name):
        del tag_maps[name]
        self.build_load_menu()

    def test_rules(self):
        Tester(self.rules, self).exec_()

if __name__ == '__main__':
    app = Application([])
    d = RulesDialog()
    d.rules = [
        {'action':'remove', 'query':'moose', 'match_type':'one_of', 'replace':''},
        {'action':'replace', 'query':'moose', 'match_type':'one_of', 'replace':'xxxx'},
    ]
    d.exec_()
    from pprint import pprint
    pprint(d.rules)
    del d, app
