from opensearchpy import NotFoundError, OpenSearch
import json

# Create the client with SSL/TLS disabled for local testing
host = "localhost"
port = 9200
auth = ("admin", "mysupersecret123Password!")
client = OpenSearch(
    hosts=[{"host": host, "port": port}],
    http_auth=auth,
    use_ssl=False,
    verify_certs=False,
)

# Names of test index and labels
index_name = "tempindex1234"
parent_label = "parentLabel"
child_label = "childLabel"


def create_index(index_name):
    index_body = {
        "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}}
    }
    response = client.indices.create(index_name, body=index_body)
    print(f"Created index: {response}")


def delete_index(index_name):
    try:
        response = client.indices.delete(index_name)
        print(f"Deleted index: {response}")
    except NotFoundError as e:
        print(f"Ignoring NotFoundError: {e}")


def insert_document(index_name, document, shard_id="1"):
    doc_id = document.get("id")
    print()
    print(f"Adding document: {doc_id=}")

    response = client.index(
        index=index_name,
        body=document,
        refresh=True,
        id=doc_id,
        routing=shard_id,
    )

    print("Response:")
    print(json.dumps(response, indent=2))


def search_documents(index_name, query):
    response = client.search(body=query, index=index_name)
    print()
    print("Search query:")
    print(json.dumps(query, indent=2))
    print("Search results:")
    print(json.dumps(response, indent=2))


def create_mappings(index_name, mappings):
    response = client.indices.put_mapping(index=index_name, body=mappings)
    print(f"Created mapping: {response}")


def parse_json(filename: str):
    with open(filename) as file:
        return json.load(file)


def generate_documents(input_file, output_file, parent_label, child_label):
    """
    Process example documents and add derived fields for parent-child relationships.
    """
    documents = parse_json(input_file)
    for document in documents:

        # Get the nested field "entityDescription.reference.publicationContext.id" if it exists
        entity_description = document.get("entityDescription", {})
        reference = entity_description.get("reference", {})
        publication_context = reference.get("publicationContext", {})
        parent_id = publication_context.get("id", None)

        if parent_id:
            document["child_to_parent"] = {"name": child_label, "parent": parent_id}
        else:
            document["child_to_parent"] = {"name": parent_label, "parent": parent_id}

    with open(output_file, "w") as file:
        json.dump(documents, file, indent=2)


def build_index(index_name, documents, mappings):
    print()
    delete_index(index_name)

    print()
    create_index(index_name)

    print()
    create_mappings(index_name, mappings)

    for document in documents:
        print()
        print("Adding document:")
        print(json.dumps(document, indent=2))
        self_id = document.get("id")
        print("Using ID = ", self_id)

        response = client.index(
            index=index_name, body=document, refresh=True, id=self_id, routing="1"
        )

        print("Response:")
        print(json.dumps(response, indent=2))


def getAll():
    """
    This query will return all documents in the index.
    """
    search_query = {"query": {"match_all": {}}}
    search_documents(index_name, search_query)


def getParentsWithInvalidChildren():
    """
    This query will find child documents that have a mismatch between their
    parent document's scientificValue field. Returns child documents that:
    - Have a parent document of type "BookAnthology" or "Textbook"
    - Have a parent document with scientificValue="Unassigned" or "LevelZero"
    - Are not themselves set to scientificValue="Unassigned" or "LevelZero"
    """
    search_query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "entityDescription.reference.publicationInstance.type": "BookAnthology"
                                    }
                                },
                                {
                                    "term": {
                                        "entityDescription.reference.publicationInstance.type": "TextBook"
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "entityDescription.reference.publicationContext.scientificValue": "Unassigned"
                                    }
                                },
                                {
                                    "term": {
                                        "entityDescription.reference.publicationContext.scientificValue": "LevelZero"
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                    {
                        "has_child": {
                            "type": "childLabel",
                            "query": {
                                "bool": {
                                    "must_not": [
                                        {
                                            "term": {
                                                "entityDescription.reference.publicationContext.scientificValue": "Unassigned"
                                            }
                                        },
                                        {
                                            "term": {
                                                "entityDescription.reference.publicationContext.scientificValue": "LevelZero"
                                            }
                                        },
                                    ],
                                },
                            },
                            "inner_hits": {},
                        }
                    },
                ],
            },
        },
    }
    search_documents(index_name, search_query)


def getParentsWithoutChildren():
    """
    This query finds parent documents where we expect child documents to exist,
    but where no child documents are linked. Returns parent documents that:
    - Are of type "BookAnthology" or "TextBook"
    - Do not have any child documents linked to them
    """
    search_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "entityDescription.reference.publicationInstance.type": "BookAnthology"
                                    }
                                },
                                {
                                    "term": {
                                        "entityDescription.reference.publicationInstance.type": "TextBook"
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                ],
                "must_not": [
                    {
                        "has_child": {
                            "type": "childLabel",
                            "query": {"match_all": {}},
                            "inner_hits": {},
                        }
                    },
                ],
            }
        }
    }
    search_documents(index_name, search_query)


if __name__ == "__main__":
    # Define example data and initialize the index
    generate_documents("data.json", "output.json", parent_label, child_label)
    documents = parse_json("output.json")
    mappings = parse_json("mappings.json")
    build_index(index_name, documents, mappings)

    # Run example queries
    getAll()
    getParentsWithInvalidChildren()
    getParentsWithoutChildren()
