# autoblast

A wrapper for multi-query blastn
---

## Requirements:

There are two important pre-requisites:

### Pre-requisite 1: The `blastn` binary

To begin with, it is recommended that you make sure you have blast installed in your computer before you proceed.
To check if it is installed, you may run the command `blastn` in your terminal and see if that works.
If it does, you're ready to proceed!
If it doesn't (e.g. command not found) then you need to fix that before moving on.

The blast binaries are typically located on https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/

If you are using Mac, you may download the version that ends with .dmg, which can be used to install blast "globally".
Note that after installing blast globally you may need to close and reopen the terminal so that the installation takes effect.

The alternatives, which applies to any platform, is to download the pre-compiled binaries and either add them to your PATH variable or use the `--bin` flag in autoblast to point to the binary path.

For example, on my Linux machine I decided not to install blast globally, and just download blast as standalone.
In that case, I can use: `--bin $HOME/ncbi-blast-2.14.0+/bin/blastn` when calling autoblast, and that will ensure that this is the binary used.
Naturally, you would need to adjust this path to your case.

### Pre-requisite 2: The blast taxonomic database

You will also need to download a copy of the blast taxonomic database.
This database is normally found at: ftp://ftp.ncbi.nlm.nih.gov/blast/db/taxdb.tar.gz
You will need to untar this file somewhere, which the `blastn` binary will try to use for cross-referencing it's output and providing taxonomic information.
Now, what's important to note is the following: in reality you only need to keep 1 copy of this database in your machine.
Naturally, you don't want to keep multiple copies of the same file scattered around your computer and taking up space.
Because of this, you have to somehow tell `blastn` where this database is located, and as you may have already guessed, there are multiple ways that this can be achieved.

To begin with, I will refer to the official documentation on blast which is found here: https://www.ncbi.nlm.nih.gov/books/NBK569858/

To summarize the information above into the parts relevat for autoblast, you have some options:

1. You can use the `BLASTDB` environment variable like this:  `export BLASTDB=/path/to/where/you/untarred/` before executing autoblast. Note that this method will only persist in the current shell, and if you close the sheel and reopen it, you will need to set this variable again, unless of course, you add it to your shell's rc file, in which case then it becomes "permanent". If you don't know what any of this means, feel free to paste this in your favorite AI tool to get more insights.

2. You can symlink the database into your current working directory, and blast should pick it up automagically.

3. You can use the `--taxdb=/path/to/where/you/untarred` the db and autoblast will take care internally of passing this information to blastn.

## Installing autoblast

First, you need to make sure your shell is currently using Python version 3.8 or greater.
Some computers in the wild still use Python 2.7 as default (I'm looking at you, MacOS).

To check which Python version you are using, simply execute: `python --version`.

On the other hand, as is typical with Python, it is highly recommended that you use a virtual environment.
There are way too many guides online on this topic, so I won't go into details about it.
You can always ask your favorite AI tool or local Python nerd for guidance on this, and at least one of them will be happy to guide you.
However I will provide here a quick hint into the process, assuming you are using conda:

```bash
conda create -n autoblast python=3.12 -y
```
and then
```bash
conda activate autoblast
```

Back to the topic of installation, assuming you have Python 3.8 or more, for most users, the installation can be as easy as executing:

`pip install git+https://code.wm.edu/jrcalzada/autoblast/`

and if all goes well, you are ready to use autoblast!

You can check that autoblast was installed by executing in your terminal the command:
`autoblast --help`

Naturally, you can always clone this repo and do a `pip install .` over it.

**This package is not in pip, by the way.**

I could put it in pip, but I don't see a good reason to do so at this stage.
Maybe I'll push it to PyPi soon, we'll see.

## Using autoblast

Ok, so this is where the actual fun begins! We have autoblast ready to roll, so how do we use it?
First, you will need an excel file.
The only thing that is **required** on this excel file is to have a header column named `sequence` that contains, you guessed it, the sequences!
You can have other header colums, they will be ignored by autoblast.
