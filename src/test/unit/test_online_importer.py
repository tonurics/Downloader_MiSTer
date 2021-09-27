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
from downloader.config import default_config
from downloader.other import empty_store
from test.objects import db_test_being_empty_descr, file_boot_rom, boot_rom_descr, overwrite_file, file_mister_descr, file_a_descr, file_a_updated_descr, db_test_with_file, db_with_file, db_test_with_file_a_descr, db_with_folders, file_a, folder_a, file_MiSTer, file_MiSTer_old
from test.fakes import OnlineImporter


class TestOnlineImporter(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = OnlineImporter()

    def test_download_dbs_contents___with_trivial_db___does_nothing(self):
        sut = OnlineImporter()
        store = empty_store()

        sut.add_db(db_test_being_empty_descr(), store)
        sut.download_dbs_contents(False)

        self.assertReportsNothing(sut)
        self.assertEqual(store, empty_store())

    def test_download_dbs_contents___being_empty___does_nothing(self):
        sut = OnlineImporter()
        sut.download_dbs_contents(False)
        self.assertReportsNothing(sut)

    def test_download_dbs_contents___with_one_file___fills_store_with_that_file(self):
        sut = OnlineImporter()
        store = empty_store()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertEqual(store['files'][file_a], file_a_descr())
        self.assertHasFolderA(store)
        self.assertReports(sut, [file_a])
        self.assertTrue(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___with_existing_incorrect_file_but_correct_already_on_store___changes_nothing(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a({'hash': 'does_not_match'})
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertEqual(store['files'][file_a], file_a_descr())
        self.assertHasFolderA(store)
        self.assertReportsNothing(sut)
        self.assertEqual(sut.file_service.hash(file_a), 'does_not_match')

    def test_download_dbs_contents___with_existing_incorrect_file_also_on_store___downloads_the_correct_one(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a({'hash': 'does_not_match'})
        store = db_test_with_file(file_a, {'hash': 'does_not_match'})

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertEqual(store['files'][file_a], file_a_descr())
        self.assertHasFolderA(store)
        self.assertReports(sut, [file_a])
        self.assertEqual(sut.file_service.hash(file_a), file_a)

    def test_download_dbs_contents___with_non_existing_one_file_already_on_store___installs_file_regardless(self):
        sut = OnlineImporter()
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertEqual(store['files'][file_a], file_a_descr())
        self.assertHasFolderA(store)
        self.assertReports(sut, [file_a])
        self.assertTrue(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___with_one_failed_file___just_reports_error(self):
        sut = OnlineImporter()
        sut.downloader_test_data.errors_at(file_a)
        store = empty_store()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFiles(store)
        self.assertHasFolderA(store)
        self.assertReports(sut, [], errors=[file_a])
        self.assertFalse(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___with_mister___needs_reboot(self):
        sut = OnlineImporter()
        store = empty_store()
        sut.file_service.test_data.with_old_mister_binary()

        sut.add_db(db_test_with_file(file_MiSTer, file_mister_descr()), store)
        sut.download_dbs_contents(False)

        self.assertEqual(store['files'][file_MiSTer], file_mister_descr())
        self.assertEmptyFolders(store)
        self.assertReports(sut, [file_MiSTer], needs_reboot=True)
        self.assertTrue(sut.file_service.is_file(file_MiSTer))
        self.assertTrue(sut.file_service.is_file(file_MiSTer_old))

    def test_download_dbs_contents___with_file_on_stored_erroring___store_deletes_file(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_folders(['a'])
        sut.downloader_test_data.errors_at(file_a)
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_with_file(file_a, file_a_updated_descr()), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFiles(store)
        self.assertEmptyFolders(store)
        self.assertReports(sut, [], errors=[file_a])
        self.assertFalse(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___with_duplicated_file___just_accounts_for_the_first_added(self):
        sut = OnlineImporter()
        store = empty_store()

        sut.add_db(db_with_file('test', file_a, file_a_descr()), store)
        sut.add_db(db_with_file('bar', file_a, file_a_updated_descr()), store)
        sut.download_dbs_contents(False)

        self.assertEqual(store['files'][file_a], file_a_descr())
        self.assertEmptyFolders(store)
        self.assertReports(sut, [file_a])
        self.assertEqual(sut.file_service.hash(file_a), file_a_descr()['hash'])

    def test_download_dbs_contents___when_file_a_gets_removed___store_becomes_empty(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a()
        sut.file_service.test_data.with_folders(['a'])
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_being_empty_descr(), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFiles(store)
        self.assertEmptyFolders(store)
        self.assertReportsNothing(sut)
        self.assertFalse(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___when_file_is_already_there___does_nothing(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a()
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertHasFolderA(store)
        self.assertReportsNothing(sut)
        self.assertTrue(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___when_downloaded_file_is_missing___downloads_it_again(self):
        sut = OnlineImporter()
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertHasFolderA(store)
        self.assertReports(sut, [file_a])
        self.assertTrue(sut.file_service.is_file(file_a))

    def test_download_dbs_contents___when_no_check_downloaded_files_and_downloaded_file_is_missing___does_nothing(self):
        config = default_config()
        config['check_manually_deleted_files'] = False
        sut = OnlineImporter(config=config)
        store = db_test_with_file_a_descr()

        sut.add_db(db_test_with_file_a_descr(), store)
        sut.download_dbs_contents(False)

        self.assertHasFolderA(store)
        self.assertReportsNothing(sut)
        self.assertFalse(sut.file_service.is_file(file_a))

    def test_overwrite___when_boot_rom_present___should_not_overwrite_it(self):
        sut = OnlineImporter()
        store = empty_store()
        sut.file_service.test_data.with_file(file_boot_rom, {"hash": "something_else"})

        sut.add_db(db_test_with_file(file_boot_rom, boot_rom_descr()), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFolders(store)
        self.assertReportsNothing(sut)
        self.assertEqual(sut.file_service.hash(file_boot_rom), "something_else")

    def test_overwrite___when_boot_rom_present_but_with_different_case___should_not_overwrite_it(self):
        sut = OnlineImporter()
        store = empty_store()
        sut.file_service.test_data.with_file(file_boot_rom.upper(), {"hash": "something_else"})

        sut.add_db(db_test_with_file(file_boot_rom.lower(), boot_rom_descr()), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFolders(store)
        self.assertReportsNothing(sut)
        self.assertEqual(sut.file_service.hash(file_boot_rom.lower()), "something_else")
        self.assertNotEqual(sut.file_service.hash(file_boot_rom.lower()), boot_rom_descr()['hash'])

    def test_overwrite___when_overwrite_yes_file_a_is_present___should_overwrite_it(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a()
        store = empty_store()

        sut.add_db(db_test_with_file(file_a, overwrite_file(file_a_updated_descr(), True)), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFolders(store)
        self.assertReports(sut, [file_a])
        self.assertEqual(sut.file_service.hash(file_a), file_a_updated_descr()['hash'])
        self.assertNotEqual(sut.file_service.hash(file_a), file_a_descr()['hash'])

    def test_overwrite___when_overwrite_no_file_a_is_present___should_overwrite_it(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a()
        store = empty_store()

        sut.add_db(db_test_with_file(file_a, overwrite_file(file_a_updated_descr(), False)), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFolders(store)
        self.assertReportsNothing(sut)
        self.assertEqual(sut.file_service.hash(file_a), file_a_descr()['hash'])
        self.assertNotEqual(sut.file_service.hash(file_a), file_a_updated_descr()['hash'])

    def test_overwrite___when_file_a_without_overwrite_is_present___should_overwrite_it(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_file_a()
        store = empty_store()

        sut.add_db(db_test_with_file(file_a, file_a_updated_descr()), store)
        sut.download_dbs_contents(False)

        self.assertEmptyFolders(store)
        self.assertReports(sut, [file_a])
        self.assertEqual(sut.file_service.hash(file_a), file_a_updated_descr()['hash'])
        self.assertNotEqual(sut.file_service.hash(file_a), file_a_descr()['hash'])

    def test_deleted_folders___when_db_1_has_a_b_c_and_store_1_has_a_x_y___should_delete_b_c_and_store_x_y(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_folders(['a', 'b', 'c'])
        store1 = db_with_folders('db1', ['a', 'b', 'c'])

        sut.add_db(db_with_folders('db1', ['a', 'x', 'y']), store1)
        sut.download_dbs_contents(False)

        self.assertEqual(store1['folders'], ['a', 'x', 'y'])
        self.assertReportsNothing(sut)
        self.assertEqual(sut.file_service.folders(), ['a', 'x', 'y'])

    def test_deleted_folders___when_db_1_has_a_b_c_and_store_1_has_a_x___and_db_2_has_b_and_store_2_is_empty__and_db_3_is_empty_and_store_3_has_z___should_delete_c_z_and_store_x(self):
        sut = OnlineImporter()
        sut.file_service.test_data.with_folders(['a', 'b', 'c', 'z'])
        store1 = db_with_folders('db1', ['a', 'b', 'c'])
        store2 = db_with_folders('db2', [])
        store3 = db_with_folders('db3', ['z'])

        sut.add_db(db_with_folders('db1', ['a', 'x']), store1)
        sut.add_db(db_with_folders('db2', ['b']), store2)
        sut.add_db(db_with_folders('db3', []), store3)
        sut.download_dbs_contents(False)

        self.assertEqual(store1['folders'], ['a', 'x'])
        self.assertEqual(store2['folders'], ['b'])
        self.assertEqual(store3['folders'], [])
        self.assertReportsNothing(sut)
        self.assertEqual(sut.file_service.folders(), ['a', 'b', 'x'])

    def assertEmptyFolders(self, store):
        self.assertEqual(store['folders'], [])

    def assertHasFolderA(self, store):
        self.assertEqual(store['folders'], [folder_a])

    def assertEmptyFiles(self, store):
        self.assertEqual(store['files'], {})

    def assertReportsNothing(self, sut):
        self.assertReports(sut, [])

    def assertReports(self, sut, installed, errors=None, needs_reboot=False):
        if errors is None:
            errors = []
        if installed is None:
            installed = []
        self.assertEqual(sut.correctly_installed_files(), installed)
        self.assertEqual(sut.files_that_failed(), errors)
        self.assertEqual(sut.needs_reboot(), needs_reboot)
