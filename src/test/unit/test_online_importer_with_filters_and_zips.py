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

import unittest

from downloader.file_filter import BadFileFilterPartException
from downloader.online_importer import WrongDatabaseOptions
from downloader.other import empty_store
from test.objects import db_test_descr, store_test_descr, config_with_filter
from test.fake_online_importer import OnlineImporter
from test.zip_objects import cheats_folder_zip_desc, cheats_folder_tag_dictionary, cheats_folder_id, \
    cheats_folder_nes_file_path, cheats_folder_nes_folder_name, cheats_folder_sms_file_path, cheats_folder_sms_folder_name,\
    zipped_files_from_cheats_folder, unzipped_summary_json_from_cheats_folder, cheats_folder_name, \
    cheats_folder_files, cheats_folder_folders, cheats_folder_sms_file_descr, cheats_folder_sms_folder_descr, \
    cheats_folder_descr, cheats_folder_nes_file_descr, cheats_folder_nes_folder_descr


class TestOnlineImporterWithFiltersAndZips(unittest.TestCase):

    def test_download_zipped_cheats_folder___with_empty_store_and_negative_nes_filter___installs_filtered_nes_zip_data_and_only_sms_file(self):
        actual_store = self.download_zipped_cheats_folder(empty_store(), '!nes')

        self.assertEqual(store_with_filtered_nes_zip_data(), actual_store)
        self.assertOnlySmsFileIsInstalled()

    def test_download_zipped_cheats_folder___with_empty_store_and_negative_cheats_filter___installs_filtered_cheats_zip_data_but_no_files(self):
        actual_store = self.download_zipped_cheats_folder(empty_store(), '!cheats')

        self.assertEqual(store_with_filtered_cheats_zip_data(), actual_store)
        self.assertNoFiles()

    def test_download_zipped_cheats_folder___with_empty_store_and_filter_none___installs_zips_and_files(self):
        actual_store = self.download_zipped_cheats_folder(empty_store(), None)

        self.assertEqual(store_with_installed_files_and_zips_but_no_filtered_data(), actual_store)
        self.assertAllFilesAreInstalled()

    def test_download_zipped_cheats_folder___with_filtered_nes_zip_data_in_store_but_empty_filter___installs_files_and_removes_filtered_zip_data(self):
        actual_store = self.download_zipped_cheats_folder(store_with_filtered_nes_zip_data(), None)

        self.assertEqual(store_with_installed_files_and_zips_but_no_filtered_data(), actual_store)
        self.assertAllFilesAreInstalled()

    def test_download_zipped_cheats_folder___with_filtered_nes_zip_data_in_store_and_negative_cheats_filter___expands_zip_and_filtered_data_with_sms_and_installs_nothing(self):
        actual_store = self.download_zipped_cheats_folder(store_with_filtered_nes_zip_data(), '!cheats')

        self.assertEqual(store_with_filtered_cheats_zip_data(), actual_store)
        self.assertNoFiles()

    def test_download_zipped_cheats_folder___with_filtered_nes_zip_data_in_store_and_negative_nes_filter___keeps_zip_and_filtered_data_and_installs_only_sms_file(self):
        actual_store = self.download_zipped_cheats_folder(store_with_filtered_nes_zip_data(), '!nes')

        self.assertEqual(store_with_filtered_nes_zip_data(), actual_store)
        self.assertOnlySmsFileIsInstalled()

    def test_download_cheat_files_without_zip___with_filtered_nes_zip_data_in_store_and_negative_nes_filter___removes_filtered_zip_data_and_installs_only_sms_file(self):
        actual_store = self.download_cheat_files_without_zip(store_with_filtered_nes_zip_data(), '!nes')

        self.assertEqual(store_with_sms_file_only(), actual_store)
        self.assertOnlySmsFileIsInstalled()

    def test_download_cheat_files_without_zip___with_filtered_nes_zip_data_in_store_and_negative_cheats_filter___removes_filtered_zip_data_and_installs_nothing(self):
        actual_store = self.download_cheat_files_without_zip(store_with_filtered_nes_zip_data(), '!cheats')

        self.assertEqual(empty_store(), actual_store)
        self.assertNoFiles()

    def test_download_cheat_files_without_zip___with_filtered_nes_zip_data_in_store_but_filter_none___install_files_and_removes_filtered_zip_data(self):
        actual_store = self.download_cheat_files_without_zip(store_with_filtered_nes_zip_data(), None)

        self.assertEqual(store_with_installed_files_without_zips_and_no_filtered_data(), actual_store)
        self.assertAllFilesAreInstalled()

    def test_download_cheat_files_without_zip___with_filtered_nes_zip_data_in_store_but_filter_empty_string___install_files_and_removes_filtered_zip_data(self):
        self.assertRaises(WrongDatabaseOptions, lambda: self.download_cheat_files_without_zip(store_with_filtered_nes_zip_data(), ''))

    def download_zipped_cheats_folder(self, store, filter_value):
        config = config_with_filter(filter_value)
        config['zip_file_count_threshold'] = 0  # This will cause to unzip the contents

        self.sut = OnlineImporter(config=config)

        self.sut.add_db(db_test_descr(zips={
            cheats_folder_id: cheats_folder_zip_desc(zipped_files=zipped_files_from_cheats_folder(), unzipped_json=unzipped_summary_json_from_cheats_folder())
        }, tag_dictionary=cheats_folder_tag_dictionary()), store).download(False)

        return store

    def download_cheat_files_without_zip(self, store, filter_value):
        self.sut = OnlineImporter(config=config_with_filter(filter_value))
        self.sut.add_db(db_test_descr(
            files=cheats_folder_files(zip_id=False),
            folders=cheats_folder_folders(zip_id=False),
            tag_dictionary=cheats_folder_tag_dictionary()),
            store).download(False)
        return store

    def assertNoFiles(self):
        self.assertFalse(self.sut.file_system.is_folder(cheats_folder_name))
        self.assertFalse(self.sut.file_system.is_file(cheats_folder_nes_file_path))
        self.assertFalse(self.sut.file_system.is_folder(cheats_folder_nes_folder_name))
        self.assertFalse(self.sut.file_system.is_file(cheats_folder_sms_file_path))
        self.assertFalse(self.sut.file_system.is_folder(cheats_folder_sms_folder_name))

    def assertOnlyNesFileIsInstalled(self):
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_name))
        self.assertTrue(self.sut.file_system.is_file(cheats_folder_nes_file_path))
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_nes_folder_name))
        self.assertFalse(self.sut.file_system.is_file(cheats_folder_sms_file_path))
        self.assertFalse(self.sut.file_system.is_folder(cheats_folder_sms_folder_name))

    def assertOnlySmsFileIsInstalled(self):
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_name))
        self.assertFalse(self.sut.file_system.is_file(cheats_folder_nes_file_path))
        self.assertFalse(self.sut.file_system.is_folder(cheats_folder_nes_folder_name))
        self.assertTrue(self.sut.file_system.is_file(cheats_folder_sms_file_path))
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_sms_folder_name))

    def assertAllFilesAreInstalled(self):
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_name))
        self.assertTrue(self.sut.file_system.is_file(cheats_folder_nes_file_path))
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_nes_folder_name))
        self.assertTrue(self.sut.file_system.is_file(cheats_folder_sms_file_path))
        self.assertTrue(self.sut.file_system.is_folder(cheats_folder_sms_folder_name))

def store_with_filtered_nes_zip_data():
    store = store_test_descr(zips={
        cheats_folder_id: cheats_folder_zip_desc()
    }, files={
        cheats_folder_sms_file_path: cheats_folder_sms_file_descr(url=False)
    }, folders={
        cheats_folder_sms_folder_name: cheats_folder_sms_folder_descr(),
        cheats_folder_name: cheats_folder_descr(),
    })

    store['filtered_zip_data'] = {
        cheats_folder_id: {
            'files': {
                cheats_folder_nes_file_path: cheats_folder_nes_file_descr(url=False)
            },
            'folders': {cheats_folder_nes_folder_name: cheats_folder_nes_folder_descr()}
        }
    }

    return store

def store_with_filtered_cheats_zip_data():
    store = store_test_descr(zips={
        cheats_folder_id: cheats_folder_zip_desc()
    })

    store['filtered_zip_data'] = {
        cheats_folder_id: unzipped_summary_json_from_cheats_folder()
    }

    return store

def store_with_sms_file_only():
    return store_test_descr(files={
        cheats_folder_sms_file_path: cheats_folder_sms_file_descr(zip_id=False, tags=False)
    }, folders={
        cheats_folder_sms_folder_name: {},
        cheats_folder_name: {}
    })

def store_with_installed_files_and_zips_but_no_filtered_data():
    store = store_test_descr(zips={
        cheats_folder_id: cheats_folder_zip_desc()
    }, files=cheats_folder_files(url=False), folders=cheats_folder_folders())
    return store

def store_with_installed_files_without_zips_and_no_filtered_data():
    return store_test_descr(files=cheats_folder_files(zip_id=False, tags=False), folders=cheats_folder_folders(zip_id=False, tags=False))
