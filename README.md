```
usage: ExifBatchTools.py [-h] (--dedupe | --sort) -s SOURCE -t TARGET [-n NUM] [-l LOGFILE] [-v] [--ignore_mtime]
                         [--ignore_size]

A small collection of commandline tools to help organize large collections of
photos and videos.

options:
  -h, --help            show this help message and exit
  --dedupe              Dedupe mode - Remove the dupes in target directory.
  --sort                Sort mode - Sort images from target directory into source directory.
  -s SOURCE, --source SOURCE
                        Source of truth directory
  -t TARGET, --target TARGET
                        Target directory to analyze
  -n NUM, --num NUM     Quit after num duplicates are found
  -l LOGFILE, --logfile LOGFILE
                        Set location of logfile
  -v, --verbose         Print extra information
  --ignore_mtime        [Dedupe mode] Ignores modified timestamp when matching
  --ignore_size         [Dedupe mode] Ignores file size when matching
```

# ExifBatchTools

A small collection of commandline tools to help organize large collections of
photos and videos. If you're anal, lazy and paranoid like me, you

* want to keep your photos perfectly organized, but
* procrastinated and accumulated years of unsorted photos, and
* you do not trust any one specific cloud service to manage your precious
   memories, knowing they may decide to drop support for your backup app at
   any time or to discontinue the service altogether, *ahem* amazon photos.

ExifBatchTools.py is the main script that allows you to access other functions
by specifying run modes.

## dedupe

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

## sort

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

## fix_dates (TODO)

fix_dates mode fixes ctime and mtime of photos in target directory. This can be
easily accomlished with exiftool (-DateTimeOriginal>FileCreateDate), but can be
imprecise since standard exif doesn't store timezone information. If you are
organizing your France photos in San Francisco, you'd be off by 9 hours (or 10,
depending on daylight saving). This script attempts to account for timezone
difference by reading GPS data from exif, match it against a timezone, and
compare against local machine timezone to compute the correct ctime and mtime.
