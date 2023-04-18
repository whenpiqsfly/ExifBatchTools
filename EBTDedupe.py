import os
import glob
import hashlib
import shutil
from pathlib import Path
from halo import Halo

class EBTDedupe:
    def __init__(self, source, target, ignore_mtime, ignore_size):
        self.source = source
        self.target = target
        self.ignore_mtime = ignore_mtime
        self.ignore_size = ignore_size

        # build a dictionary from source directory tree
        src_spinner = Halo(text='Generating library from source directory...', spinner='dots')
        src_spinner.start()
        self.library = {}
        for filepath in glob.iglob(os.path.join(source,'**'), recursive=True):
            # skip synology meta data folders
            if (filepath.find("@eaDir") != -1):
                continue

            if os.path.isfile(filepath):
                hashkey = self._CreateKey(filepath, ignore_mtime, ignore_size)
                self.library[hashkey] = filepath
        src_spinner.succeed("Generating library from source directory...Done!")
        print("  Indexed", str(len(self.library)), "files in", source)

    def Dedupe(self, dry_run, verbose, limit, logger):
        # file dupes in dest directory
        counter = 0
        dupes = 0
        deleted = 0
        target_spinner = Halo(text='Finding duplicates from target directory (dry run)...', spinner='dots')
        if not dry_run:
            target_spinner.text = "Finding and deleting duplicates from target directory..."
        target_spinner.start()
        for filepath in glob.iglob(os.path.join(self.target,'**'), recursive=True):
            # skip synology meta data folders
            if (filepath.find("@eaDir") != -1):
                continue

            # TODO: check to see file is image or video
            if os.path.isfile(filepath) :
                hashkey = self.create_key(filepath, self.ignore_mtime, self.ignore_size)
                srcfile = self.library.get(hashkey)
                counter += 1

                if srcfile is not None:
                    # sanity check - in case source and target folder overlap.
                    if srcfile == filepath:
                        logger.warning("source and target file are the same! skipping " + filepath)
                        continue

                    logger.info("Found dupe! " + srcfile + " and " + filepath + " matches!")
                    overwrite = False
                    move = False
                    if verbose or not dry_run:
                        # overwrite if size is ignored and target file is larger than source file,
                        if self.ignore_size:
                            src_size = Path(srcfile).stat().st_size
                            tgt_size = Path(filepath).stat().st_size
                            logger.info("src size: " + str(src_size))
                            logger.info("tgt size: " + str(tgt_size))
                            if tgt_size > src_size:
                                overwrite = True
                        # overwrite if mtime is ignored and target file is older than source file,
                        if overwrite == False and self.ignore_mtime:
                            src_mtime = Path(srcfile).stat().st_mtime
                            tgt_mtime = Path(filepath).stat().st_mtime
                            logger.info("src mtime: " + str(src_mtime))
                            logger.info("tgt mtime: " + str(tgt_mtime))
                            if tgt_mtime < src_mtime:
                                move = True                    

                    if not dry_run:
                        try:
                            if overwrite or move:
                                try:
                                    os.rename(filepath, srcfile)
                                    logger.info("Moved " + filepath + " to " + srcfile)
                                except OSError as err:
                                    # most likely failure reason: rename across local and network drives
                                    # for overwrites: try copy first before delete
                                    logger.warning("Failed to rename " + filepath + " to " + srcfile + ":" + repr(err))
                                    if overwrite:
                                        shutil.copy2(filepath, srcfile)
                                        logger.info("Copied " + filepath + " to " + srcfile)
                                    os.remove(filepath)
                                    logger.info("Deleted " + filepath)
                                    # if we fail here again let it fail.
                            else:
                                os.remove(filepath)
                                logger.info("Deleted " + filepath)
                            deleted += 1
                        except OSError as err:
                            print("OS error: {0}".format(err))
                            logger.error("Failed to delete " + filepath + ": " + repr(err))
                            # break on any error
                            break
                    dupes += 1
                    if limit > 0 and dupes >= limit:
                        break

        target_spinner.text += "Done!"
        target_spinner.succeed()
        print("  Found", str(dupes), "duplicates out of", str(counter), "files in", self.target)
        logger.info("  Found " + str(dupes) + " duplicates out of " + str(counter) + " files in " + self.target)
        if not dry_run:
            print("  Deleted", str(deleted), "duplicates out of", str(counter), "files in", self.target)
            logger.info("  Deleted " + str(deleted) + " duplicates " + str(counter) + " files in " + self.target)



    def _CreateKey(self, filepath, ignore_mtime, ignore_size):
        stats = Path(filepath).stat()
        filename = os.path.basename(filepath)
        filestats = filename
        if not ignore_size:
            filestats += str(stats.st_size)
        if not ignore_mtime:
            filestats += str(stats.st_mtime)
        hashkey = hashlib.sha1(filestats.encode('utf-8')).hexdigest()
        # print ("created hash key", hashkey,"from",filestats,"for",filepath)
        return hashkey

