"""
MiVote - assemble the deployable site from the template and the data folder.

  webapp_template.html  +  webapp_data/*.json   ->   mivote_site/
"""
import json, os, shutil

SRC_HTML = 'webapp_template.html'
SRC_DATA = 'webapp_data'
OUT = 'mivote_site'


def main():
    dir_json = json.load(open(f'{SRC_DATA}/_dir.json'))
    html = open(SRC_HTML, encoding='utf-8').read()
    html = html.replace('/*DATA*/', '{}').replace('/*DIR*/', json.dumps(dir_json, separators=(',', ':')))

    os.makedirs(f'{OUT}/data', exist_ok=True)
    open(f'{OUT}/index.html', 'w', encoding='utf-8').write(html)
    n = 0
    for f in os.listdir(SRC_DATA):
        if f.endswith('.json'):
            shutil.copy2(f'{SRC_DATA}/{f}', f'{OUT}/data/{f}')
            n += 1
    if os.path.exists('README.md'):
        shutil.copy2('README.md', f'{OUT}/README.md')
    size = sum(os.path.getsize(os.path.join(dp, f))
               for dp, _, fs in os.walk(OUT) for f in fs)
    print(f'index.html  {os.path.getsize(f"{OUT}/index.html")/1024:.0f} KB')
    print(f'data files  {n}')
    print(f'total       {size/1e6:.1f} MB')
    ls = [a['n'] for a in dir_json if a.get('ls24')]
    print(f'LS 2024 village layer on {len(ls)} constituencies: {", ".join(ls)}')


if __name__ == '__main__':
    main()
