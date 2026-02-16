import json
import urllib.request
import xml.etree.ElementTree as ET

COMPLAINTS_URL = 'https://pie.med.utoronto.ca/DC/DC_content/assets/xml/complaints.xml'
DIAGNOSES_URL = 'https://pie.med.utoronto.ca/DC/DC_content/assets/xml/diagnoses.xml'
OUTPUT = 'data/seed-data.json'


def fetch(url):
    print(f'Fetching {url}...')
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def parse_diagnoses(data):
    root = ET.fromstring(data)
    return {diag.attrib['CODE']: diag.attrib.get('VALUE', '') for diag in root.findall('.//DIAGNOSIS')}


def parse_complaints(data, diag_map):
    root = ET.fromstring(data)
    result = {}
    for complaint in root.findall('.//COMPLAINT'):
        symptom = complaint.attrib.get('VALUE', '').strip()
        if not symptom:
            continue
        freq = []
        do_not_miss = []
        commonly_missed = []
        for diag in complaint.findall('.//DIAGNOSIS'):
            code = diag.attrib.get('CODE')
            name = diag_map.get(code, f'Unknown ({code})')
            freq.append(name)
            if diag.attrib.get('DO_NOT_MISS', '').lower() == 'true':
                do_not_miss.append(name)
            if diag.attrib.get('COMMONLY_MISSED', '').lower() == 'true':
                commonly_missed.append(name)
        result[symptom] = {
            'frequency': freq,
            'doNotMiss': do_not_miss,
            'commonlyMissed': commonly_missed,
            'source': 'University of Toronto Diagnostic Checklist'
        }
    return result


def main():
    complaints_data = fetch(COMPLAINTS_URL)
    diagnoses_data = fetch(DIAGNOSES_URL)
    diag_map = parse_diagnoses(diagnoses_data)
    payload = parse_complaints(complaints_data, diag_map)
    with open(OUTPUT, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print(f'Wrote {len(payload)} entries to {OUTPUT}')


if __name__ == '__main__':
    main()
