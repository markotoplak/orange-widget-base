from unittest import TestCase
from unittest.mock import Mock
from Orange.data import Domain, DiscreteVariable
from Orange.data import ContinuousVariable
from Orange.widgets.settings import DomainContextHandler, ContextSetting
from Orange.widgets.utils import vartype

Continuous = vartype(ContinuousVariable())
Discrete = vartype(DiscreteVariable())


class DomainContextHandlerTestCase(TestCase):
    def setUp(self):
        self.domain = Domain(
            attributes=[ContinuousVariable('c1'),
                        DiscreteVariable('d1', values='abc'),
                        DiscreteVariable('d2', values='def')],
            class_vars=[DiscreteVariable('d3', values='ghi')],
            metas=[ContinuousVariable('c2'),
                   DiscreteVariable('d4', values='jkl')]
        )
        self.args = (self.domain,
                     {'c1': Continuous, 'd1': Discrete,
                      'd2': Discrete, 'd3': Discrete},
                     {'c2': Continuous, 'd4': Discrete, })
        self.handler = DomainContextHandler(metas_in_res=True)

    def test_encode_domain_with_match_none(self):
        handler = DomainContextHandler(
            match_values=DomainContextHandler.MATCH_VALUES_NONE,
            metas_in_res=True)

        encoded_attributes, encoded_metas = handler.encode_domain(self.domain)

        self.assertEqual(encoded_attributes,
                         {'c1': Continuous, 'd1': Discrete,
                          'd2': Discrete, 'd3': Discrete})
        self.assertEqual(encoded_metas, {'c2': Continuous, 'd4': Discrete, })

    def test_encode_domain_with_match_class(self):
        handler = DomainContextHandler(
            match_values=DomainContextHandler.MATCH_VALUES_CLASS,
            metas_in_res=True)

        encoded_attributes, encoded_metas = handler.encode_domain(self.domain)

        self.assertEqual(encoded_attributes,
                         {'c1': Continuous, 'd1': Discrete, 'd2': Discrete,
                          'd3': list('ghi')})
        self.assertEqual(encoded_metas, {'c2': Continuous, 'd4': Discrete})

    def test_encode_domain_with_match_all(self):
        handler = DomainContextHandler(
            match_values=DomainContextHandler.MATCH_VALUES_ALL,
            metas_in_res=True)

        encoded_attributes, encoded_metas = handler.encode_domain(self.domain)

        self.assertEqual(encoded_attributes,
                         {'c1': Continuous, 'd1': list('abc'),
                          'd2': list('def'), 'd3': list('ghi')})
        self.assertEqual(encoded_metas,
                         {'c2': Continuous, 'd4': list('jkl')})

    def test_encode_domain_with_false_attributes_in_res(self):
        handler = DomainContextHandler(attributes_in_res=False,
                                       metas_in_res=True)

        encoded_attributes, encoded_metas = handler.encode_domain(self.domain)

        self.assertEqual(encoded_attributes, {})
        self.assertEqual(encoded_metas, {'c2': Continuous, 'd4': Discrete})

    def test_encode_domain_with_false_metas_in_res(self):
        handler = DomainContextHandler(attributes_in_res=True,
                                       metas_in_res=False)

        encoded_attributes, encoded_metas = handler.encode_domain(self.domain)

        self.assertEqual(encoded_attributes,
                         {'c1': Continuous, 'd1': Discrete,
                          'd2': Discrete, 'd3': Discrete})
        self.assertEqual(encoded_metas, {})

    def test_match_returns_2_on_perfect_match(self):
        context = Mock(
            attributes=self.args[1], metas=self.args[2], values={})
        self.assertEqual(2., self.handler.match(context, *self.args))

    def test_match_returns_1_if_everything_matches(self):
        self.handler.bind(SimpleWidget)

        # Attributes in values
        context = Mock(values=dict(
            with_metas=('d1', Discrete),
            required=('d1', Discrete)))
        self.assertEqual(1., self.handler.match(context, *self.args))

        # Metas in values
        context = Mock(values=dict(
            with_metas=('d4', Discrete),
            required=('d1', Discrete)))
        self.assertEqual(1., self.handler.match(context, *self.args))

        # Attributes in lists
        context = Mock(values=dict(
            with_metas=[("d1", Discrete)]
        ))
        self.assertEqual(1., self.handler.match(context, *self.args))

        # Metas in lists
        context = Mock(values=dict(
            with_metas=[("d4", Discrete)]
        ))
        self.assertEqual(1., self.handler.match(context, *self.args))

    def test_match_returns_point_1_when_nothing_to_match(self):
        self.handler.bind(SimpleWidget)

        context = Mock(values={})
        self.assertEqual(0.1, self.handler.match(context, *self.args))

    def test_match_returns_zero_on_incompatible_context(self):
        self.handler.bind(SimpleWidget)

        # required
        context = Mock(values=dict(required=('u', Discrete),
                                   with_metas=('d1', Discrete)))
        self.assertEqual(0, self.handler.match(context, *self.args))

        # selected if_selected
        context = Mock(values=dict(with_metas=('d1', Discrete),
                                   if_selected=[('u', Discrete)],
                                   selected=[0]))
        self.assertEqual(0, self.handler.match(context, *self.args))

        # unselected if_selected
        context = Mock(values=dict(with_metas=('d1', Discrete),
                                   if_selected=[('u', Discrete),
                                                ('d1', Discrete)],
                                   selected=[1]))
        self.assertAlmostEqual(0.667, self.handler.match(context, *self.args),
                               places=2)

    def test_new_context(self):
        context = self.handler.new_context()

        self.assertTrue(hasattr(context, 'attributes'))
        self.assertTrue(hasattr(context, 'metas'))
        self.assertTrue(hasattr(context, 'ordered_domain'))
        self.assertTrue(hasattr(context, 'values'))

    def test_clone_context(self):
        self.handler.bind(SimpleWidget)
        context = Mock(values=dict(
            text=('u', -2),
            with_metas=[('d1', Discrete), ('d1', Continuous),
                        ('c1', Continuous), ('c1', Discrete)],
            required=('u', Continuous)
        ))

        new_values = self.handler.clone_context(context, *self.args).values

        self.assertEqual(new_values['text'], ('u', -2))
        self.assertEqual([('d1', Discrete), ('c1', Continuous)],
                         new_values['with_metas'])
        self.assertNotIn('required', new_values)



class SimpleWidget:
    name = "Simple Widget"

    text = ContextSetting("", not_attribute=True)
    with_metas = ContextSetting("", exclude_metas=False)
    required = ContextSetting("", required=ContextSetting.REQUIRED)
    if_selected = ContextSetting([], required=ContextSetting.IF_SELECTED,
                                 selected='selected')
