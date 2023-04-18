"""
- scans source folder recursively and stores dates taken exif data into hash [date, [array of folder paths]], 
- scans target folder recursively, if date taken matches at least 1 folder in hash (matched folder), create a 'moved' folder in the matched folder and move the photo there.
"""
from exif import Image
from halo import Halo
from datetime import datetime
import glob
import os

class EBTSort:
    def __init__(self, source, target):
        self.source = source
        self.target = target

        # build a dictionary from target directory tree
        src_spinner = Halo(text='Generating library from source directory...', spinner='dots')
        src_spinner.start()
        self.targetLibrary = {}
        for filepath in glob.iglob(os.path.join(target,'**'), recursive=True):
            # skip synology meta data folders
            if (filepath.find("@eaDir") != -1):
                continue

            # TODO: check to see file is image or video
            if os.path.isfile(filepath):
                fileDate = self._GetExifDateAsString(filepath)
                if fileDate:
                    folderPath = os.path.dirname(filepath)
                    # add date as key if not exist
                    if fileDate not in self.targetLibrary:
                        self.targetLibrary[fileDate] = { folderPath }
                    # add folder into value set if not exist
                    elif folderPath not in self.targetLibrary[fileDate]:
                        self.targetLibrary[fileDate].add(folderPath);

        src_spinner.succeed("Generating library from target directory...Done!")
        print("  Indexed", str(len(self.targetLibrary)), "files in", target)

    def Sort(self, dry_run, limit, logger):
        target_spinner = Halo(text='Finding movable files in source directory (dry run)...', spinner='dots')
        if not dry_run:
            target_spinner.text = "Moving files from source directory to target directory..."
        target_spinner.start()

        counter = 0
        moved = 0
        for filepath in glob.iglob(os.path.join(self.source,'**'), recursive=True):
            # skip synology meta data folders
            if (filepath.find("@eaDir") != -1):
                continue

            # TODO: check to see file is image or video
            if os.path.isfile(filepath):
                fileDate = self._GetExifDateAsString(filepath)
                if fileDate and fileDate in self.targetLibrary:
                    counter += 1
                    folderPaths = self.targetLibrary[fileDate]
                    if len(folderPaths) > 1:
                        logger.warn("Photos from " + fileDate + "are in" + str(len(self.folderPaths)) + "directories, picking the first folder.")
                    targetFolder = os.path.join(folderPaths[0],"moved")
                    targetFolder.mkdir(parents=False, exist_ok=True)
                    target = os.path.join(targetFolder, os.path.basename(filepath))
                    try:
                        os.rename(filepath, target)
                        logger.info("Moved " + filepath + " to " + target)
                        moved += 1
                        if limit > 0 and moved >= limit:
                            break
                    except OSError as err:
                        print("OS error: {0}".format(err))
                        logger.warning("Failed to rename " + filepath + " to " + target + ":" + repr(err))

        target_spinner.text += "Done!"
        target_spinner.succeed()
        print("  Found", str(moved), "movable files out of", str(counter), "files in", self.source)
        logger.info("  Found " + str(moved) + " movable files out of " + str(counter) + " files in " + self.source)
        if not dry_run:
            print("  Moved", str(moved), "files out of", str(counter), "files in", self.source)
            logger.info("  Moved " + str(moved) + " files " + str(counter) + " files in " + self.source)

    def _GetExifDateAsString(self, filepath):
        try:
            with open(filepath, 'rb') as image_file:
                image_obj = Image(image_file)
                if image_obj.has_exif:
                    # 2018:09:19 12:21:47
                    # doing the conversion to and back ensures that the timestamp
                    # is formatted correctly
                    datetimeObj = datetime.strptime(image_obj.datetime_original, '%Y:%m:%d %H:%M:%S')
                    return datetimeObj.strftime("%Y%m%d")

        except OSError as err:
            print("OS error: {0}".format(err))

        print("Failed obtain date taken from " + filepath)
        return None
