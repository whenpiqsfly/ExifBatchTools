"""
MIT License
Copyright 2020-2023 David C. Lien

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import argparse
import logging
from argparse import RawTextHelpFormatter

from EBTDedupe import EBTDedupe
from EBTSort import EBTSort

# parse arguments
desc = """
A small collection of commandline tools to help organize large collections of
photos and videos. If you're anal, lazy and paranoid like me, you
  a. want to keep your photos perfectly organized, but 
  b. procrastinated and accumulated years of unsorted photos, and
  c. you do not trust any one specific cloud service to manage your precious
     memories, knowing they may decide to drop support for your backup app at
     any time or to discontinue the service altogether, *ahem* amazon photos.
ExifBatchTools.py is the main script that allows you to access other functions
by specifying run modes (stackable).

--dedupe

dedupe mode dedupes files between source and target directory with options to
loosen match criteria. By default, the script matchs filename + size + modtime.
You may optionally instruct the script to ignore size and/or modtime. This is
useful if various backup/copy operations causes the files to no longer reflect
the  original timestamp; or if the backup app stores lower resolution copies to
save space. If size is ignored and a match is found, the larger file is kept.
That is, if target file is LARGER than source file. the script OVERWRITES the
source file with target file. Similarly, if modtime is ignored and the target is
OLDER than the source, script attempts to MOVE the target file to source file.

WARNING: THIS SCRIPT IS NOT A REGULAR DEDUPE TOOL AND AGGRESSIVELY PRUNE SMALLER
FILES IF REQUESTED. YOU MAY LOSE DATA IF SCRIPT IS USED INCORRECTLY. It serves a
very specific use case of attempting to have 1 copy of best quality/original
date photo/video at the source location

--sort

sort mode attempts to move photos and videos from target directory into the
existing directory structure in source directory, provided the source dirs are
populated with existing photos. This is useful when you need to sort from
multiple sources into the same folders (say, your phone and your SO's phone). 
You've sorted your photos into directories and now want to sort your SO's
photos into the same directories. For each photo in target directory, the script
reads the date taken from its exif data. It then looks for a folder in the
source directory where photos of the same date are stored, and moved the target
photo there undered 'moved' subdirectory. For example, it'd move
'target/IMG_2018_0919_122147.jpg' to
'source/2018/09 Monterrey Trip/moved/IMG_2018_0919_122147.jpg'
if the '09 Monterray Trip' folders contains other photos from 2018/09/19.

--fix_dates (TODO)

fix_dates mode fixes ctime and mtime of photos in source directory. This can be
easily accomlished with exiftool (-DateTimeOriginal>FileCreateDate), but can be
imprecise since standard exif doesn't store timezone information. If you are
organizing your France photos in San Francisco, you'd be off by 9 hours (or 10,
depending on daylight saving). This script attempts to account for timezone
difference by reading GPS data from exif, match it against a timezone, and
compare against local machine timezone to compute the correct ctime and mtime.

"""

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

def main():
    parser = argparse.ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-dedupe', action='store_true', help="Dedupe mode - Remove the dupes in target directory.")
    parser.add_argument('-sort', action='store_true', help="Sort mode - Sort images from target directory into source directory.")

    parser.add_argument('-s', '--source', type=str, required=True, default=None, help="Source of truth directory")
    parser.add_argument('-t', '--target', type=str, required=True, default=None, help="Duplicate and/or unsorted directory to analyze")
    parser.add_argument('-n', '--num', type=int, default=0, help="Quit after num duplicates are found")
    parser.add_argument('-l', '--logfile', type=str, default="./DedupeFiles.log", help="Set location of logfile")
    parser.add_argument('-v', '--verbose', action='store_true', help="Print extra information")
    parser.add_argument('-ignore_mtime', action='store_true', help="[Dedupe mode] Ignores modified timestamp when matching")
    parser.add_argument('-ignore_size', action='store_true', help="[Dedupe mode] Ignores file size when matching")

    args = parser.parse_args()

    # setup logging
    logger = logging.getLogger('DedupeFiles')
    handler = logging.FileHandler(args.logfile, 'w', encoding = 'utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler) 
    logger.setLevel(logging.INFO)

    mode = set()
    if args.dedupe:
        mode.add("Dedupe")
    if args.sort:
        mode.add("Sort")

    if not mode:
        parser.error('No mode specified, add -dedupe or -sort (or both)')

    print("Mode:            ", mode)
    print("Ignore mtime:    ", str(args.ignore_mtime))
    print("Ignore size:     ", str(args.ignore_size))
    print("Source directory:", args.source)
    print("Target directory:", args.target)
    print("Logfile:         ", args.logfile)
    print("File limit:      ", args.num, "(0 = unlimited)")
    print("Verbose:         ", str(args.verbose))


    if args.dedupe:
        dedupe = EBTDedupe(args.source, args.target, args.ignore_mtime, args.ignore_size)
        if dedupe is not None:
            dry_run = query_yes_no("Dry run?")
            dedupe.Dedupe(dry_run,  args.verbose, args.num, logger)
    if args.sort:
        sort = EBTSort(args.source, args.target)
        if sort is not None:
            dry_run = query_yes_no("Dry run?")
            sort.Sort(dry_run, args.num, logger)

if __name__ == "__main__":
         main()