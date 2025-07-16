# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import asyncio
import logging
from collections import defaultdict
from collections.abc import Iterator, Iterable

import torch
import sentence_transformers.util as st_util
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.core.schema import TextNode

from src.retrieval.graph_retriever.grag.search import BaseRetriever


_LOGGER = logging.getLogger(__name__)


class TripleBeam:
    def __init__(self, nodes: list[TextNode], score: float) -> None:
        self._beam = nodes
        self._exist_triples = {x.text for x in self._beam}
        self._score = score

    def __getitem__(self, idx) -> TextNode:
        return self._beam[idx]

    def __len__(self) -> int:
        return len(self._beam)

    def __contains__(self, triple: TextNode) -> bool:
        return triple.text in self._exist_triples

    def __iter__(self) -> Iterator[TextNode]:
        return iter(self._beam)

    @property
    def triples(self) -> list[TextNode]:
        return self._beam

    @property
    def score(self) -> float:
        return self._score


class TripleBeamSearch:
    def __init__(
        self,
        retriever: BaseRetriever,
        num_beams: int = 10,
        num_candidates_per_beam: int = 100,
        max_length: int = 2,
        encoder_batch_size: int = 256,
    ) -> None:
        if max_length < 1:
            raise ValueError(f"expect max_length >= 1; got {max_length=}")

        self.retriever = retriever
        self.num_beams = num_beams
        self.num_candidates_per_beam = num_candidates_per_beam

        self.max_length = max_length
        self.encoder_batch_size = encoder_batch_size
        self.embed_model = retriever.embed_model

    def __call__(self, query: str, triples: list[TextNode]) -> list[TripleBeam]:
        return asyncio.get_event_loop().run_until_complete(self._beam_search(query, triples))

    def _format_triple(self, triple: TextNode) -> str:
        return str(tuple(triple.metadata["triple"]))
        # return triple.text

    def _format_triples(self, triples: Iterable[TextNode]) -> str:
        return "; ".join(self._format_triple(x) for x in triples)

    async def _beam_search(self, query: str, triples: list[TextNode]) -> list[TripleBeam]:

        if not triples:
            _LOGGER.warning(f"beam search got empty input triples, {query=}")
            return []

        # initial round; encode query and input triples
        texts = [self._format_triple(x) for x in triples] + [query]
        embeddings = self.embed_model.embed_docs(texts, batch_size=self.encoder_batch_size)
        query_embedding = embeddings[-1].unsqueeze(0)  # shape (1, emb_size)
        embeddings = embeddings[:-1]  # shape (N, emb_size)
        scores = st_util.cos_sim(query_embedding, embeddings)[0]  # shape (N, )
        topk = scores.topk(k=min(self.num_beams, len(scores)))
        beams = [
            TripleBeam([triples[idx]], score)
            for idx, score in zip(
                topk.indices.tolist(),
                topk.values.tolist(),
            )
        ]

        for _ in range(self.max_length - 1):
            candidates_per_beam = await asyncio.gather(*[self._search_candidates(x) for x in beams])
            beams = self._expand_beams(
                beams=beams,
                candidates_per_beam=candidates_per_beam,
                query_embedding=query_embedding,
            )

        return beams

    def _expand_beams(
        self,
        query_embedding: torch.Tensor,
        beams: list[TripleBeam],
        candidates_per_beam: list[list[TextNode]],
    ) -> list[TripleBeam]:
        texts: list[str] = []
        candidate_paths: list[tuple[TripleBeam, TextNode | None]] = []
        exist_triples = {x.text for beam in beams for x in beam}
        for beam, cands in zip(beams, candidates_per_beam):
            if not cands:
                candidate_paths.append((beam, None))
                texts.append(self._format_triples(beam))
                continue

            for triple in cands:
                if triple.text in exist_triples:
                    continue
                candidate_paths.append((beam, triple))
                texts.append(self._format_triples(beam.triples + [triple]))

        if not texts:
            return beams

        embeddings = self.embed_model.embed_docs(texts, batch_size=self.encoder_batch_size)
        next_scores = st_util.cos_sim(query_embedding, embeddings)[0]  # shape (N, )
        scores = torch.tensor([beam.score for beam, _ in candidate_paths], device=next_scores.device)
        scores += next_scores
        # topk = scores.topk(k=min(self.num_beams, len(scores)))
        # topk = scores.topk(k=len(scores))
        beam2indices: dict[TripleBeam, list[int]] = defaultdict(list)
        for idx, (beam, _) in enumerate(candidate_paths):
            beam2indices[beam].append(idx)

        all_indices = []
        weighted_scores = []
        for indices in beam2indices.values():
            beam_scores = scores[indices]
            sorted_ = torch.sort(beam_scores, descending=True)
            all_indices.extend([indices[x] for x in sorted_.indices.tolist()])
            weighted_scores.append(beam_scores)

        weighted_scores = torch.cat(weighted_scores)
        topk = weighted_scores.topk(k=min(self.num_beams, len(weighted_scores)))

        _beams = []
        for idx in topk.indices.tolist():
            original_idx = all_indices[idx]
            beam, next_triple = candidate_paths[original_idx]
            if next_triple is None:
                _beams.append(beam)
                continue

            _beams.append(TripleBeam(beam.triples + [next_triple], scores[original_idx].item()))

        return _beams


    async def _search_candidates(self, beam: TripleBeam) -> list[TextNode]:
        if len(beam) < 1:
            raise RuntimeError("unexpected empty beam")

        triple = beam[-1].metadata["triple"]

        entities = {triple[0], triple[-1]}
        query_str = " ".join(entities)

        query = VectorStoreQuery(
            query_str=query_str,
            similarity_top_k=self.num_candidates_per_beam,
            mode="text_search",
        )

        # search neighbours
        nodes = await self.retriever.async_search(query)

        ret = []
        for x in nodes:
            if x in beam:
                continue

            triple = x.metadata["triple"]

            if triple[0] not in entities and triple[-1] not in entities:
                continue

            ret.append(x)

        if not ret:
            _LOGGER.warning(f"empty candidates for beam: {self._format_triples(beam)}")

        return ret
