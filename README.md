# Geneea NLP platform integration with Keboola Connection

Integration of the [Geneea API](https://api.geneea.com) with [Keboola Connection](https://connection.keboola.com).

This is a Docker container used for running general-purpose NLP analysis jobs in the KBC.
Automatically built Docker images are available at [Docker Hub Registry](https://hub.docker.com/r/geneea/keboola-nlp-analysis/).

The supported NLP analysis types are: `sentiment`, `entities`, `tags`, `relations`.

## Building a container
To build this container manually one can use:

```
git clone https://github.com/Geneea/keboola-nlp-analysis.git
cd keboola-nlp-analysis
sudo docker build --no-cache -t geneea/keboola-nlp-analysis .
```

## Running a container
This container can be run from the Registry using:

```
sudo docker run \
--volume=/home/ec2-user/data:/data \
--rm \
geneea/keboola-nlp-analysis:latest
```
Note: `--volume` needs to be adjusted accordingly.

## Sample configuration
Mapped to `/data/config.json`

```
{
  "storage": {
    "input": {
      "tables": [
        {
          "destination": "source.csv"
        }
      ]
    }
  },
  "parameters": {
    "user_key": "<ENTER API KEY HERE>",
    "columns": {
      "id": ["date", "subject"],
      "title": ["subject"],
      "text": ["body_1", "body_2"]
    },
    "analysis_types": ["sentiment", "entities", "tags", "relations"],
    "language": "cs",
    "domain": "news",
    "correction": "basic",
    "diacritization": "auto",
    "use_beta": false
  }
}
```

## Output format

The results of the NLP analysis are written into three tables.

* `analysis-result-documents.csv` with document-level results, columns:
    * all `id` columns from the input table (used as primary keys)
    * `language` detected language of the document, as ISO 639-1 language code
    * `sentimentValue` detected sentiment of the document, from an interval _\[-1.0; 1.0\]_
    * `sentimentPolarity` detected sentiment of the document (_-1_, _0_ or _1_)
    * `sentimentLabel` sentiment of the document as a label (_negative_, _neutral_ or _positive_)
    * `usedChars` the number of used characters by this document

* `analysis-result-entities.csv` with entities-level results (multiple results per one document), columns:
    * all `id` columns from the input table (used as primary keys)
    * `type` type of the found entity, e.g. _person_, _address_ or _tag_, (primary key)
    * `text` disambiguated and standardized form of the entity (primary key)
    * `score` relevance score of the entity

* `analysis-result-relations.csv` with relations-level results (multiple results per one document), columns:
    * all `id` columns from the input table (used as primary keys)
    * `type` type of the found relation, _VERB_ or _ATTR_, (primary key)
    * `name` textual name of the relation, e.g. _buy_ or _smart_, (primary key)
    * `subject` possible subject of the relation (primary key)
    * `object` possible object of the relation (primary key)
    * `subjectType` type of the relation's subject
    * `objectType` type of the relation's object
    * `sentimentValue` detected sentiment of the relation, from an interval _\[-1.0; 1.0\]_
    * `sentimentPolarity` detected sentiment of the relation (_-1_, _0_ or _1_)
    * `sentimentLabel` sentiment of the relation as a label (_negative_, _neutral_ or _positive_)
