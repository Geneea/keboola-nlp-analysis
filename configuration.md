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

* The 'analysis-result-documents.csv' table; it contains the following fields for each document:
   * id - document id
   * language 
   * usedChars
   * sentimentPolarity
   * sentimentLabel

* The 'analysis-result-entities.csv' table; it contains the following fields for each document:
   * id - document id
   * type - type of the entity (e.g. person, organization, tag) 
   * text - text of the entity (e.g. John Smith, Keboola, safe carseat)



