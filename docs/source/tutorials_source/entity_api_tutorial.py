"""
Tutorial Entity API
===========================

In this tutorial you will learn how to use the `Entity API <https://pro.europeana.eu/page/entity>`_,
which offers information about several type of entities: ``agent``, ``place``, ``concept`` and ``timespan``.
These named entities are part of the Europeana Entity Collection, a collection of entities in the context of Europeana
harvested from and linked to controlled vocabularies, such as ​Geonames, Dbpedia and Wikidata.

The Entity API has three methods:

* ``apis.entity.suggest``: returns entities of a certain type matching a text query

* ``apis.entity.retrieve``: returns information about an individual entity of a certain type

* ``apis.entity.resolve``: returns entities that match a query url

We will use `PyEuropeana <https://github.com/europeana/rd-europeana-python-api>`_,
a Python client library for Europeana APIs.
Read more about how the package works in the `Documentation <https://rd-europeana-python-api.readthedocs.io/en/stable/>`_.
Europeana APIs require a key for authentication, find more information on how to get your API key `here <https://pro.europeana.eu/pages/get-api>`_.
"""

import pyeuropeana.apis as apis
import pandas as pd

# %%
# Agents
# -------
#
# In this section we focus on the agent type of entities. We would like to find out if there are agents that match some query.
# In the following cell we use the ``suggest`` method, which returns a dictionary

resp = apis.entity.suggest(
    text="leonardo",
    TYPE="agent",
)

resp.keys()


# %%
# The response contains several fields. The field ``total`` represents the number of entities matching our query

resp["total"]

# %%
# The field ``items`` contains a list where each object represents an entity, which are the results of the search

len(resp["items"])

# %%
# This list can be converted in a pandas DataFrame as follows:


df = pd.json_normalize(resp["items"])
df.columns

# %%
#
# The resulting dataframe has several columns. The ``id`` column contain the identifier for the entity.
# The columns starting with ``shownBy`` contain information about an illustration for a given entity. We can discard this information if we want

df = df.drop(columns=[col for col in df.columns if "isShownBy" in col])
cols = df.columns.tolist()
df = df[cols[-2:] + cols[:-2]]
df.head()

# %%
#
# We have some information about several entities matching our query. What other information can we obtain for these entities?
# The method ``retrieve`` can be used to obtain more information about a particular entity using its identifier.
# The ``id`` column in the table above contains the uris of the different entities, where the identifier is an integer located at the end of each entiry uri.
# For example, for the entity *Leonardo da Vinci* with uri http://data.europeana.eu/agent/base/146741 we can call ``retrieve`` as:


resp = apis.entity.retrieve(
    TYPE="agent",
    IDENTIFIER=146741,
)

resp.keys()

# %%
# We observe that the response contains several fields, some of them not present in the suggest method.
# The field ``prefLabel`` contains a list of the name of the entity in different languages. We can transform this list into a dataframe


def get_name_df(resp):
    lang_name_df = None
    if "prefLabel" in resp.keys():
        lang_name_df = pd.DataFrame(
            [
                {"language": lang, "name": name}
                for lang, name in resp["prefLabel"].items()
            ]
        )
    return lang_name_df


lang_name_df = get_name_df(resp)
lang_name_df.head()

# %%
# The field ``biographicalInformation`` can be useful to know more about the biography of the agent in particular.
# This information is also multilingual, and can be transformed into a dataframe


def get_biography_df(resp):
    bio_df = None
    if "biographicalInformation" in resp.keys():
        bio_df = pd.DataFrame(resp["biographicalInformation"])
    return bio_df


bio_df = get_biography_df(resp)
bio_df.head()

# %%
# We can access the biography in English for instance in the following way

bio_df["@value"].loc[bio_df["@language"] == "en"].values[0]

# %%
# Now, let's say that we want to find the biography for all the entities returned by ``entity.search``.
# We can encapsulate the previous steps into a function that can be applied to the dataframe resulting from ``entity.search``:


def get_bio_uri(uri):
    id = int(uri.split("/")[-1])
    resp = apis.entity.retrieve(
        TYPE="agent",
        IDENTIFIER=id,
    )

    bio_df = get_biography_df(resp)
    bio = bio_df["@value"].loc[bio_df["@language"] == "en"].values[0]
    return bio


df["bio"] = df["id"].apply(get_bio_uri)
df.head()

# %%
# The biography in English has been added for each entity. Great!
# Something of interest can be the place of birth and death of the agents. We can create a function as:


def get_place_resp(resp, event):

    if event == "birth":
        if "placeOfBirth" not in resp.keys():
            return
        place = resp["placeOfBirth"]

    elif event == "death":
        if "placeOfDeath" not in resp.keys():
            return
        place = resp["placeOfDeath"]

    if not place:
        return

    place = list(place[0].values())[0]

    if place.startswith("http"):
        place = place.split("/")[-1].replace("_", " ")
    return place


resp = apis.entity.retrieve(
    TYPE="agent",
    IDENTIFIER=146741,
)
get_place_resp(resp, "birth")

# %%
# .. note::
#   WARNING: The function above parses the URI and extracts the name of the places of birth and date.
#   In reality we should use either the ``resolve`` method of the Entity API,
#   if the URI is that of an entity in Europeana's Entity Collection,
#   or seek to de-reference it using `Linked Data content negotiation <https://https://www.w3.org/DesignIssues/Conneg>`_,
#   if it is not known in the Entity Collection.
#
# Now we can add this information to the original dataframe:


def get_place(uri, event):
    id = int(uri.split("/")[-1])
    resp = apis.entity.retrieve(
        TYPE="agent",
        IDENTIFIER=id,
    )
    return get_place_resp(resp, event)


df["placeOfBirth"] = df["id"].apply(lambda x: get_place(x, "birth"))
df["placeOfDeath"] = df["id"].apply(lambda x: get_place(x, "death"))
df.drop(columns=["id"]).head()

# %%
# The previous pipeline can be applied to any other agent:

resp = apis.entity.suggest(
    text="Marguerite Gérard",
    TYPE="agent",
)

df = pd.json_normalize(resp["items"])
df = df.drop(columns=[col for col in df.columns if "isShownBy" in col])
df["bio"] = df["id"].apply(get_bio_uri)
df["placeOfBirth"] = df["id"].apply(lambda x: get_place(x, "birth"))
df["placeOfDeath"] = df["id"].apply(lambda x: get_place(x, "death"))
df.drop(columns=["id"]).head()

# %%
# Finally, we can use the method ``resolve`` for obtaining the entity matching a an external URI when it is present as entity in the Europeana Entity Collection.
# Find more information in the ` documentation of the Entity API <https://pro.europeana.eu/page/entity#resolve>`_

resp = apis.entity.resolve("http://dbpedia.org/resource/Leonardo_da_Vinci")
resp.keys()

# %%
# Places
# -------
# One of the types of entities we can work with are places. Let's get the place of death of the previous agent

place_of_death = df["placeOfDeath"].values[0]
place_of_death

# %%
# We can now search the entity corresponding to this place by using the suggest method using ``place`` as the ``TYPE`` argument.

resp = apis.entity.suggest(
    text=place_of_death,
    TYPE="place",
)
place_df = pd.json_normalize(resp["items"])
cols = place_df.columns.tolist()
cols = cols[-1:] + cols[:-1]
place_df = place_df[cols]
place_df.head()

# %%
# Let's use the first uri with the ``retrieve`` method

uri = place_df["id"].values[0]
IDENTIFIER = uri.split("/")[-1]

resp = apis.entity.retrieve(
    IDENTIFIER=IDENTIFIER,
    TYPE="place",
)
resp.keys()

# %%
# We can reuse the function ``get_name_df`` for places as well, as the response has a similar data structure as for ``agent``

name_df = get_name_df(resp)
name_df.head()

# %%
# The response include the field ``isPartOf``, which indicates an entity that the current entity belongs to, if any

is_part_uri = resp["isPartOf"][0]
is_part_uri

# %%
# Let's see what this misterious uri refers to using the retrieve method

is_part_id = is_part_uri.split("/")[-1]
resp = apis.entity.retrieve(
    IDENTIFIER=is_part_id,
    TYPE="place",
)

name_df = get_name_df(resp)
name_df.head()

# %%
# It had to be the emblematic *Île-de-France*, of course! And its coordinates are:

f"lat: {resp['lat']}, long: {resp['long']}"

# %%
# Concepts
# -------
# Let's query for all concepts

resp = apis.entity.suggest(
    text="war",
    TYPE="concept",
)

resp["total"]

# %%
# We build a table containing the field ``items``, were we can see the name and uri of the different concepts

df = pd.json_normalize(resp["items"])
df = df.drop(columns=[col for col in df.columns if "isShownBy" in col])
df.head()

# %%
# Do we want to know more information about the first concept of the list? We got it

concept_uri = df["id"].values[0]
concept_uri

concept_id = concept_uri.split("/")[-1]
resp = apis.entity.retrieve(
    IDENTIFIER=concept_id,
    TYPE="concept",
)

name_df = get_name_df(resp)
name_df.loc[name_df["language"] == "en"]

# %%
# The concept is World War I. We can get some related concepts from dbpedia

resp["related"]

# %%
# The field ``note`` contains a multilingual description of the concept

note_df = pd.json_normalize(
    [{"lang": k, "note": v[0]} for k, v in resp["note"].items()]
)
note_df.head()

# %%
# We can obtain the description for a particular language as

note_df["note"].loc[note_df["lang"] == "en"].values[0]

# %%
# Tips for using entities with the Search API
# --------------------------------------------
# Once we know the identifier for a certain entity we can use the Search API to obtain objects containing it.
# For instance we can query objects containing the entity "Painting" using its uri http://data.europeana.eu/concept/base/47

concept_uri = "http://data.europeana.eu/concept/base/47"
resp = apis.search(query=f'"{concept_uri}"')

resp["totalResults"]

# %%
# Notice that in order to use a uri as a query we need to wrap it in quotation marks "".
# We might want to query for object belonging to more than one entity. We can simply do that by using logical operators in the query. Querying for paintings from the 16th century:


resp = apis.search(
    query='"http://data.europeana.eu/timespan/16" AND "http://data.europeana.eu/concept/base/47"',
    media=True,
    qf="TYPE:IMAGE",
)

resp["totalResults"]

# %%
# Queyring for paintings with some relation to Paris

resp = apis.search(
    query='"http://data.europeana.eu/place/base/41488" AND "http://data.europeana.eu/concept/base/47"',
    media=True,
    qf="TYPE:IMAGE",
)

resp["totalResults"]

# %%
# When querying for entities uris, the objects returned are those that have the requested uris in the metadata.
# However, not all objects contain this information and instead many of them contain the name of the entity.
# It is always a good idea to query for the name of the entities as well, as there might be more objects:

resp = apis.search(query="Paris AND Painting", media=True, qf="TYPE:IMAGE")

resp["totalResults"]

# %%
# Conclusions
# --------------------------------------------
# In this tutorial we learned:
#
# * What types of entities are available in the Europeana Entity API
#
# * To use the ``suggest`` method for obtaining entities of a certain type matching a text query
#
# * To use the ``retrieve`` method for obtaining information about an individual entity of a certain type
#
# * To use the method ``resolve`` for obtaining entities that match a query url
#
# * To process some of the fields contained in the responses of the methods above and convert the responses to Pandas dataframes
#
# * To query for entities using Europeana Search API
