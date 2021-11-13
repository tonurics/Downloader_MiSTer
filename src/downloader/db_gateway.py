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

from pathlib import Path
from itertools import chain


class DbGateway:
    def __init__(self, file_system, file_downloader_factory, logger):
        self._file_system = file_system
        self._logger = logger
        self._file_downloader_factory = file_downloader_factory

    def fetch_all(self, descriptions):

        descriptions_by_file, local_files, remote_files = self._categorize_files_on_db_url(descriptions)

        downloaded_files, download_errors = self._download_files(remote_files)

        files_by_section = {descriptions_by_file[file]['section']: file for file in chain(downloaded_files, local_files)}

        dbs, db_errors = self._read_dbs(descriptions, files_by_section)

        self._cleanup_temp_files(descriptions_by_file)

        return dbs, db_errors + self._identify_download_errors(download_errors, descriptions_by_file)

    def _categorize_files_on_db_url(self, descriptions):
        descriptions_by_file = {}
        local_files = []
        remote_files = []

        for section, description in descriptions.items():
            db_url = description['db_url']
            if not db_url.startswith("http"):
                if not db_url.startswith("/"):
                    db_url = self._file_system.resolve(db_url)

                self._logger.debug('Loading db from local path: %s' % db_url)
                descriptions_by_file[db_url] = description
                local_files.append(db_url)
            else:
                temp = self._file_system.temp_file()
                descriptions_by_file[temp] = description
                description[temp_marker] = True
                self._logger.debug('Loading db from url: %s' % db_url)
                remote_files.append((db_url, temp))

        return descriptions_by_file, local_files, remote_files

    def _download_files(self, remote_files):
        file_downloader = self._file_downloader_factory.create(parallel_update=True, silent=True, hash_check=False)

        for db_url, temp in remote_files:
            file_downloader.queue_file({"url": db_url, "hash": "ignore", "size": 0}, temp)

        file_downloader.download_files(False)

        return file_downloader.correctly_downloaded_files(), file_downloader.errors()

    def _read_dbs(self, descriptions, files_by_section):
        dbs = []
        errors = []
        for section, description in descriptions.items():
            if section in files_by_section:
                try:
                    db = self._file_system.load_db_from_file(files_by_section[section], Path(description['db_url']).suffix.lower())
                    dbs.append((section, db))
                except Exception as e:
                    self._logger.debug(e)
                    self._logger.print('Could not load json from "%s"' % description['db_url'])
                    errors.append(description['db_url'])

        return dbs, errors

    def _cleanup_temp_files(self, descriptions_by_file):
        for file, description in descriptions_by_file.items():
            if temp_marker in description:
                self._file_system.unlink(file)

    def _identify_download_errors(self, download_errors, descriptions_by_file):
        errors = [descriptions_by_file[file]['db_url'] for file in download_errors]

        for db_url in errors:
            self._logger.print('Could not download file from db_url: "%s"' % db_url)

        return errors


temp_marker = 'temp'
