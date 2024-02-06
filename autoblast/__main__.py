#!/usr/bin/env python
from io import StringIO
from pathlib import Path
import os
import re
import tempfile

import pandas as pd
import click
import pexpect



def parse_outfmt(outfmt):
    # Default delimiter
    delimiter = ' '

    # Regular expression pattern to match optional number and optional delim
    pattern = r'^(\d+)?\s?(delim=.)?\s?(.*)$'
    match = re.match(pattern, outfmt)

    if match:
        # If delim is provided, extract the delimiter
        if match.group(2):
            delimiter = match.group(2).split('=')[1]

        # The remainder are the column headers
        column_headers = match.group(3).split()

    return delimiter, column_headers


@click.command()
@click.argument('file_path', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--max-seqs-per-file', '--nseqs', type=int)
@click.option('--bin', default='blastn', type=str, help="Path to the binary or the binary name if it's in the system's PATH.")
# @click.option('--db', default='nt')
@click.option('--taxdb')
@click.option('--max_target_seqs', default=1, type=int)
@click.option('--outfmt', default='6 delim=, qseqid sseqid evalue bitscore pident length sgi sacc staxids sscinames scomnames', type=str)
def main(file_path, max_seqs_per_file, bin, taxdb, max_target_seqs, outfmt):
    """
    eDNA data processing
    """

    df = pd.read_excel(file_path, engine='openpyxl')

    max_seqs_per_file = max_seqs_per_file if max_seqs_per_file else len(df)
    delimiter, column_headers = parse_outfmt(outfmt)
    outdf = pd.DataFrame(columns=column_headers)
    env = os.environ
    if taxdb is not None:
        env['BLASTDB'] = str(Path(taxdb).resolve())
    for i in range(0, len(df), max_seqs_per_file):
        with tempfile.NamedTemporaryFile() as output_file:
            with open(output_file.name, 'w', encoding='utf-8') as f:
                for j, row in enumerate(df.iloc[i:i+max_seqs_per_file].itertuples()):
                    f.write(f'>seq{j:d}\n')
                    f.write(f'{row.sequence}\n')
                cmd = [
                        str(bin),
                        '-remote',
                        '-db',
                        'nt',
                        '-query',
                        output_file.name,
                        '-max_target_seqs',
                        str(max_target_seqs),
                        '-outfmt',
                        f"'{outfmt}'",
                    ]
                print(' '.join(cmd))
                with pexpect.spawn(
                        ' '.join(cmd),
                        timeout=None,
                        encoding='utf-8',
                        env=env,
                        ) as child:
                    child.expect(pexpect.EOF)
            outlines = []
            for line in child.before.split('\n'):
                if 'warning' in line.lower():
                    continue
                outlines.append(line)
            outdf = pd.concat([outdf, pd.read_csv(StringIO('\n'.join(outlines)), sep=delimiter, names=column_headers)])
    outdf.to_csv(file_path.with_suffix('.csv'), index=False)


if __name__ == "__main__":
    main()
