#!/usr/bin/env python
from multiprocessing import Pool
from pathlib import Path
import argparse
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
    parser.add_argument('--outfmt', default='6 qseqid sseqid evalue bitscore pident length sgi sacc staxids sscinames scomnames', type=str)
    return parser


def run_blast(cmd):
    print(' '.join(cmd))
    with pexpect.spawn(
            ' '.join(cmd),
            timeout=None,
            encoding='utf-8',
            ) as child:
        child.expect(pexpect.EOF)
        return child.before


def main(args):

    df = pd.read_excel(args.file_path, engine='openpyxl')
    max_seqs_per_file = args.max_seqs_per_file if args.max_seqs_per_file else len(df)

    files_to_process = []
    for i in range(0, len(df), max_seqs_per_file):
        output_file = tempfile.NamedTemporaryFile()
        with open(output_file.name, 'w') as f:
            for index, row in df.iloc[i:i+max_seqs_per_file].iterrows():
                f.write(f'>seq{index:d}\n')
                f.write(f'{row["sequence"]}\n')
        files_to_process.append(output_file)

    cmds = []
    for file_to_process in files_to_process:
        cmds.append([
                str(args.bin),
                '-remote',
                '-db',
                args.db,
                '-query',
                file_to_process.name,
                '-max_target_seqs',
                str(args.max_target_seqs),
                '-outfmt',
                f"'{args.outfmt}'",
            ])
    with Pool() as pool:
        results = pool.map(run_blast, cmds)
    breakpoint()


if __name__ == "__main__":
    main(get_argument_parser().parse_args())
