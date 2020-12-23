import os

import pytest

from .source_test import check_source_example
from beancount.ingest.importers.csv import Importer as CSVImporter, Col
from beancount.core.data import Transaction, Posting, Amount

testdata_dir = os.path.realpath(
    os.path.join(
        os.path.dirname(__file__), '..', '..', 'testdata', 'source', 'generic_importer'))

testdata_csv = os.path.join(testdata_dir, "csv")

examples = [
    'test_basic',
    'test_invalid',
    'test_training_examples',
    'test_dummy_predictor'
]
# tests that should be wrapped in below DummyPostingPredictor
wrap_dummy_predictor = ['test_dummy_predictor']

def Importer():
    return CSVImporter({Col.DATE: 'Date',
                        Col.NARRATION1: 'Description',
                        Col.AMOUNT: 'Amount',
                        },
                       'Assets:Bank',
                       'USD',
                       '"Date","Description","Amount"',
                       )

class DummyPostingPredictor:
    DUMMY_ACCOUNT = "Assets:Dummy"

    def __init__(self, importer):
        self.importer = importer
        # move extract to _extract
        self.importer._extract = self.importer.extract
        self.importer.extract = self.extract_wrapper

    def extract_wrapper(self, f, existing_entries):
        entries = self.importer._extract(f, existing_entries)
        for entry in entries:
            if isinstance(entry, Transaction):
                p = entry.postings[0]
                entry.postings.append(
                    Posting(
                        account=self.DUMMY_ACCOUNT,
                        units=Amount(currency=p.units.currency, number=-1*p.units.number),
                        cost=None,
                        price=None,
                        flag=None,
                        meta={},
                    )
                )
        return entries


@pytest.mark.parametrize('name', examples)
def test_source(name: str):
    importer = Importer()
    # wrap the importer in dummy posting predictor
    if name in wrap_dummy_predictor:
        _ = DummyPostingPredictor(importer)
    check_source_example(
        example_dir=os.path.join(testdata_dir, name),
        source_spec={
            'module': 'beancount_import.source.generic_importer_source',
            'directory': testdata_csv,
            'account': 'Assets:Bank',
            'importer': importer,
        },
        replacements=[(testdata_dir, '<testdata>')])
