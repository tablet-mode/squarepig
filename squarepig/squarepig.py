#!/usr/bin/python3

"""Square Pig playlist mangler."""

import argparse
import sys
from os import path, makedirs
from re import match, sub
from shutil import copy

GUI = True

try:
    # Check if PyQt is installed.
    from PyQt4 import QtCore
except ImportError:
    GUI = False

# TODO: Cleanup function and variable names.
# TODO: Write some tests.
# TODO: Localisation
# TODO: Move Playlist class into separate library.


class Playlist:

    """Playlist class."""

    class UnknownPlaylistFormat(Exception):
        pass

    class UnsupportedPlaylistFormat(Exception):
        pass

    def __init__(self, playlist, musicdir=None):
        """Parse playlist."""
        files = []
        # Might throw FileNotFoundError.
        with open(path.expanduser(playlist)) as ofile:
            for line in ofile:
                files.append(line.rstrip())
        # Try to guess playlist format from file content.
        if match(r"^#EXTM3U", files[0]):
            # m3u playlist
            self._parse_m3u(files, musicdir)
        elif match(r".*(http://xspf.org/ns)", files[0]):
            # xspf playlist
            self._parse_xspf(files, musicdir)
        else:
            self._parse_by_extension(playlist, files, musicdir)

    def _parse_by_extension(self, filename, files, musicdir):
        """Try to get playlist format from file extension."""
        if match(r".*\.m3u", filename):
            self._parse_m3u(files, musicdir)
        elif match(r".*\.xspf", filename):
            self._parse_xspf(files, musicdir)
        else:
            raise self.UnknownPlaylistFormat

    def _parse_m3u(self, playlist, musicdir):
        """Get file paths from m3u playlist."""
        lines = []
        for line in playlist:
            if not match(r"^#", line):
                if line[0] != "/":
                    if musicdir:
                        line = musicdir + "/" + line
                lines.append(line)
        self.files = lines

    def _parse_xspf(self, playlist, musicdir):
        """Get file paths from xspf playlist."""
        # See if beautifulsoup is installed
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            msg = (
                "For XSPF support, the 'Beautiful Soup' python library is "
                "required.")
            raise self.UnsupportedPlaylistFormat(msg)

        lines = []
        soup = BeautifulSoup(''.join(playlist))
        for location in soup.findAll('location'):
            line = sub(r"file://", "", location.contents[0])
            if line[0] != "/":
                if musicdir:
                    line = musicdir + "/" + line
            lines.append(line)
        self.files = lines

    def get_files(self):
        """Return list of files in playlist."""
        return self.files


class SquarePig:

    """Main class."""

    def __init__(self):
        """Initialisation."""
        self.state = 'stopped'
        self.progress = (0, 0)
        self.error = None
        self.stop = False

    class CopyError(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return str(self.value)

    def copy_to(self, files, destination):
        """Copy files to destination."""
        if not path.isdir(path.expanduser(destination)):
            try:
                makedirs(destination)
            except PermissionError:
                msg = (
                    "Insufficient permissions to create DESTINATION "
                    "directory: {0}".format(destination))
                raise self.CopyError(msg)
            except FileNotFoundError:
                msg = "Invalid DESTINATION path: {0}".format(destination)
                self.state = 'stopped'
                self.error = msg
                raise self.CopyError(msg)
        file_count = len(files)
        max_zeroes = len(str(file_count)) - 1
        ten = 10
        self.state = 'running'
        for count, file in enumerate(files):
            if self.stop:
                self.stop = False
                self.state = 'stopped'
                return
            # TODO: Add numbering to last part of name
            zero_string = ""
            for zero in range(max_zeroes):
                zero_string += "0"
            padding = (zero_string + str(count))
            if count == (ten - 1):
                ten *= 10
                max_zeroes = int(max_zeroes) - 1
            target = destination + "/" + padding + "_" + path.basename(file)
            try:
                copy(file, target)
                self.progress = (count, file_count)
                #percent = int(count / file_count * 100)
                #stdout.write("                    \r")
                #stdout.write("Copying files: {0}%\r".format(percent))
            except PermissionError:
                msg = (
                    "Insufficient permissions to copy {file} to DESTINATION "
                    "directory {dest}".format(file=file, dest=destination))
                self.state = 'stopped'
                self.error = msg
                raise self.CopyError(msg)
            except FileNotFoundError:
                msg = "Unable to find files referenced in playlist"
                self.state = 'stopped'
                self.error = msg
                raise self.CopyError(msg)

        self.progress = (file_count, file_count)
        self.state = 'done'

    def get_state(self):
        """Get current state."""
        return self.state

    def get_progress(self):
        """Get progress information."""
        return self.progress

    def request_stop(self):
        """Tell thread to close."""
        self.stop = True


def gui():
    """GUI."""
    from qtpig import main as gui_main
    gui_main()


def main():
    """Run Square Pig."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--playlist', metavar='PLAYLIST', type=str,
        help='playlist file - supported formats: [ m3u, xspf ]')
    parser.add_argument(
        '-d', '--destination', metavar='DESTINATION', type=str,
        help='target directory')
    parser.add_argument(
        '-m', '--musicdir', metavar='MUSIC_DIR', type=str,
        help='prefix paths in playlist with MUSIC_DIR')
    args = parser.parse_args()

    arg_count = 0
    if args.destination:
        arg_count += 1
        if path.isfile(path.expanduser(args.destination)):
            parser.error("DESTINATION {0} is a file.".format(args.destination))
    if args.playlist:
        arg_count += 1
        playlist = args.playlist
    musicdir = None
    if args.musicdir:
        arg_count += 1
        musicdir = path.expanduser(args.musicdir)

    if arg_count == 0:
        if GUI:
            gui()
        else:
            parser.print_help()
    else:
        sargasso = SquarePig()
        try:
            playlist = Playlist(playlist, musicdir)
        except Playlist.UnknownPlaylistFormat:
            parser.error("unknown playlist format")
        except Playlist.UnsupportedPlaylistFormat as e:
            parser.error("unsupported playlist format: {0}\n".format(e))
        except FileNotFoundError:
            parser.error("unable to find '{0}'\n".format(playlist))
        try:
            sargasso.copy_to(playlist.get_files(), args.destination)
        except SquarePig.CopyError as e:
            sys.stderr.write(e + "\n")
            exit(1)


if __name__ == "__main__":
    main()