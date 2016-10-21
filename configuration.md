Input:
* id - id of the document
* text - main text of the document
* title - optional title of the document 
* lead - optional lead or abstract of the document

Input options:
* language - the language of text to analyze; leave empty for automatic detection
* domain - the domain or type of text to analyze
* correction - should common typos be corrected before analysis
* diacritization - before analysing Czech text where diacritics are missing, add all the wedges and accents. For example, for "Muj ctyrnohy pritel" > "Můj čtyřnohý přítel".
* use_beta - use Geneea's beta server (use only when instructed to do so)


Type of analysis:    
    
* sentiment - detect the emotions contained in the text. Was the author happy (I loved it.), neutral (We went to London.) or unhappy (The lunch was not good at all.) with their experience? You can detect sentiment of reviews, feedback or customer service inquiries.

* entities - search your texts for names of people, locations, products, dates, account numbers, etc. We can adjust the detectors to your needs (e.g. taking into account your products) or even identify a new type of entity whether it should be financial products or offending expressions.

* tags - the objective of a topic tag is to describe the content of a text whether an email, commercial contract, or a news article. A tag can be cancel subscription, safe car, or terrible cook. Again, we can easily adjust tags to your domain and to your needs.


The result contains two tables:

* `analysis-result-documents.csv` with document-level results, columns:
    * all `id` columns from the input table (used as primary keys)
    * `language` detected language of the document, as ISO 639-1 language code
    * `sentimentPolarity` detected sentiment of the document (_1_, _0_ or _-1_)
    * `sentimentLabel` sentiment of the document as a label (_positive_, _neutral_ or _negative_)
    * `usedChars` the number of used characters by this document

* `analysis-result-entities.csv` with entity-level results (multiple rows per one document) has these columns:
    * all `id` columns from the input table (used as primary keys)
    * `type` type of the found entity, e.g., _person_, _organization_ or _tag_ (primary key)
    * `text` disambiguated and standardized form of the entity e.g., _John Smith_, _Keboola_, _safe carseat_ (primary key)

