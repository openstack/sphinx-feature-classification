# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""
This provides a sphinx extension able to render the support-matrix.ini
file into the developer documentation.

It is used via a single directive in the .rst file

  .. support_matrix::

"""

from os import path
import re
import shutil

from docutils import nodes
from docutils.parsers import rst
import six
from six.moves import configparser

KEY_PATTERN = re.compile("[^a-zA-Z0-9_]")
DRIVER_PREFIX = "driver."
FEATURE_PREFIX = 'operation.'
DRIVER_NOTES_PREFIX = "driver-notes."


class Matrix(object):
    """Represents the entire support matrix for project drivers"""

    def __init__(self, cfg):
        self.drivers = self._set_drivers(cfg)
        self.features = self._set_features(cfg)

    @staticmethod
    def _set_drivers(cfg):
        drivers = {}

        for section in cfg.sections():
            if not section.startswith(DRIVER_PREFIX):
                continue

            title = cfg.get(section, "title")

            link = None
            if cfg.has_option(section, 'link'):
                link = cfg.get(section, "link")

            driver = Driver(title, link)
            drivers[section] = driver

        return drivers

    def _set_features(self, cfg):
        features = []

        def _process_feature(section):
            if not cfg.has_option(section, "title"):
                raise Exception(
                    "'title' option missing in '[%s]' section" % section)

            title = cfg.get(section, "title")
            status = Feature.STATUS_OPTIONAL
            group = None

            if cfg.has_option(section, "status"):
                # The value is a string "status(group)" where
                # the 'group' part is optional
                status, group = re.match('^([^(]+)(?:\(([^)]+)\))?$',
                                         cfg.get(section, "status")).groups()

                if status not in Feature.STATUS_ALL:
                    raise ValueError(
                        "'status' option value '%s' in ['%s']"
                        "section must be one of (%s)" %
                        (status, section,
                         ", ".join(Feature.STATUS_ALL)))

            cli = []
            if cfg.has_option(section, "cli"):
                cli = cfg.get(section, "cli")

            notes = None
            if cfg.has_option(section, "notes"):
                notes = cfg.get(section, "notes")
            return Feature(section, title, status, group, notes, cli)

        def _process_implementation(section, option, feature):
            if option not in self.drivers:
                raise Exception(
                    "'%s' section is not declared in the "
                    "INI file." % (option))

            status = cfg.get(section, option)
            if status not in Implementation.STATUS_ALL:
                raise ValueError(
                    "%s is set to %s in '[%s]' section but must be "
                    "one of (%s)" % (option, status, section, ", ".join(
                        Implementation.STATUS_ALL)))

            option_notes = ''.join([DRIVER_NOTES_PREFIX,
                                    option[len(DRIVER_PREFIX):]])
            notes = None
            if cfg.has_option(section, option_notes):
                notes = cfg.get(section, option_notes)

            impl = Implementation(status=status, notes=notes)
            feature.implementations[option] = impl

            return feature

        for section in cfg.sections():
            if not section.startswith(FEATURE_PREFIX):
                continue

            feature = _process_feature(section)

            # Now we've got the basic feature details, we must process
            # the backend driver implementation for each feature
            for option in cfg.options(section):
                if not option.startswith(DRIVER_PREFIX):
                    continue

                _process_implementation(section, option, feature)
            features.append(feature)

        return features


class Feature(object):
    STATUS_CHOICE = "choice"
    STATUS_CONDITION = "condition"
    STATUS_MANDATORY = "mandatory"
    STATUS_OPTIONAL = "optional"
    STATUS_MATURE = "mature"
    STATUS_IMMATURE = "immature"

    STATUS_ALL = [STATUS_MANDATORY, STATUS_OPTIONAL, STATUS_CHOICE,
                  STATUS_CONDITION, STATUS_MATURE, STATUS_IMMATURE]

    def __init__(self, key, title, status=STATUS_OPTIONAL,
                 group=None, notes=None, cli=(), api=None):
        self.key = key
        self.title = title
        self.status = status
        self.group = group
        self.notes = notes
        self.cli = cli
        self.api = api

        self.implementations = {}


class Implementation(object):
    STATUS_COMPLETE = "complete"
    STATUS_PARTIAL = "partial"
    STATUS_MISSING = "missing"
    STATUS_UNKNOWN = "unknown"

    STATUS_ALL = [STATUS_COMPLETE, STATUS_MISSING,
                  STATUS_PARTIAL, STATUS_UNKNOWN]

    def __init__(self, status=STATUS_MISSING, notes=None):
        self.status = status
        self.notes = notes


STATUS_SYMBOLS = {
    Implementation.STATUS_COMPLETE: u"\u2714",
    Implementation.STATUS_MISSING: u"\u2716",
    Implementation.STATUS_PARTIAL: u"\u2714",
    Implementation.STATUS_UNKNOWN: u"?"
}


class Driver(object):
    def __init__(self, title, link=None):
        """Driver object.

        :param title: Human readable name for plugin
        :param link: A URL to documentation about the driver.
        """
        self.title = title
        self.link = link


class Directive(rst.Directive):

    # support-matrix.ini is the arg
    required_arguments = 1

    def run(self):
        matrix = self._load_support_matrix()
        return self._build_markup(matrix)

    def _load_support_matrix(self):
        """Parse support-matrix.ini file.

        Reads the support-matrix.ini file and populates an instance of the
        Matrix class with all the data.

        :returns: Matrix instance
        """

        cfg = configparser.ConfigParser()
        env = self.state.document.settings.env
        fname = self.arguments[0]
        rel_fpath, fpath = env.relfn2path(fname)

        # Handle deprecation of readfp in py3 for read_file that was not
        # available in py2.
        if six.PY2:
            cfg.read_file = cfg.readfp

        with open(fpath) as fp:
            cfg.read_file(fp)

        # This ensures that the docs are rebuilt whenever the
        # .ini file changes
        env.note_dependency(rel_fpath)

        matrix = Matrix(cfg)
        return matrix

    def _build_markup(self, matrix):
        """Constructs the docutils content for the support matrix."""
        content = []
        self._build_summary(matrix, content)
        self._build_details(matrix, content)
        self._build_notes(content)
        return content

    @staticmethod
    def _build_summary(matrix, content):
        """Constructs the content for the summary of the support matrix.

        The summary consists of a giant table, with one row
        for each feature, and a column for each backend
        driver. It provides an 'at a glance' summary of the
        status of each driver.
        """

        summary_title = nodes.subtitle(text="Summary")
        summary = nodes.table(classes=["sp_feature_cells"])
        cols = len(matrix.drivers.keys())

        # Add two columns for the Feature and Status columns.
        cols += 2

        summary_group = nodes.tgroup(cols=cols)
        summary_body = nodes.tbody()
        summary_head = nodes.thead()

        for i in range(cols):
            summary_group.append(nodes.colspec(colwidth=1))
        summary_group.append(summary_head)
        summary_group.append(summary_body)
        summary.append(summary_group)
        content.append(summary_title)
        content.append(summary)

        # This sets up all the column headers - two fixed
        # columns for feature name & status
        header = nodes.row()
        blank = nodes.entry(classes=["sp_feature_cells"])
        blank.append(nodes.emphasis(text="Feature"))
        header.append(blank)
        blank = nodes.entry(classes=["sp_feature_cells"])
        blank.append(nodes.emphasis(text="Status"))
        header.append(blank)
        summary_head.append(header)

        # then one column for each backend driver
        impls = sorted(matrix.drivers,
                       key=lambda x: matrix.drivers[x].title)
        for key in impls:
            driver = matrix.drivers[key]
            implcol = nodes.entry(classes=["sp_feature_cells"])
            header.append(implcol)
            if driver.link:
                uri = driver.link
                target_ref = nodes.reference("", refuri=uri)
                target_txt = nodes.inline()
                implcol.append(target_txt)
                target_txt.append(target_ref)
                target_ref.append(nodes.strong(text=driver.title))
            else:
                implcol.append(nodes.strong(text=driver.title))

        # We now produce the body of the table, one row for
        # each feature to report on
        for feature in matrix.features:
            item = nodes.row()

            # the hyperlink driver name linking to details
            feature_id = re.sub(KEY_PATTERN, "_", feature.key)

            # first the fixed columns for title/status
            key_col = nodes.entry(classes=["sp_feature_cells"])
            item.append(key_col)
            key_ref = nodes.reference(refid=feature_id)
            key_txt = nodes.inline()
            key_col.append(key_txt)
            key_txt.append(key_ref)
            key_ref.append(nodes.strong(text=feature.title))

            status_col = nodes.entry(classes=["sp_feature_cells"])
            item.append(status_col)
            status_col.append(nodes.inline(
                text=feature.status,
                classes=["sp_feature_" + feature.status]))

            # and then one column for each backend driver
            for key in impls:
                impl = feature.implementations[key]
                impl_col = nodes.entry(classes=["sp_feature_cells"])
                item.append(impl_col)

                key_id = re.sub(KEY_PATTERN, "_",
                                "{}_{}".format(feature.key, key))

                impl_ref = nodes.reference(refid=key_id)
                impl_txt = nodes.inline()
                impl_col.append(impl_txt)
                impl_txt.append(impl_ref)

                status = STATUS_SYMBOLS.get(impl.status, "")

                impl_ref.append(nodes.literal(
                    text=status,
                    classes=["sp_impl_summary", "sp_impl_" + impl.status]))

            summary_body.append(item)

    def _build_details(self, matrix, content):
        """Constructs the content for the details of the support matrix."""

        details_title = nodes.subtitle(text="Details")
        details = nodes.bullet_list()

        content.append(details_title)
        content.append(details)

        # One list entry for each feature we're reporting on
        for feature in matrix.features:
            item = nodes.list_item()

            status = feature.status
            if feature.group is not None:
                status += "({})".format(feature.group)

            feature_id = re.sub(KEY_PATTERN, "_", feature.key)

            # Highlight the feature title name
            item.append(nodes.strong(text=feature.title, ids=[feature_id]))

            # Add maturity status
            para = nodes.paragraph()
            para.append(nodes.strong(text="Status: {}. ".format(status)))
            item.append(para)

            if feature.api is not None:
                para = nodes.paragraph()
                para.append(
                    nodes.strong(text="API Alias: {} ".format(feature.api)))
                item.append(para)

            if feature.cli:
                item.append(self._create_cli_paragraph(feature))

            if feature.notes is not None:
                item.append(self._create_notes_paragraph(feature.notes))

            para_divers = nodes.paragraph()
            para_divers.append(nodes.strong(text="Driver Support:"))
            # A sub-list giving details of each backend driver
            impls = nodes.bullet_list()
            keys = sorted(feature.implementations,
                          key=lambda x: matrix.drivers[x].title)
            for key in keys:
                driver = matrix.drivers[key]
                impl = feature.implementations[key]
                subitem = nodes.list_item()

                key_id = re.sub(KEY_PATTERN, "_",
                                "{}_{}".format(feature.key, key))

                subitem += [
                    nodes.strong(text="{}: ".format(driver.title)),
                    nodes.literal(text=impl.status,
                                  classes=["sp_impl_{}".format(impl.status)],
                                  ids=[key_id]),
                ]

                if impl.notes is not None:
                    subitem.append(self._create_notes_paragraph(impl.notes))

                impls.append(subitem)

            para_divers.append(impls)
            item.append(para_divers)
            details.append(item)

    @staticmethod
    def _build_notes(content):
        """Constructs a list of notes content for the support matrix.

        This is generated as a bullet list.
        """
        notes_title = nodes.subtitle(text="Notes:")
        notes = nodes.bullet_list()

        content.append(notes_title)
        content.append(notes)

        for note in ["This document is a continuous work in progress"]:
            item = nodes.list_item()
            item.append(nodes.strong(text=note))
            notes.append(item)

    @staticmethod
    def _create_cli_paragraph(feature):
        """Create a paragraph which represents the CLI commands of the feature

        The paragraph will have a bullet list of CLI commands.
        """
        para = nodes.paragraph()
        para.append(nodes.strong(text="CLI commands:"))
        commands = nodes.bullet_list()
        for c in feature.cli.split(";"):
            cli_command = nodes.list_item()
            cli_command += nodes.literal(text=c, classes=["sp_cli"])
            commands.append(cli_command)
        para.append(commands)
        return para

    @staticmethod
    def _create_notes_paragraph(notes):
        """Constructs a paragraph which represents the implementation notes

        The paragraph consists of text and clickable URL nodes if links were
        given in the notes.
        """
        para = nodes.paragraph()
        para.append(nodes.strong(text="Notes: "))
        # links could start with http:// or https://
        link_idxs = [m.start() for m in re.finditer('https?://', notes)]
        start_idx = 0
        for link_idx in link_idxs:
            # assume the notes start with text (could be empty)
            para.append(nodes.inline(text=notes[start_idx:link_idx]))
            # create a URL node until the next text or the end of the notes
            link_end_idx = notes.find(" ", link_idx)
            if link_end_idx == -1:
                # In case the notes end with a link without a blank
                link_end_idx = len(notes)
            uri = notes[link_idx:link_end_idx + 1]
            para.append(nodes.reference("", uri, refuri=uri))
            start_idx = link_end_idx + 1

        # get all text after the last link (could be empty) or all of the
        # text if no link was given
        para.append(nodes.inline(text=notes[start_idx:]))
        return para


def on_build_finished(app, exc):
    if exc is None:
        src = path.join(path.abspath(path.dirname(__file__)),
                        'support-matrix.css')
        dst = path.join(app.outdir, '_static', 'support-matrix.css')
        shutil.copyfile(src, dst)


def setup(app):
    app.add_directive('support_matrix', Directive)
    app.add_css_file('support-matrix.css')
    app.connect('build-finished', on_build_finished)
