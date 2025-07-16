# Graph Based Retrieval

## 1. Environment Setup

Python environment:
```
conda create -n grag python=3.12.11
conda activate grag
cd graph-based-retrieval
pip install -r requirements.txt
```

## 2. Indexing

```sh
python -m src.retrieval.graph_retriever.grag.pipeline.index
python -m src.retrieval.graph_retriever.grag.pipeline.extract_triples
python -m src.retrieval.graph_retriever.grag.pipeline.index_triples
```

#### 2.1 Text Indexer
The TextIndexer class processes and builds a text-based index. It splits documents into multiple text chunks (TextNode), uses the SBERT model to generate embeddings, and stores the results in Elasticsearch.

Configuration
- embed_model: model used to create embedding for each chunk
- batch_size: Controls the number of documents processed in each batch
- es_url, es_index: Elasticsearch index to store text chunks
- data_dir: directory of the jsonl file of documents 


#### 2.2 Triple Indexer
The TripleIndexer class processes and builds an index based on triples. It stores extracted triple data into Elasticsearch for easy querying.

Configuration
- batch_size: Controls the number of triples processed in each batch
- es_url, es_index: Elasticsearch index to store text triples
- text_es_url, text_es_index: Elasticsearch index of text chunks
- data_dir: Path to the directory containing triple data
- batch_size: Controls the number of triples processed in each batch


## 3. Run Retrieval Experiments

For example:

```sh
python -m src.retrieval.local_search
```