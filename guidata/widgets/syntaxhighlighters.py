# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Editor widget syntax highlighters based on QtGui.QSyntaxHighlighter
(Python syntax highlighting rules are inspired from idlelib)
"""


import builtins
import keyword
import re

from guidata.config import CONF, _
from qtpy.QtWidgets import (
    QApplication,
)
from qtpy.QtGui import (
    QColor,
    QCursor,
    QFont,
    QTextCharFormat,
    QTextOption,
    QSyntaxHighlighter,
)
from qtpy.QtCore import Qt

# =============================================================================
# Constants
# =============================================================================
COLOR_SCHEME_KEYS = {
    "background": _("Background:"),
    "currentline": _("Current line:"),
    "currentcell": _("Current cell:"),
    "occurrence": _("Occurrence:"),
    "ctrlclick": _("Link:"),
    "sideareas": _("Side areas:"),
    "matched_p": _("Matched <br>parens:"),
    "unmatched_p": _("Unmatched <br>parens:"),
    "normal": _("Normal text:"),
    "keyword": _("Keyword:"),
    "builtin": _("Builtin:"),
    "definition": _("Definition:"),
    "comment": _("Comment:"),
    "string": _("String:"),
    "number": _("Number:"),
    "instance": _("Instance:"),
}
COLOR_SCHEME_NAMES = CONF.get("color_schemes", "names")
# Mapping for file extensions that use Pygments highlighting but should use
# different lexers than Pygments' autodetection suggests.  Keys are file
# extensions or tuples of extensions, values are Pygments lexer names.


# ==============================================================================
# Auxiliary functions
# ==============================================================================
def get_color_scheme(name):
    """Get a color scheme from config using its name"""
    name = name.lower()
    scheme = {}
    for key in COLOR_SCHEME_KEYS:
        try:
            scheme[key] = CONF.get("color_schemes", name + "/" + key)
        except:
            scheme[key] = CONF.get("color_schemes", "spyder/" + key)
    return scheme


# ==============================================================================
# Syntax highlighting color schemes
# ==============================================================================
class BaseSH(QSyntaxHighlighter):
    """Base Syntax Highlighter Class"""

    # Syntax highlighting rules:
    PROG = None
    BLANKPROG = re.compile(r"\s+")
    # Syntax highlighting states (from one text block to another):
    NORMAL = 0
    # Syntax highlighting parameters.
    BLANK_ALPHA_FACTOR = 0.31

    def __init__(self, parent, font=None, color_scheme=None):
        QSyntaxHighlighter.__init__(self, parent)

        self.font = font
        if color_scheme is None:
            color_scheme = CONF.get("color_schemes", "default")
        if isinstance(color_scheme, str):
            self.color_scheme = get_color_scheme(color_scheme)
        else:
            self.color_scheme = color_scheme

        self.background_color = None
        self.currentline_color = None
        self.currentcell_color = None
        self.occurrence_color = None
        self.ctrlclick_color = None
        self.sideareas_color = None
        self.matched_p_color = None
        self.unmatched_p_color = None

        self.formats = None
        self.setup_formats(font)

        self.cell_separators = None

    def get_background_color(self):
        """

        :return:
        """
        return QColor(self.background_color)

    def get_foreground_color(self):
        """Return foreground ('normal' text) color"""
        return self.formats["normal"].foreground().color()

    def get_currentline_color(self):
        """

        :return:
        """
        return QColor(self.currentline_color)

    def get_currentcell_color(self):
        """

        :return:
        """
        return QColor(self.currentcell_color)

    def get_occurrence_color(self):
        """

        :return:
        """
        return QColor(self.occurrence_color)

    def get_ctrlclick_color(self):
        """

        :return:
        """
        return QColor(self.ctrlclick_color)

    def get_sideareas_color(self):
        """

        :return:
        """
        return QColor(self.sideareas_color)

    def get_matched_p_color(self):
        """

        :return:
        """
        return QColor(self.matched_p_color)

    def get_unmatched_p_color(self):
        """

        :return:
        """
        return QColor(self.unmatched_p_color)

    def get_comment_color(self):
        """Return color for the comments"""
        return self.formats["comment"].foreground().color()

    def get_color_name(self, fmt):
        """Return color name assigned to a given format"""
        return self.formats[fmt].foreground().color().name()

    def setup_formats(self, font=None):
        """

        :param font:
        """
        base_format = QTextCharFormat()
        if font is not None:
            self.font = font
        if self.font is not None:
            base_format.setFont(self.font)
        self.formats = {}
        colors = self.color_scheme.copy()
        self.background_color = colors.pop("background")
        self.currentline_color = colors.pop("currentline")
        self.currentcell_color = colors.pop("currentcell")
        self.occurrence_color = colors.pop("occurrence")
        self.ctrlclick_color = colors.pop("ctrlclick")
        self.sideareas_color = colors.pop("sideareas")
        self.matched_p_color = colors.pop("matched_p")
        self.unmatched_p_color = colors.pop("unmatched_p")
        for name, (color, bold, italic) in list(colors.items()):
            format = QTextCharFormat(base_format)
            format.setForeground(QColor(color))
            format.setBackground(QColor(self.background_color))
            if bold:
                format.setFontWeight(QFont.Bold)
            format.setFontItalic(italic)
            self.formats[name] = format

    def set_color_scheme(self, color_scheme):
        """

        :param color_scheme:
        """
        if isinstance(color_scheme, str):
            self.color_scheme = get_color_scheme(color_scheme)
        else:
            self.color_scheme = color_scheme
        self.setup_formats()
        self.rehighlight()

    def highlightBlock(self, text):
        """

        :param text:
        """
        raise NotImplementedError

    def highlight_spaces(self, text, offset=0):
        """
        Make blank space less apparent by setting the foreground alpha.
        This only has an effect when 'Show blank space' is turned on.
        Derived classes could call this function at the end of
        highlightBlock().
        """
        flags_text = self.document().defaultTextOption().flags()
        show_blanks = flags_text & QTextOption.ShowTabsAndSpaces
        if show_blanks:
            format_leading = self.formats.get("leading", None)
            format_trailing = self.formats.get("trailing", None)
            match = self.BLANKPROG.search(text, offset)
            while match:
                start, end = match.span()
                start = max([0, start + offset])
                end = max([0, end + offset])
                # Format trailing spaces at the end of the line.
                if end == len(text) and format_trailing is not None:
                    self.setFormat(start, end, format_trailing)
                # Format leading spaces, e.g. indentation.
                if start == 0 and format_leading is not None:
                    self.setFormat(start, end, format_leading)
                format = self.format(start)
                color_foreground = format.foreground().color()
                alpha_new = self.BLANK_ALPHA_FACTOR * color_foreground.alphaF()
                color_foreground.setAlphaF(alpha_new)
                self.setFormat(start, end - start, color_foreground)
                match = self.BLANKPROG.search(text, match.end())

    def rehighlight(self):
        """ """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()


# ==============================================================================
# Python syntax highlighter
# ==============================================================================
def any(name, alternates):
    "Return a named group pattern matching list of alternates."
    return "(?P<%s>" % name + "|".join(alternates) + ")"


def make_python_patterns(additional_keywords=[], additional_builtins=[]):
    "Strongly inspired from idlelib.ColorDelegator.make_pat"
    kwlist = keyword.kwlist + additional_keywords
    builtinlist = [
        str(name) for name in dir(builtins) if not name.startswith("_")
    ] + additional_builtins
    repeated = set(kwlist) & set(builtinlist)
    for repeated_element in repeated:
        kwlist.remove(repeated_element)
    kw = r"\b" + any("keyword", kwlist) + r"\b"
    builtin = r"([^.'\"\\#]\b|^)" + any("builtin", builtinlist) + r"\b"
    comment = any("comment", [r"#[^\n]*"])
    instance = any(
        "instance",
        [
            r"\bself\b",
            r"\bcls\b",
            (r"^\s*@([a-zA-Z_][a-zA-Z0-9_]*)" r"(\.[a-zA-Z_][a-zA-Z0-9_]*)*"),
        ],
    )
    number_regex = [
        r"\b[+-]?[0-9]+[lLjJ]?\b",
        r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b",
        r"\b[+-]?0[oO][0-7]+[lL]?\b",
        r"\b[+-]?0[bB][01]+[lL]?\b",
        r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?[jJ]?\b",
    ]

    # Based on
    # https://github.com/python/cpython/blob/
    # 81950495ba2c36056e0ce48fd37d514816c26747/Lib/tokenize.py#L117
    # In order: Hexnumber, Binnumber, Octnumber, Decnumber,
    # Pointfloat + Exponent, Expfloat, Imagnumber
    number_regex = [
        r"\b[+-]?0[xX](?:_?[0-9A-Fa-f])+[lL]?\b",
        r"\b[+-]?0[bB](?:_?[01])+[lL]?\b",
        r"\b[+-]?0[oO](?:_?[0-7])+[lL]?\b",
        r"\b[+-]?(?:0(?:_?0)*|[1-9](?:_?[0-9])*)[lL]?\b",
        r"\b((\.[0-9](?:_?[0-9])*')|\.[0-9](?:_?[0-9])*)"
        "([eE][+-]?[0-9](?:_?[0-9])*)?[jJ]?\b",
        r"\b[0-9](?:_?[0-9])*([eE][+-]?[0-9](?:_?[0-9])*)?[jJ]?\b",
        r"\b[0-9](?:_?[0-9])*[jJ]\b",
    ]
    number = any("number", number_regex)

    sqstring = r"(\b[rRuU])?'[^'\\\n]*(\\.[^'\\\n]*)*'?"
    dqstring = r'(\b[rRuU])?"[^"\\\n]*(\\.[^"\\\n]*)*"?'
    uf_sqstring = r"(\b[rRuU])?'[^'\\\n]*(\\.[^'\\\n]*)*(\\)$(?!')$"
    uf_dqstring = r'(\b[rRuU])?"[^"\\\n]*(\\.[^"\\\n]*)*(\\)$(?!")$'
    sq3string = r"(\b[rRuU])?'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?"
    dq3string = r'(\b[rRuU])?"""[^"\\]*((\\.|"(?!""))[^"\\]*)*(""")?'
    uf_sq3string = r"(\b[rRuU])?'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(\\)?(?!''')$"
    uf_dq3string = r'(\b[rRuU])?"""[^"\\]*((\\.|"(?!""))[^"\\]*)*(\\)?(?!""")$'
    string = any("string", [sq3string, dq3string, sqstring, dqstring])
    ufstring1 = any("uf_sqstring", [uf_sqstring])
    ufstring2 = any("uf_dqstring", [uf_dqstring])
    ufstring3 = any("uf_sq3string", [uf_sq3string])
    ufstring4 = any("uf_dq3string", [uf_dq3string])
    return "|".join(
        [
            instance,
            kw,
            builtin,
            comment,
            ufstring1,
            ufstring2,
            ufstring3,
            ufstring4,
            string,
            number,
            any("SYNC", [r"\n"]),
        ]
    )


class PythonSH(BaseSH):
    """Python Syntax Highlighter"""

    # Syntax highlighting rules:
    add_kw = ["async", "await"]
    PROG = re.compile(make_python_patterns(additional_keywords=add_kw), re.S)
    IDPROG = re.compile(r"\s+(\w+)", re.S)
    ASPROG = re.compile(r".*?\b(as)\b")
    # Syntax highlighting states (from one text block to another):
    (
        NORMAL,
        INSIDE_SQ3STRING,
        INSIDE_DQ3STRING,
        INSIDE_SQSTRING,
        INSIDE_DQSTRING,
    ) = list(range(5))
    # Comments suitable for Outline Explorer
    OECOMMENT = re.compile(r"^(# ?--[-]+|##[#]+ )[ -]*[^- ]+")

    def __init__(self, parent, font=None, color_scheme=None):
        BaseSH.__init__(self, parent, font, color_scheme)
        self.import_statements = {}
        self.found_cell_separators = False

    def highlightBlock(self, text):
        """

        :param text:
        """
        text = str(text)
        prev_state = self.previousBlockState()
        if prev_state == self.INSIDE_DQ3STRING:
            offset = -4
            text = r'""" ' + text
        elif prev_state == self.INSIDE_SQ3STRING:
            offset = -4
            text = r"''' " + text
        elif prev_state == self.INSIDE_DQSTRING:
            offset = -2
            text = r'" ' + text
        elif prev_state == self.INSIDE_SQSTRING:
            offset = -2
            text = r"' " + text
        else:
            offset = 0
            prev_state = self.NORMAL

        import_stmt = None

        self.setFormat(0, len(text), self.formats["normal"])

        state = self.NORMAL
        match = self.PROG.search(text)
        while match:
            for key, value in list(match.groupdict().items()):
                if value:
                    start, end = match.span(key)
                    start = max([0, start + offset])
                    end = max([0, end + offset])
                    if key == "uf_sq3string":
                        self.setFormat(start, end - start, self.formats["string"])
                        state = self.INSIDE_SQ3STRING
                    elif key == "uf_dq3string":
                        self.setFormat(start, end - start, self.formats["string"])
                        state = self.INSIDE_DQ3STRING
                    elif key == "uf_sqstring":
                        self.setFormat(start, end - start, self.formats["string"])
                        state = self.INSIDE_SQSTRING
                    elif key == "uf_dqstring":
                        self.setFormat(start, end - start, self.formats["string"])
                        state = self.INSIDE_DQSTRING
                    else:
                        self.setFormat(start, end - start, self.formats[key])
                        if key == "keyword":
                            if value in ("def", "class"):
                                match1 = self.IDPROG.match(text, end)
                                if match1:
                                    start1, end1 = match1.span(1)
                                    self.setFormat(
                                        start1,
                                        end1 - start1,
                                        self.formats["definition"],
                                    )
                            elif value == "import":
                                import_stmt = text.strip()
                                # color all the "as" words on same line, except
                                # if in a comment; cheap approximation to the
                                # truth
                                if "#" in text:
                                    endpos = text.index("#")
                                else:
                                    endpos = len(text)
                                while True:
                                    match1 = self.ASPROG.match(text, end, endpos)
                                    if not match1:
                                        break
                                    start, end = match1.span(1)
                                    self.setFormat(
                                        start, end - start, self.formats["keyword"]
                                    )

            match = self.PROG.search(text, match.end())

        self.setCurrentBlockState(state)

        # Use normal format for indentation and trailing spaces.
        self.formats["leading"] = self.formats["normal"]
        self.formats["trailing"] = self.formats["normal"]
        self.highlight_spaces(text, offset)

        if import_stmt is not None:
            block_nb = self.currentBlock().blockNumber()
            self.import_statements[block_nb] = import_stmt

    def get_import_statements(self):
        """

        :return:
        """
        return list(self.import_statements.values())

    def rehighlight(self):
        """ """
        self.import_statements = {}
        self.found_cell_separators = False
        BaseSH.rehighlight(self)
