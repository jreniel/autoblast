#!/usr/bin/env python
from io import StringIO
from pathlib import Path
import argparse
import re
import tempfile

import pandas as pd
import pexpect


def get_argument_parser():
    parser = argparse.ArgumentParser(description='eDNA data processing')
    parser.add_argument('file_path', type=Path)
    parser.add_argument('--max-seqs-per-file', '--nseqs', type=int)
    parser.add_argument('--bin', type=Path, default='blastn')
    parser.add_argument('--db', default='nt')
    parser.add_argument('--max_target_seqs', default=1, type=int)
    parser.add_argument('--outfmt', default='6 delim=, qseqid sseqid evalue bitscore pident length sgi sacc staxids sscinames scomnames', type=str)
    return parser

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

def main(args):

    df = pd.read_excel(args.file_path, engine='openpyxl')

    max_seqs_per_file = args.max_seqs_per_file if args.max_seqs_per_file else len(df)
    delimiter, column_headers = parse_outfmt(args.outfmt)
    outdf = pd.DataFrame(columns=column_headers)
    for i in range(0, len(df), max_seqs_per_file):
        output_file = tempfile.NamedTemporaryFile(delete=False)
        with open(output_file.name, 'w') as f:
            for j, row in enumerate(df.iloc[i:i+max_seqs_per_file].itertuples()):
                f.write(f'>seq{j:d}\n')
                f.write(f'{row.sequence}\n')
        cmd = [
                str(args.bin),
                '-remote',
                '-db',
                args.db,
                '-query',
                output_file.name,
                '-max_target_seqs',
                str(args.max_target_seqs),
                '-outfmt',
                f"'{args.outfmt}'",
            ]
        print(' '.join(cmd))
        with pexpect.spawn(
                ' '.join(cmd),
                timeout=None,
                encoding='utf-8',
                ) as child:
            child.expect(pexpect.EOF)
        outlines = []
        for line in child.before.split('\n'):
            if 'warning' in line.lower():
                continue
            outlines.append(line)
        outdf = pd.concat([outdf, pd.read_csv(StringIO('\n'.join(outlines)), sep=delimiter, names=column_headers)])
    outdf.to_csv(args.file_path.with_suffix('.csv'), index=False)


if __name__ == "__main__":
    main(get_argument_parser().parse_args())
