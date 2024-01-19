
from feed.errors import FeedIndexerError
from feed.fetch_data import validate_request,create_document
from feed.database import get_announce_papers

from unittest.mock import patch
import pytest
from datetime import datetime, date

def test_no_request_cat():
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("   ")
    assert "Invalid archive specification" in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("cs.ai+")
    assert "Invalid archive specification" in str(excinfo.value)

def test_categories_not_case_sensitive():
    expected= ([],["cs.AI"])
    assert validate_request("cs.ai") == expected
    assert validate_request("CS.ai") == expected
    assert validate_request("cs.AI") == expected
    assert validate_request("CS.AI") == expected

    expected= (["physics"],[])
    assert validate_request("physics") == expected
    assert validate_request("PhYsiCs") == expected

def test_seperates_categories_and_archives():
    assert validate_request("cs.CV+math+hep-lat+cs.CG")==(["math","hep-lat"],["cs.CV","cs.CG"])

def test_bad_cat_requests():
    #bad category form
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request(".AI")
    assert "Bad archive ''." in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("....AI")
    assert "Bad archive/subject class structure" in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("cs.AI.revolutionary")
    assert "Bad archive/subject class structure" in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("cs.AI.")
    assert "Bad archive/subject class structure" in str(excinfo.value)    

    #not an archive
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("psuedo-science")
    assert "Bad archive 'psuedo-science'." in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("psuedo-science.CS")
    assert "Bad archive 'psuedo-science'." in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("cs.AI+psuedo-science")
    assert "Bad archive 'psuedo-science'." in str(excinfo.value) 

    #not a category
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("physics.psuedo-science")
    assert "Bad subject class 'psuedo-science'." in str(excinfo.value)
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("cs.AI+physics.psuedo-science")
    assert "Bad subject class 'psuedo-science'." in str(excinfo.value)

    #invalid combiantion   
    with pytest.raises(FeedIndexerError) as excinfo:
        validate_request("physics.AI")
    assert "Bad subject class 'AI'." in str(excinfo.value)

def test_create_document(sample_arxiv_metadata, sample_arxiv_update, sample_doc,sample_author, sample_author2):
    #simple
    assert sample_doc==create_document((sample_arxiv_update,sample_arxiv_metadata))
    #multiple authors
    sample_doc.authors=[sample_author,sample_author2]
    sample_arxiv_metadata.authors="Very Real Sr. (Cornell University), L Emeno"
    assert sample_doc==create_document((sample_arxiv_update,sample_arxiv_metadata))

def test_basic_db_query(app):
    last_date=date(2023,10,26)
    first_date=date(2023,10,26)
    category=["cs.CV"]
    with app.app_context():
        items=get_announce_papers(first_date, last_date, [],category)
    #any data is returned
    assert len(items) >0
    for item in items:
        update, meta= item
        #no absonly entries
        assert update.action != "absonly"
        #no updates with a version above 4
        assert update.action != "replace" or update.version <5
        #correct category
        assert update.category =="cs.CV"
        #fetched matching metadata
        assert update.document_id == meta.document_id
        #correct date
        assert update.date==last_date

def test_db_date_range(app):
    last_date=date(2023,10,27)
    first_date=date(2023,10,26)
    category=["cs.CV"]
    with app.app_context():
        items=get_announce_papers(first_date, last_date, [],category)
    
    assert len(items) >=2 #two valid entries in database
    found_26=False
    found_27=False
    for item in items:
        update, meta= item
        assert update.date >=first_date and update.date <= last_date
        if update.date==first_date:
            found_26=True
        if update.date==last_date:
            found_27=True
    assert found_26 and found_27

def test_db_archive(app):
    last_date=date(2023,10,26)
    first_date=date(2023,10,26)
    archive=["cs"]
    with app.app_context():
        items=get_announce_papers(first_date, last_date, archive,[])
    assert len(items) >0 
    for item in items:
        update, meta= item
        assert update.archive in archive

def test_db_multiple_archives(app):
    last_date=date(2023,10,26)
    first_date=date(2023,10,26)
    archives=["cs", "math"]
    with app.app_context():
        items=get_announce_papers(first_date, last_date, archives,[])
    assert len(items) >0 
    found_cs=False
    found_math=False
    for item in items:
        update, meta= item
        assert update.archive in archives
        if update.archive=="math":
            found_math=True
        if update.archive=="cs":
            found_cs=True
    assert found_cs and found_math

def test_db_multiple_categories(app):
    last_date=date(2023,10,26)
    first_date=date(2023,10,26)
    cats=["cs.CV", "math.NT"]
    with app.app_context():
        items=get_announce_papers(first_date, last_date, [],cats)
    assert len(items) >0 
    found_cs=False
    found_math=False
    for item in items:
        update, meta= item
        assert update.category in cats
        if update.category=="math.NT":
            found_math=True
        if update.category=="cs.CV":
            found_cs=True
    assert found_cs and found_math

def test_db_cat_and_archive(app):
    last_date=date(2023,10,26)
    first_date=date(2023,10,26)
    cat=["cs.CV"]
    archive=["math"]
    with app.app_context():
        items=get_announce_papers(first_date, last_date, archive,cat)
    assert len(items) >0 
    found_cs=False
    found_math=False
    for item in items:
        update, meta= item
        assert update.category in cat or update.archive in archive
        if update.archive=="math":
            found_math=True
        if update.category=="cs.CV":
            found_cs=True
    assert found_cs and found_math