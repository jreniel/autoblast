#!/usr/bin/env python
import asyncio
import os
import re
import tempfile
from io import StringIO
from pathlib import Path

import click
import numpy as np
import pandas as pd
import pexpect


def parse_outfmt(outfmt):
    # Default delimiter
    delimiter = " "

    # Regular expression pattern to match optional number and optional delim
    pattern = r"^(\d+)?\s?(delim=.)?\s?(.*)$"
    match = re.match(pattern, outfmt)

    if match:
        # If delim is provided, extract the delimiter
        if match.group(2):
            delimiter = match.group(2).split("=")[1]

        # The remainder are the column headers
        column_headers = match.group(3).split()

    return delimiter, column_headers


async def process_chunk(
    df_chunk, binary, max_target_seqs, outfmt, env, timeout, delimiter, column_headers
):
    with tempfile.NamedTemporaryFile() as output_file:
        with open(output_file.name, "w", encoding="utf-8") as f:
            for j, row in enumerate(df_chunk.itertuples()):
                f.write(f">seq{j:d}\n")
                f.write(f"{row.sequence}\n")
        cmd = [
            str(binary),
            "-remote",
            "-db",
            "nt",
            "-query",
            output_file.name,
            "-max_target_seqs",
            str(max_target_seqs),
            "-outfmt",
            f"'{outfmt}'",
        ]
        print(" ".join(cmd))
        with pexpect.spawn(
            " ".join(cmd),
            timeout=timeout,
            encoding="utf-8",
            env=env,
        ) as child:
            index = await child.expect([pexpect.EOF, pexpect.TIMEOUT], async_=True)
        if index == 1:
            return pexpect.TIMEOUT
        outlines = []
        for line in child.before.split("\n"):
            if "warning" in line.lower():
                continue
            outlines.append(line)

        return pd.read_csv(
            StringIO("\n".join(outlines)),
            sep=delimiter,
            names=column_headers,
        )


async def process_as_completed(jobs, max_concurrent_tasks):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def sem_task(job):
        async with semaphore:
            return await process_chunk(*job)

    tasks = [asyncio.create_task(sem_task(job)) for job in jobs]
    results = []
    for completed_future in asyncio.as_completed(tasks):
        results.append(await completed_future)
        print(results[-1])
    return results


def parse_timedelta(ctx, param, value):
    try:
        return pd.Timedelta(value).to_pytimedelta().total_seconds()
    except ValueError as e:
        raise click.BadParameter(f"Could not parse '{value}' as pd.Timedelta: {e}")


@click.command()
@click.argument(
    "file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--max-seqs-per-file", "--nseqs", type=int, default=50)
@click.option(
    "--bin",
    default="blastn",
    type=str,
    help="Path to the binary or the binary name if it's in the system's PATH.",
)
# @click.option('--db', default='nt')
@click.option("--taxdb")
@click.option("--max_target_seqs", default=1, type=int)
@click.option(
    "--outfmt",
    default="6 delim=, qseqid sseqid evalue bitscore pident length sgi sacc staxids sscinames scomnames",
    type=str,
)
@click.option(
    "--timeout",
    default="20m",
    callback=parse_timedelta,
    help="Timeout period. Specify in pandas Timedelta string format (e.g., '30s', '2h', '1d').",
)
@click.option("--max_concurrent_tasks", default=4, type=int)
def main(
    file_path,
    max_seqs_per_file,
    bin,
    taxdb,
    max_target_seqs,
    outfmt,
    timeout,
    max_concurrent_tasks,
):
    """
    eDNA data processing
    """

    df = pd.read_excel(file_path, engine="openpyxl")

    max_seqs_per_file = max_seqs_per_file if max_seqs_per_file else len(df)

    df_no_duplicates = df.dropna().drop_duplicates("sequence")
    nitems = np.ceil(len(df_no_duplicates) / max_seqs_per_file)

    df_chunks = np.array_split(df_no_duplicates, nitems)

    delimiter, column_headers = parse_outfmt(outfmt)
    env = os.environ.copy()
    if taxdb is not None:
        env["BLASTDB"] = str(Path(taxdb).resolve())
    jobs = [
        (
            chunk,
            bin,
            max_target_seqs,
            outfmt,
            env,
            timeout,
            delimiter,
            column_headers,
        )
        for chunk in df_chunks
    ]

    results = asyncio.get_event_loop().run_until_complete(
        process_as_completed(jobs, max_concurrent_tasks)
    )
    print(results)
    # timeouts = []
    # for future in asyncio.as_completed(asyncio.gather(futures)):
    #     print(future)

    # with Pool(cpu_count()) as pool:
    #     results = pool.starmap(process_chunk, jobs)
    # retry = []
    # final_results = []
    # for i, result in enumerate(results):
    #     if isinstance(result, pexpect.TIMEOUT):
    #         retry.append(jobs[i])
    #     final_results.append(result)

    # print(retry)
    # print(final_results)

    # outdf.to_csv(file_path.with_suffix(".csv"), index=False)


if __name__ == "__main__":
    main()
