# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_sphinx_feature_classification
----------------------------------

Tests for `sphinx_feature_classification` module.
"""
import os

import ddt
import six
from six.moves import configparser

from sphinx_feature_classification import support_matrix
from sphinx_feature_classification.tests import base


@ddt.ddt
class MatrixTestCase(base.TestCase):

    def setUp(self):
        super(MatrixTestCase, self).setUp()

        cfg = configparser.ConfigParser()
        directory = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(directory, 'fakes', 'support-matrix.ini')

        if six.PY2:
            cfg.read_file = cfg.readfp

        with open(config_file) as fp:
            cfg.read_file(fp)

        self.matrix = support_matrix.Matrix(cfg)

    def test_features_set(self):
        fake_feature = self.matrix.features[0]
        self.assertEqual('Cool Feature', fake_feature.title)
        self.assertEqual('optional', fake_feature.status)
        self.assertEqual('A pretty darn cool feature.',
                         fake_feature.notes)

    @ddt.unpack
    @ddt.data({'key': 'driver.foo', 'title': 'Foo Driver',
               'link': 'https://docs.openstack.org'},
              {'key': 'driver.bar', 'title': 'Bar Driver',
               'link': 'https://docs.openstack.org'})
    def test_drivers_set(self, key, title, link):
        fake_driver = self.matrix.drivers[key]
        self.assertEqual(title, fake_driver.title)
        self.assertEqual(link, fake_driver.link)

    @ddt.unpack
    @ddt.data({'key': 'driver.foo', 'status': 'complete',
               'notes': None},
              {'key': 'driver.bar', 'status': 'partial',
               'notes': 'Requires hardware support.'})
    def test_implementations_set(self, key, status, notes):
        fake_implementation = self.matrix.features[0].implementations[key]
        self.assertEqual(status, fake_implementation.status)
        self.assertEqual(notes, fake_implementation.notes)
