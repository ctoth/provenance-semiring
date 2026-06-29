"""Tests for the polynomial-native label / environment / nogood antichain algebra."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from provenance_semiring import (
    EnvironmentKey,
    JustificationRecord,
    Label,
    NogoodSet,
    SourceVariableId,
    SupportEvidence,
    SupportQuality,
    combine_labels,
    merge_labels,
    normalize_environments,
)

_PROP_SETTINGS = settings(deadline=None)
_VARIABLES = tuple(SourceVariableId(f"var:source:test:{name}") for name in ("a", "b", "c", "d"))


def _var(name: str) -> SourceVariableId:
    return SourceVariableId(f"var:source:test:{name}")


def _env(*names: str) -> EnvironmentKey:
    return EnvironmentKey(tuple(_var(name) for name in names))


@st.composite
def environments(draw: st.DrawFn) -> EnvironmentKey:
    selected = draw(st.lists(st.sampled_from(_VARIABLES), min_size=0, max_size=4))
    return EnvironmentKey(tuple(selected))


@st.composite
def labels(draw: st.DrawFn) -> Label:
    envs = draw(st.lists(environments(), min_size=0, max_size=4))
    return Label(tuple(envs))


class TestEnvironmentKey:
    def test_normalizes_dedup_and_sort(self) -> None:
        env = EnvironmentKey((_var("b"), _var("a"), _var("b")))
        assert env.variables == (_var("a"), _var("b"))

    def test_union_merges_variables(self) -> None:
        assert _env("a").union(_env("b")) == _env("a", "b")

    def test_subsumes_is_subset(self) -> None:
        assert _env("a").subsumes(_env("a", "b"))
        assert not _env("a", "b").subsumes(_env("a"))
        assert _env().subsumes(_env("a"))

    def test_order_is_total(self) -> None:
        assert _env("a") < _env("a", "b")


class TestNormalizeEnvironments:
    def test_prunes_supersets(self) -> None:
        result = normalize_environments([_env("a", "b"), _env("a")])
        assert result == (_env("a"),)

    def test_deduplicates(self) -> None:
        result = normalize_environments([_env("a"), _env("a")])
        assert result == (_env("a"),)

    def test_drops_known_nogood(self) -> None:
        nogoods = NogoodSet([_env("a", "b")])
        result = normalize_environments([_env("a", "b"), _env("c")], nogoods=nogoods)
        assert result == (_env("c"),)

    @pytest.mark.property
    @given(st.lists(environments(), min_size=0, max_size=6))
    @_PROP_SETTINGS
    def test_result_is_an_antichain(self, raw: list[EnvironmentKey]) -> None:
        result = normalize_environments(raw)
        for outer in result:
            for inner in result:
                if outer is inner:
                    continue
                assert not outer.subsumes(inner)


class TestLabel:
    def test_empty_is_unconditional_support(self) -> None:
        assert Label.empty().environments == (_env(),)

    def test_no_environments_is_unsupported(self) -> None:
        assert Label(()).environments == ()

    def test_from_variable_single_environment(self) -> None:
        assert Label.from_variable(_var("a")).environments == (_env("a"),)

    def test_environments_round_trip_through_polynomial(self) -> None:
        label = Label((_env("a"), _env("b", "c")))
        assert label.environments == (_env("a"), _env("b", "c"))

    def test_environments_are_normalized(self) -> None:
        label = Label((_env("a"), _env("a", "b")))
        assert label.environments == (_env("a"),)

    def test_eq_and_hash_on_environments(self) -> None:
        a = Label((_env("a"), _env("b")))
        b = Label((_env("b"), _env("a")))
        assert a == b
        assert hash(a) == hash(b)

    def test_support_polynomial_is_the_label(self) -> None:
        label = Label.from_variable(_var("a"))
        assert isinstance(label.support, SupportEvidence)
        assert label.support.quality is SupportQuality.EXACT
        # The polynomial IS the label; environments project it back.
        rebuilt = Label(support=label.support)
        assert rebuilt == label


class TestCombineLabels:
    def test_empty_combine_is_unconditional(self) -> None:
        assert combine_labels() == Label.empty()

    def test_cross_product_of_environments(self) -> None:
        left = Label((_env("a"), _env("b")))
        right = Label((_env("c"),))
        combined = combine_labels(left, right)
        assert combined.environments == (_env("a", "c"), _env("b", "c"))

    def test_unconditional_is_identity(self) -> None:
        label = Label((_env("a"),))
        assert combine_labels(label, Label.empty()) == label

    def test_unsupported_antecedent_yields_unsupported(self) -> None:
        assert combine_labels(Label((_env("a"),)), Label(())) == Label(())

    def test_nogood_filters_inconsistent_join(self) -> None:
        nogoods = NogoodSet([_env("a", "c")])
        left = Label((_env("a"), _env("b")))
        right = Label((_env("c"),))
        combined = combine_labels(left, right, nogoods=nogoods)
        assert combined.environments == (_env("b", "c"),)


class TestMergeLabels:
    def test_disjoins_alternative_supports(self) -> None:
        merged = merge_labels([Label((_env("a"),)), Label((_env("b"),))])
        assert merged.environments == (_env("a"), _env("b"))

    def test_merge_prunes_supersets(self) -> None:
        merged = merge_labels([Label((_env("a"),)), Label((_env("a", "b"),))])
        assert merged.environments == (_env("a"),)

    def test_merge_drops_nogood_environments(self) -> None:
        nogoods = NogoodSet([_env("a")])
        merged = merge_labels([Label((_env("a"),)), Label((_env("b"),))], nogoods=nogoods)
        assert merged.environments == (_env("b"),)


class TestNogoodSet:
    def test_excludes_superset_of_nogood(self) -> None:
        nogoods = NogoodSet([_env("a", "b")])
        assert nogoods.excludes(_env("a", "b", "c"))
        assert not nogoods.excludes(_env("a"))

    def test_environments_round_trip(self) -> None:
        nogoods = NogoodSet([_env("a", "b"), _env("c")])
        assert set(nogoods.environments) == {_env("a", "b"), _env("c")}

    def test_provenance_nogood_carries_variables_and_witness(self) -> None:
        nogoods = NogoodSet([_env("a", "b")])
        (nogood,) = nogoods.provenance_nogoods
        assert nogood.variables == frozenset({_var("a"), _var("b")})
        assert nogood.witness.source == "provenance_semiring.labels.NogoodSet"

    def test_empty_nogood_excludes_everything(self) -> None:
        nogoods = NogoodSet([_env()])
        assert nogoods.excludes(_env("a"))
        assert nogoods.excludes(_env())


class TestJustificationRecord:
    def test_from_antecedents_combines(self) -> None:
        record = JustificationRecord.from_antecedents(
            "concl",
            [Label((_env("a"),)), Label((_env("b"),))],
        )
        assert record.conclusion == "concl"
        assert record.label == combine_labels(Label((_env("a"),)), Label((_env("b"),)))


class TestAlgebraicProperties:
    @pytest.mark.property
    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_combine_is_commutative(self, left: Label, right: Label) -> None:
        assert combine_labels(left, right) == combine_labels(right, left)

    @pytest.mark.property
    @given(labels(), labels())
    @_PROP_SETTINGS
    def test_merge_is_commutative(self, left: Label, right: Label) -> None:
        assert merge_labels([left, right]) == merge_labels([right, left])

    @pytest.mark.property
    @given(labels())
    @_PROP_SETTINGS
    def test_combine_with_unconditional_is_identity(self, label: Label) -> None:
        assert combine_labels(label, Label.empty()) == label

    @pytest.mark.property
    @given(labels())
    @_PROP_SETTINGS
    def test_label_environments_are_an_antichain(self, label: Label) -> None:
        envs = label.environments
        for outer in envs:
            for inner in envs:
                if outer is inner:
                    continue
                assert not outer.subsumes(inner)
