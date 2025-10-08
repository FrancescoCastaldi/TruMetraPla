"""Classifier for inferring canonical TruMetraPla fields from Excel columns.

The project needs to ingest spreadsheets coming from wildly different
departments.  Header names change frequently and the data samples themselves can
contain hints about the semantics of a column (for instance a column full of
timestamps is very likely to be the production ``date``).

To provide a resilient experience we implement a tiny Naïve Bayes text
classifier that analyses header names together with a short sample of values.
The classifier has been trained with curated examples for each canonical field
and produces a score for a candidate column.  The :class:`ColumnGuesser`
combines those scores with lightweight heuristics (numeric detection,
date-likeness, etc.) in order to auto-map arbitrary spreadsheets.

The training data is intentionally embedded in the source so that the module is
completely self-contained and does not require extra dependencies.  Although it
is a very small model, it behaves like a standard machine learning component:
tokens are extracted, priors are computed and predictions are made based on the
calculated probabilities.
"""

from __future__ import annotations

from collections import Counter
import math
import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

_TOKEN_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    return [_token.casefold() for _token in _TOKEN_RE.findall(text)]


def _flatten_samples(samples: Sequence[str] | None) -> list[str]:
    flattened: list[str] = []
    if not samples:
        return flattened
    for sample in samples:
        if not sample:
            continue
        flattened.extend(_tokenize(sample))
    return flattened


@dataclass(slots=True)
class _FieldProfile:
    name: str
    token_counts: Counter[str]
    total_tokens: int


class NaiveBayesColumnClassifier:
    """Very small multinomial Naïve Bayes classifier for column inference."""

    def __init__(self, training_samples: Mapping[str, Sequence[str]]):
        if not training_samples:
            raise ValueError("training_samples must not be empty")

        self._profiles: dict[str, _FieldProfile] = {}
        vocabulary: set[str] = set()

        for field, samples in training_samples.items():
            token_counter: Counter[str] = Counter()
            for sample in samples:
                token_counter.update(_tokenize(sample))
            total = sum(token_counter.values())
            self._profiles[field] = _FieldProfile(field, token_counter, total)
            vocabulary.update(token_counter.keys())

        self._vocabulary_size = max(len(vocabulary), 1)
        self._log_prior = math.log(1 / len(self._profiles))

    def score(self, field: str, *, header: str, samples: Sequence[str] | None = None) -> float:
        profile = self._profiles[field]
        tokens = _tokenize(header)
        tokens.extend(_flatten_samples(samples))
        if not tokens:
            return float("-inf")

        score = self._log_prior
        denominator = profile.total_tokens + self._vocabulary_size
        for token in tokens:
            count = profile.token_counts.get(token, 0)
            score += math.log((count + 1) / denominator)
        return score

    def most_likely_fields(
        self,
        *,
        header: str,
        samples: Sequence[str] | None = None,
        candidates: Iterable[str] | None = None,
    ) -> list[tuple[str, float]]:
        """Return the candidate fields sorted by likelihood."""

        fields = list(candidates) if candidates is not None else list(self._profiles)
        scored = [(field, self.score(field, header=header, samples=samples)) for field in fields]
        return sorted(scored, key=lambda item: item[1], reverse=True)


def analyse_samples(samples: Sequence[str] | None) -> dict[str, float]:
    """Extract lightweight metadata from column samples.

    The heuristics inspect the first N values of a column to infer whether they
    look numeric, textual or date-like.  The metadata is later combined with the
    probabilistic classifier to make a final decision.
    """

    if not samples:
        return {"numeric_ratio": 0.0, "date_like_ratio": 0.0, "text_length": 0.0}

    numeric_matches = 0
    date_matches = 0
    total_length = 0

    date_pattern = re.compile(r"\d{1,4}[-/.]" r"\d{1,2}[-/.]\d{1,4}")

    for sample in samples:
        if sample is None:
            continue
        text = str(sample).strip()
        if not text:
            continue
        total_length += len(text)

        if date_pattern.search(text):
            date_matches += 1

        try:
            float(text.replace(",", "."))
        except ValueError:
            pass
        else:
            numeric_matches += 1

    total_samples = max(len(samples), 1)
    return {
        "numeric_ratio": numeric_matches / total_samples,
        "date_like_ratio": date_matches / total_samples,
        "text_length": total_length / total_samples,
    }


class ColumnGuesser:
    """Combine a probabilistic classifier with heuristics."""

    def __init__(self, classifier: NaiveBayesColumnClassifier):
        self._classifier = classifier

    def evaluate(
        self,
        *,
        field: str,
        header: str,
        samples: Sequence[str] | None,
    ) -> float:
        metadata = analyse_samples(samples)
        base_score = self._classifier.score(field, header=header, samples=samples)
        if not math.isfinite(base_score):
            base_score = -1_000.0

        score = base_score

        numeric_ratio = metadata["numeric_ratio"]
        date_ratio = metadata["date_like_ratio"]

        if field == "date":
            score += 2.5 * date_ratio
            score -= 1.5 * numeric_ratio  # pure numbers are usually not valid dates
        elif field in {"quantity", "duration_minutes"}:
            score += 3.0 * numeric_ratio
            score -= 1.0 * date_ratio
        else:
            # Textual fields benefit from actual text content
            score += 0.002 * metadata["text_length"]
            score -= 2.0 * numeric_ratio

        return score

    def guess(
        self,
        *,
        field: str,
        columns: Mapping[str, Sequence[str] | None],
        already_assigned: set[str],
    ) -> tuple[str | None, float]:
        best_column: str | None = None
        best_score = float("-inf")
        second_score = float("-inf")

        for header, samples in columns.items():
            if header in already_assigned:
                continue
            score = self.evaluate(field=field, header=header, samples=samples)
            if score > best_score:
                second_score = best_score
                best_score = score
                best_column = header
            elif score > second_score:
                second_score = score

        if best_column is None:
            return None, float("-inf")

        margin = best_score - second_score
        if best_score < -20 or margin < 0.75:
            return None, best_score

        return best_column, best_score


DEFAULT_TRAINING_DATA: dict[str, tuple[str, ...]] = {
    "date": (
        "data produzione",
        "giorno commessa",
        "production date",
        "day",
        "data registrazione",
        "2024-01-01",
        "03/02/2024",
        "12.02.24",
    ),
    "employee": (
        "operatore",
        "dipendente",
        "responsabile cella",
        "worker name",
        "operator",
        "mario rossi",
        "team leader",
    ),
    "process": (
        "processo",
        "fase produttiva",
        "operazione",
        "fase",
        "production stage",
        "taglio laser",
        "assemblaggio",
    ),
    "machine": (
        "macchina",
        "impianto",
        "postazione",
        "machine",
        "equipment",
        "piegatrice 02",
    ),
    "process_type": (
        "tipo processo",
        "tipologia",
        "categoria",
        "process family",
        "assemblaggio",
        "lavorazione meccanica",
    ),
    "quantity": (
        "pezzi",
        "output",
        "qta prodotta",
        "pieces",
        "numero pezzi",
        "100",
        "45",
    ),
    "duration_minutes": (
        "durata",
        "minuti lavorati",
        "tempo ciclo",
        "cycle minutes",
        "tempo totale",
        "89",
        "123",
    ),
}


def build_default_guesser() -> ColumnGuesser:
    classifier = NaiveBayesColumnClassifier(DEFAULT_TRAINING_DATA)
    return ColumnGuesser(classifier)

