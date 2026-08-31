"""Run the full Form 20 -> village-wise results pipeline for one election.

Usage: python run_pipeline.py elections/haryana_2024
"""
import sys, os, importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import build, parties, report


def load_config(election_dir):
    spec = importlib.util.spec_from_file_location('config', os.path.join(election_dir, 'config.py'))
    cfg = importlib.util.module_from_spec(spec)
    cfg.BASE_DIR = os.path.abspath(election_dir)
    spec.loader.exec_module(cfg)
    return cfg


def main():
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    cfg = load_config(sys.argv[1])
    print('=== STEP 1-2: parse Form 20s, extract names, aggregate, build DB ===')
    db_path, _ = build.run(cfg)
    if getattr(cfg, 'PARTY_LIST', None) and os.path.exists(cfg.PARTY_LIST):
        print('\n=== STEP 3: match party list ===')
        parties.run(db_path, cfg)
    else:
        print('\n(no party_list.txt - skipping party matching)')
    print('\n=== STEP 4: report + exports ===')
    import shutil
    report.run(db_path, cfg)
    shutil.copy(db_path, os.path.join(cfg.OUTPUT_DIR, 'results.db'))
    print('\nDone. Deliverables in', cfg.OUTPUT_DIR)


if __name__ == '__main__':
    main()
