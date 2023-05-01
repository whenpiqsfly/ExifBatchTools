"""
- scans target folder recursively and stores dates taken exif data into hash [date, [array of folder paths]], 
- scans source folder recursively, if date taken matches at least 1 folder in source hash (matched folder), create a 'moved' folder in the matched folder and move the photo there.
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

        # build a dictionary from source directory tree
        sourceSpinner = Halo(text='Generating library from source of truth directory...', spinner='dots')
        sourceSpinner.start()
        self.sourceLibrary = {}
        for filePath in glob.iglob(os.path.join(source,'**'), recursive=True):
            if not self._IsImageFile(filePath):
                continue

            fileDate = self._GetExifDateAsString(filePath)
            if fileDate:
                folderPath = os.path.dirname(filePath)
                # add date as key if not exist
                if fileDate not in self.sourceLibrary:
                    self.sourceLibrary[fileDate] = [folderPath]
                # add folder into value list if not exist
                elif folderPath not in self.sourceLibrary[fileDate]:
                    self.sourceLibrary[fileDate].append(folderPath);

        sourceSpinner.succeed("Generating library from source directory...Done!")
        print("  Indexed", str(len(self.sourceLibrary)), "folders in", source)

    def Sort(self, dry_run, limit, logger):
        targetSpinner = Halo(text='Finding movable files in target directory (dry run)...', spinner='dots')
        if not dry_run:
            targetSpinner.text = "Moving files from target directory to source of truth directory..."
        targetSpinner.start()

        counter = 0
        moved = 0
        for filePath in glob.iglob(os.path.join(self.target,'**'), recursive=True):
            if not self._IsImageFile(filePath):
                continue

            counter += 1
            fileDate = self._GetExifDateAsString(filePath)
            if not fileDate:
                logger.warn("No exif data found for " + filePath + ". Skipping...")
                continue

            if not (fileDate in self.sourceLibrary):
                logger.warn("No photos with matching date " + fileDate + " found for " + filePath + ". Skipping...")
                continue

            folderPaths = self.sourceLibrary[fileDate]
            if len(folderPaths) > 1:
                logger.warn("Photos from " + fileDate + " are in " + str(len(folderPaths)) + " directories, picking the first folder.")
            destFolder = os.path.join(folderPaths[0],"moved")
            destPath = os.path.join(destFolder, os.path.basename(filePath))

            if dry_run:
                logger.info("Will move " + filePath + " to " + destPath)
                moved += 1
                continue

            try:
                os.makedirs(destFolder, exist_ok=True)
                os.rename(filePath, destPath)
                logger.info("Moved " + filePath + " to " + destPath)
                moved += 1
                if limit > 0 and moved >= limit:
                    break
            except OSError as err:
                print("OS error: {0}".format(err))
                logger.warning("Failed to rename " + filePath + " to " + destPath + ":" + repr(err))

        targetSpinner.text += "Done!"
        targetSpinner.succeed()
        print("  Found", str(moved), "movable files out of", str(counter), "files in", self.target)
        logger.info("  Found " + str(moved) + " movable files out of " + str(counter) + " files in " + self.target)
        if not dry_run:
            print("  Moved", str(moved), "files out of", str(counter), "files to", self.source)
            logger.info("  Moved " + str(moved) + " files " + str(counter) + " files to " + self.source)

    def _IsImageFile(self, filePath):
        # skip synology meta data folders
        if (filePath.find("@eaDir") != -1):
            return False
        # skip non-files
        if not os.path.isfile(filePath):
            return False
        # only jpegs and tiffs have exif data
        if not filePath.lower().endswith(('.jpg', '.jpeg', '.jpe', '.jif', '.jfif', '.tif', '.tiff')):
            return False
        return True

    def _GetExifDateAsString(self, filePath):
        try:
            with open(filePath, 'rb') as imageFile:
                imageObj = Image(imageFile)
                if imageObj.has_exif and imageObj.get("datetime_original"):
                    # 2018:09:19 12:21:47
                    # doing the conversion to and back ensures that the timestamp
                    # is formatted correctly
                    datetimeObj = datetime.strptime(imageObj.datetime_original, '%Y:%m:%d %H:%M:%S')
                    return datetimeObj.strftime("%Y%m%d")

        except OSError as err:
            print("OS error: {0}".format(err))

        print("Failed obtain date taken from " + filePath)
        return None
