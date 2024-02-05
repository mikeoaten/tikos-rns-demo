"""
This module, `vector.py`, is responsible for generating responses
to prompts using the Neo4j Vector Search Index and the Language Model (LLM). 

It contains a function `generate_response` that takes a prompt as input and
returns a generated response. The response is generated by querying the
Neo4j Vector Search Index and augmenting the response from the LLM.

The module also contains a retrieval query for the `split_text_embedding` index.
This query is used to match nodes and relationships in the Neo4j database.

This module is part of the Langchain Community project and is used for
retrieval-based Question Answering (QA) tasks.
"""

import streamlit as st
from langchain.chains import RetrievalQA
from langchain_community.vectorstores.neo4j_vector import Neo4jVector

from llm import embeddings, llm


def generate_response(prompt):
    """
    Use the Neo4j Vector Search Index
    to augment the response from the LLM

    Args:
        prompt (str): The prompt or question to generate a response for.

    Returns:
        str: The generated response.
    """

    # Handle the response
    response = kg_qa({"question": prompt})
    return response["answer"]


# for split_text_embedding index
RETRIEVAL_QUERY = """
MATCH (node)-[:CHILD_OF]->(n:News)-[:PUBLISHED_BY]->(c:Company)
// MATCH path = (node)-[r*..2]-()
MATCH path = (n)-[r*..1]-()
where none(x in nodes(path) where x:Resource|SplitText|Rns)
WITH
    score, n, c, node, path
UNWIND relationships(path) AS rels
WITH
    score, n, c, node,
    collect(DISTINCT [
    id(startNode(rels)), 
    CASE 
        WHEN 'Company' IN labels(startNode(rels)) THEN startNode(rels).company_name 
        WHEN 'News' IN labels(startNode(rels)) THEN startNode(rels).headline_name
        WHEN 'NewsCategory' IN labels(startNode(rels)) THEN startNode(rels).category
        WHEN 'Date' IN labels(startNode(rels)) THEN startNode(rels).date
        WHEN 'Industry' IN labels(startNode(rels)) THEN startNode(rels).industry
        WHEN 'Sector' IN labels(startNode(rels)) THEN startNode(rels).sector
        WHEN 'SubSector' IN labels(startNode(rels)) THEN startNode(rels).subsector
        WHEN 'SuperSector' IN labels(startNode(rels)) THEN startNode(rels).supersector
        WHEN 'Tag' IN labels(startNode(rels)) THEN startNode(rels).tag_name
        WHEN 'Person' IN labels(startNode(rels)) THEN startNode(rels).person_name
        WHEN 'Organisation' IN labels(startNode(rels)) THEN startNode(rels).organisation_name
        WHEN 'Position' IN labels(startNode(rels)) THEN startNode(rels).position_name
        ELSE {} 
    END,
    id(rels), 
    type(rels), 
    id(endNode(rels)), 
    CASE 
        WHEN 'Company' IN labels(endNode(rels)) THEN endNode(rels).company_name 
        WHEN 'News' IN labels(endNode(rels)) THEN endNode(rels).headline_name
        WHEN 'NewsCategory' IN labels(endNode(rels)) THEN endNode(rels).category
        WHEN 'Date' IN labels(endNode(rels)) THEN endNode(rels).date
        WHEN 'Industry' IN labels(endNode(rels)) THEN endNode(rels).industry
        WHEN 'Sector' IN labels(endNode(rels)) THEN endNode(rels).sector
        WHEN 'SubSector' IN labels(endNode(rels)) THEN endNode(rels).subsector
        WHEN 'SuperSector' IN labels(endNode(rels)) THEN endNode(rels).supersector
        WHEN 'Tag' IN labels(endNode(rels)) THEN endNode(rels).tag_name
        WHEN 'Person' IN labels(endNode(rels)) THEN endNode(rels).person_name
        WHEN 'Organisation' IN labels(endNode(rels)) THEN endNode(rels).organisation_name
        WHEN 'Position' IN labels(endNode(rels)) THEN endNode(rels).position_name
        ELSE {}
    END
    ]) AS relslist

RETURN DISTINCT
n.body AS text, // this is returning the parent text after matching on the child text
score,
node {
        score: score,
        split_id: node.split_id,
        company: [(node)-[:CHILD_OF]->(n:News)-[:PUBLISHED_BY]->(Company) | Company.company_name],
        url: [(node)-[:CHILD_OF]->(n:News) | n.url],
        graph: relslist
    } AS metadata
// ORDER BY score DESC
LIMIT 3
"""


# neo4jvector = Neo4jVector.from_existing_index(
#     embeddings,
#     url=st.secrets["NEO4J_URI"],
#     username=st.secrets["NEO4J_USERNAME"],
#     password=st.secrets["NEO4J_PASSWORD"],
#     index_name="news_body_embedding",
#     retrieval_query=RETRIEVAL_QUERY,
#     # text_node_property="body",
#     # database="neo4j",
#     # node_label="News",
#     # embedding_node_property="body_embedding",
# )

neo4jvector = Neo4jVector.from_existing_index(
    embeddings,
    url=st.secrets["NEO4J_URI"],
    username=st.secrets["NEO4J_USERNAME"],
    password=st.secrets["NEO4J_PASSWORD"],
    index_name="split_text_embedding",
    retrieval_query=RETRIEVAL_QUERY,
    # text_node_property="body",
    # database="neo4j",
    # node_label="SplitText",
    # embedding_node_property="body_embedding",
)

retriever = neo4jvector.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 3, "score_threshold": 0.87},
)


kg_qa = RetrievalQA.from_chain_type(
    llm,
    chain_type="stuff",
    retriever=retriever,
)

# print()
