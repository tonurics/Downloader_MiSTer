# Copyright (c) 2021 José Manuel Barroso Galindo <theypsilon@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# You can download the latest version of this tool from:
# https://github.com/MiSTer-devel/Downloader_MiSTer

import os
import hashlib
import shutil
import json
import subprocess
import tempfile
import re
from pathlib import Path
from downloader.config import AllowDelete
from downloader.other import ClosableValue


class FileSystem:
    def __init__(self, config, logger):
        self._config = config
        self._logger = logger
        self._system_paths = set()
        self._unique_temp_filenames = set()
        self._unique_temp_filenames.add(None)

    def temp_file(self):
        return tempfile.NamedTemporaryFile(prefix='temp_file')

    def unique_temp_filename(self):
        name = None
        while name in self._unique_temp_filenames:
            name = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
        self._unique_temp_filenames.add(name)
        return ClosableValue(name, lambda: self._unique_temp_filenames.remove(name))

    def resolve(self, path):
        return str(Path(path).resolve())

    def add_system_path(self, path):
        self._system_paths.add(path)

    def is_file(self, path):
        return os.path.isfile(self._path(path))

    def is_folder(self, path):
        return os.path.isdir(self._path(path))

    def read_file_contents(self, path):
        with open(self._path(path), 'r') as f:
            return f.read()

    def write_file_contents(self, path, content):
        with open(self._path(path), 'w') as f:
            return f.write(content)

    def touch(self, path):
        return Path(self._path(path)).touch()

    def move(self, source, target):
        self._makedirs(str(Path(self._path(target)).parent))
        os.replace(self._path(source), self._path(target))

    def copy(self, source, target):
        return shutil.copyfile(self._path(source), self._path(target))

    def hash(self, path):
        return hash_file(self._path(path))

    def make_dirs(self, path):
        return self._makedirs(self._path(path))

    def make_dirs_parent(self, path):
        return self._makedirs(str(Path(self._path(path)).parent))

    def _makedirs(self, target):
        try:
            os.makedirs(target, exist_ok=True)
        except FileExistsError as e:
            if e.errno == 17:
                return
            raise e

    def folder_has_items(self, path):
        result = False
        for _ in os.scandir(self._path(path)):
            result = True
        return result

    def folders(self):
        raise Exception('folders Not implemented')

    def remove_folder(self, path):
        if self._config['allow_delete'] != AllowDelete.ALL:
            return

        self._logger.print('Deleting empty folder %s' % path)
        os.rmdir(self._path(path))

    def download_target_path(self, path):
        return self._path(path)

    def unlink(self, path):
        verbose = not path.startswith('/tmp/')
        if self._config['allow_delete'] != AllowDelete.ALL:
            if self._config['allow_delete'] == AllowDelete.OLD_RBF and path[-4:].lower() == ".rbf":
                return self._unlink(path, verbose)

            return True

        return self._unlink(path, verbose)

    def delete_previous(self, file):
        if self._config['allow_delete'] != AllowDelete.ALL:
            return True

        path = Path(self._path(file))
        if not self.is_folder(str(path.parent)):
            return

        regex = re.compile("^(.+_)[0-9]{8}([.][a-zA-Z0-9]+)$", )
        m = regex.match(path.name)
        if m is None:
            return

        g = m.groups()
        if g is None:
            return

        start = g[0].lower()
        ext = g[1].lower()

        deleted = False
        for child in path.parent.iterdir():
            name = child.name.lower()
            if name.startswith(start) and name.endswith(ext) and regex.match(name):
                child.unlink()
                deleted = True

        if deleted:
            self._logger.print('Deleted previous "%s"* files.' % start)

    def load_dict_from_file(self, path, suffix=None):
        path = self._path(path)
        if suffix is None:
            suffix = Path(path).suffix.lower()
        if suffix == '.json':
            return _load_json(path)
        elif suffix == '.zip':
            return _load_json_from_zip(path)
        else:
            raise Exception('File type "%s" not supported' % suffix)

    def save_json_on_zip(self, db, path):
        json_name = Path(path).stem
        json_path = '/tmp/%s' % json_name
        with open(json_path, 'w') as f:
            json.dump(db, f)

        zip_path = Path(self._path(path)).absolute()

        _run_successfully('cd /tmp/ && zip -qr %s %s' % (zip_path, json_name), self._logger)

        self._unlink(json_path, False)

    def unzip_contents(self, file, path):
        result = subprocess.run(['unzip', '-q', '-o', self._path(file), '-d', self._path(path)], shell=False, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            raise Exception("Could not unzip %s: %s" % (file, result.returncode))
        self._unlink(self._path(file), False)

    def _unlink(self, path, verbose):
        if verbose:
            self._logger.print('Removing %s' % path)
        try:
            Path(self._path(path)).unlink()
            return True
        except FileNotFoundError as _:
            return False

    def _path(self, path):
        if os.name == 'nt' and path.startswith('C:\\'):
            return path

        if path[0] == '/':
            return path

        base_path = self._config['base_system_path'] if path in self._system_paths else self._config['base_path']

        return '%s/%s' % (base_path, path)


def hash_file(path):
    with open(path, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
        return file_hash.hexdigest()


def _load_json_from_zip(path):
    json_str = _run_stdout("unzip -p %s" % path)
    return json.loads(json_str)


def _load_json(file_path):
    with open(file_path, "r") as f:
        return json.loads(f.read())


def _run_successfully(command, logger):
    result = subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    stdout = result.stdout.decode()
    stderr = result.stderr.decode()
    if stdout.strip():
        logger.print(stdout)

    if stderr.strip():
        logger.print(stderr)

    if result.returncode != 0:
        raise Exception("subprocess.run %s Return Code was '%d'" % (command, result.returncode))


def _run_stdout(command):
    result = subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception("subprocess.run %s Return Code was '%d'" % (command, result.returncode)
                        + '\n' + result.stdout.decode() + '\n' + result.stderr.decode())

    return result.stdout.decode()
