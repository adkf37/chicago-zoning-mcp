import xml.etree.ElementTree as ET
from pathlib import Path


def test_zoning_eval_xml_is_well_formed():
    eval_file = Path(__file__).resolve().parent.parent / "evals" / "zoning_qa.xml"
    tree = ET.parse(eval_file)
    assert tree.getroot().tag == "eval_suite"
