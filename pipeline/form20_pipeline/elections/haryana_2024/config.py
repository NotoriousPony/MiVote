"""Haryana Vidhan Sabha 2024 - election-specific configuration.

BASE_DIR is injected by run_pipeline.py (this folder's absolute path).
"""
import os

PDF_DIR = os.path.join(BASE_DIR, 'data', 'form20')
MAPPING_XLSX = os.path.join(BASE_DIR, 'data', 'mapping.xlsx')
PARTY_LIST = os.path.join(BASE_DIR, 'party_list.txt')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# PDF filename (normalized: lowercase letters only, no '(sc)') -> mapping sheet name
AC_ALIASES = {'gurgaon': 'Gurugram', 'panipat': 'Panipat Rural'}

# Mapping sheets that are wrong and must be ignored (range fixes used instead)
SHEET_SKIP = {'Kaithal'}

# Booth-range corrections: sheet -> [(first_booth, last_booth, village), ...]
RANGE_FIXES = {
    'Badkhal': [(189, 228, 'Lakadpur'), (229, 256, 'Anangpur'), (257, 283, 'Fatehpur Chandila')],
    'Faridabad': [(154, 165, 'Daulatabad'), (166, 187, 'Ajraunda'), (188, 244, 'Sihi'), (245, 249, 'Ballabgarh')],
    'Kaithal': [(1,4,'Niwach'),(5,6,'Balwanti'),(7,8,'Jaswanti'),(9,18,'Kyodak'),(19,21,'Dayora'),
        (22,22,'Ujhana'),(23,23,'Jagdish Pura'),(24,25,'Kultaran'),(26,28,'Khurana'),
        (29,31,'Patti Afghan (Urban)'),(32,34,'Sirta'),(35,38,'Manas'),(39,41,'Ladana Baba'),
        (42,44,'Budhakhera'),(45,45,'Sangatpura'),(46,46,'Nand Singh Wala'),(47,49,'Sanghan'),
        (50,51,'Malkhedi'),(52,55,'Padla'),(56,56,'Chakk Padla'),(57,57,'Diluwali'),(58,61,'Guhna'),
        (62,66,'Sajuma'),(67,68,'Dundrehedi'),(69,70,'Diwal'),(71,72,'Chhot'),(73,73,'Bhanpura'),
        (74,74,'Gadi Padla'),(75,75,'Madho Majri'),(76,77,'Patti Khot / Gadli'),(78,78,'Phansawala'),
        (79,80,'Kutubpur'),(81,81,'Patti Dogar / Shila Khera'),(82,90,'Arjun Nagar / Sirta Road'),
        (91,94,'Shakti Nagar'),(95,96,'Balaji Colony / Bank Colony / Rajni Colony'),
        (97,97,'Devigarh / Shiv Nagar'),(98,98,'Friends Colony / HUDA Sector 18'),(99,100,'Balraj Nagar'),
        (101,104,'Subhash Nagar / Friends Colony / Janakpuri'),(105,107,'Mayapuri / Sugar Mill Colony'),
        (108,110,'Nankpuri Colony / D.P.V. Colony'),(111,113,'HUDA Sector 19 / Sector 20 / Rishi Nagar'),
        (114,116,'HUDA Sector 21 / Rajouri Garden / Moti Bagh'),(117,118,'HUDA Sector 19 / Officer Colony'),
        (119,120,'HUDA Sector 20'),(121,123,'Siwan Gate / Dogran Gate'),(124,127,'Pratap Gate / Mata Gate'),
        (128,129,'Mahadev Colony / Rajiv Colony'),(130,134,'West Bihar Colony / Gupta Colony / Subhash Nagar'),
        (135,137,'Agrasen Puram / RK Puram / Employees Colony'),(138,139,'Chiranjeev Colony / Seth Colony'),
        (140,141,'Khushhal Majri / Chichdan Mohalla'),(142,143,'Jain Mohalla / Joshian Mohalla'),
        (144,146,'Main Bazar / Shastri Market / Prem Gali'),(147,148,'Sivka Market / Railway Gate'),
        (149,151,'State Bank Colony / GTB Colony / Govind Nagar'),(152,152,'Canal Colony / MITC Colony'),
        (153,155,'Adarsh Nagar / Professor Colony'),(156,156,'Model Town / PWD Colony'),
        (157,162,'Amargadh Gamri / Kamal Colony / Krishna Nagar'),
        (163,166,'Patel Nagar / Sarsoda Colony / Om Shanti Nagar'),
        (167,169,'Model Town Jind Road / Sora Kothi'),(170,171,'Bank Colony / Ram Nagar'),
        (172,175,'HUDA Housing Board / Chanda Road'),(176,180,'Saini Colony / Gabi Sahib Colony'),
        (181,183,'Sripunj Mohalla / Khurana Mohalla'),(184,188,'Pratap Gate / Ambkeshwar Colony'),
        (189,190,'Shiv Nagar / Azad Nagar'),(191,191,'Shergad'),(192,193,'Dayodkhedi'),
        (194,194,'Bhaini Majra'),(195,198,'Gyong'),(199,199,'Sapan Khedi'),(200,203,'Munddi'),
        (204,206,'Naina'),(207,209,'Kathwad'),(210,212,'Dhaus'),(213,215,'Khanoda')],
}

# Constituencies with no usable Form 20: AC-level totals entered manually
MANUAL_ENTRIES = {
    'Shahbad': {
        'status': 'AC_TOTAL_ONLY: Government has not released Form 20 booth-wise data; village breakdown unavailable',
        'candidates': [  # (name, party, total votes incl. postal) - source: results.eci.gov.in S07-12
            ('Ram Karan', 'INC', 61050), ('Subhash Chand', 'BJP', 54609),
            ('Chander Bhan Chauhan', 'BSP', 1638), ('Kanta Aalldia', 'Mission Ekta Party', 1333),
            ('Asha Rani', 'AAP', 932), ('Rajeeta Singh', 'JJP', 431),
            ('Pawan Kumar', 'IND', 358), ('Rajesh Kanipla', 'IND', 235), ('Shiv Nath', 'IND', 185)],
    },
}

# --- party matching ---
PARTY_TOKENS = ['BJP', 'INC', 'INLD', 'BSP', 'JJP', 'ASP(KR)', 'CPI(M)']
MAJOR_PARTIES = {'BJP', 'INC', 'CPI(M)'}  # get a rank<=3 prior in matching
PARTY_AC_ALIASES = {'ambalacant': 'Ambala Cantt', 'gurgaon': 'Gurugram', 'nangalchaudhry': 'Nangal Chaudhary'}

# (AC, party) -> exact ballot name, for matches the fuzzy matcher can't make alone
MATCH_OVERRIDES = {
    ('Sohna', 'INC'): 'ROHTAS SINGH',
    ('Jind', 'JJP'): 'DHARAM PAL TANWAR',       # confirmed same person as Dharampal Prajapat
    ('Tigaon', 'JJP'): 'TIKA RAM',
    ('Badhra', 'JJP'): 'YASHVIR',
    ('Karnal', 'JJP'): 'JETENDER ROYAL',
    ('Rohtak', 'INLD'): 'DILOUR MEHRA',
    ('Pataudi', 'JJP'): 'AMARNATH J. E.',
    ('Sonipat', 'INLD'): 'SARDHARAM SINGH',
    ('Hathin', 'INLD'): 'TAYUB HUSAIN URF NAZIR AHMED',
    ('Hathin', 'JJP'): 'RAVINDER KUMAR',
    ('Israna', 'INLD'): 'SURAJBHAN',
    ('Israna', 'JJP'): 'KUMAR SUNIL',
    ('Baroda', 'BSP'): 'DHARAM VIR',
    ('Guhla', 'JJP'): 'KRISHAN KUMAR',
    ('Badli', 'JJP'): 'KRISHAN KUMAR',
    ('Palwal', 'ASP(KR)'): 'KUMAR HARIT',
}
# Note: Ratia BSP (Chhindwara Pal) withdrew - intentionally unmatched.

# (AC, party) pairs where the extracted ballot name is glitched -> use party-list spelling
NAME_FROM_LIST = {('Julana', 'INC'), ('Hodal', 'INC')}

REPORT_NOTES = [
    'HARYANA 2024 ASSEMBLY - VILLAGE-WISE RESULTS: DATA VALIDATION REPORT',
    '',
    'Source: Form 20 Final Result Sheets (CEO Haryana), 90 ACs; booth-to-village mapping user-provided.',
    'Validation: every booth row checksummed; per-candidate booth sums matched against Form 20 EVM totals.',
    'Shahbad: Form 20 not released; AC-level ECI totals with status AC_TOTAL_ONLY. App must show overall',
    'result with footer: "Government is yet to release Form 20 (booth-wise) data for this constituency."',
    'Ratia BSP candidate withdrew (confirmed). Jind JJP appears on ballot as Dharam Pal Tanwar (confirmed).',
    'Postal ballots are AC-level and excluded from village numbers - show separately in the app.',
    'Auxiliary booths (e.g. 160A) are credited to the parent booth village.',
]
