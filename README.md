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

The results of the NLP analysis are written into four tables.

* `analysis-result-documents.csv` with document-level results in the following columns:
    * all `id` columns from the input table (used as primary keys)
    * `language` detected language of the document, as ISO 639-1 language code
    * `sentimentValue` detected sentiment of the document, from an interval _\[-1.0; 1.0\]_
    * `sentimentPolarity` detected sentiment of the document (_-1_, _0_ or _1_)
    * `sentimentLabel` sentiment of the document as a label (_negative_, _neutral_ or _positive_)
    * `sentimentDetailedLabel` sentiment of the document as a detailed label
    * `usedChars` the number of characters used by this document

* `analysis-result-sentences.csv` with sentence-level results has the following columns:
    * all `id` columns from the input table (used as primary keys)
    * `index` zero-based index of the sentence in the document, (primary key)
    * `segment` text segment where the sentence is located
    * `text` the sentence text
    * `sentimentValue` detected sentiment of the sentence, from an interval _\[-1.0; 1.0\]_
    * `sentimentPolarity` detected sentiment of the sentence (_-1_, _0_ or _1_)
    * `sentimentLabel` sentiment of the sentence as a label (_negative_, _neutral_ or _positive_)
    * `sentimentDetailedLabel` sentiment of the sentence as a detailed label

  There are multiple rows per one document. All `id` columns plus the `index` column are part of the primary key.

* `analysis-result-entities.csv` with entity-level results has the following columns:
    * all `id` columns from the input table (used as primary keys)
    * `type` type of the found entity, e.g. _person_, _organization_ or _tag_, (primary key)
    * `text` disambiguated and standardized form of the entity, e.g. _John Smith_, _Keboola_, _safe carseat_, (primary key)
    * `score` relevance score of the entity, e.g. _0.8_
    * `entityUid` unique ID of the entity, may be empty
    * `sentimentValue` detected sentiment of the entity, from an interval _\[-1.0; 1.0\]_
    * `sentimentPolarity` detected sentiment of the entity (_-1_, _0_ or _1_)
    * `sentimentLabel` sentiment of the entity as a label (_negative_, _neutral_ or _positive_)
    * `sentimentDetailedLabel` sentiment of the entity as a detailed label

  There are multiple rows per one document. All `id` columns plus `type` and `text` columns are part of the primary key.

  Note that the table also contains topic tags, marked as _tag_ in the `type` column.

* `analysis-result-relations.csv` with relation-level results has the following columns:
    * all `id` columns from the input table (used as primary keys)
    * `type` type of the found relation, _VERB_ or _ATTR_, (primary key)
    * `name` textual name of the relation, e.g. _buy_ or _smart_, (primary key)
    * `negated` negation flag of the relation, _true_ or _false_, (primary key)
    * `subject` possible subject of the relation (primary key)
    * `object` possible object of the relation (primary key)
    * `subjectType` type of the relation's subject
    * `objectType` type of the relation's object
    * `subjectUid` unique ID of the relation's subject
    * `objectUid` unique ID of the relation's object
    * `sentimentValue` detected sentiment of the relation, from an interval _\[-1.0; 1.0\]_
    * `sentimentPolarity` detected sentiment of the relation (_-1_, _0_ or _1_)
    * `sentimentLabel` sentiment of the relation as a label (_negative_, _neutral_ or _positive_)
    * `sentimentDetailedLabel` sentiment of the relation as a detailed label

  There are multiple rows per one document. All `id` columns plus `type`, `name`, `negated`, `subject`, `object` columns are part of the primary key.
