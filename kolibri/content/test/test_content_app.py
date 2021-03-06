"""
To run this test, type this in command line <kolibri manage test -- kolibri.content>
"""
from __future__ import unicode_literals
import os
import shutil
import tempfile
from django.core.urlresolvers import reverse

from django.conf import settings
from django.db import connections, IntegrityError
from django.test.utils import override_settings

from kolibri.content import models as content
from kolibri.content import api

from rest_framework.test import APITestCase as TestCase

from rest_framework.test import APITestCase

@override_settings(
    CONTENT_COPY_DIR=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test_content_copy"
    )
)
class ContentMetadataTestCase(TestCase):
    """
    Testcase for content metadata methods
    """
    fixtures = ['channel_test.json', 'content_test.json']
    multi_db = True
    the_channel_id = 'content_test'
    connections.databases[the_channel_id] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        # Create files in the temporary directory
        self.temp_f_1 = open(os.path.join(self.test_dir, 'test_1.pdf'), 'wb')
        self.temp_f_2 = open(os.path.join(self.test_dir, 'test_2.mp4'), 'wb')
        # Write something to it
        self.temp_f_1.write(b'The owls are not what they seem')
        self.temp_f_2.write(b'The owl are not what they seem')

        # Reopen the file and check if what we read back is the same
        self.temp_f_1 = open(os.path.join(self.test_dir, 'test_1.pdf'), 'rb')
        self.temp_f_2 = open(os.path.join(self.test_dir, 'test_2.mp4'), 'rb')
        self.assertEqual(self.temp_f_1.read(), b'The owls are not what they seem')
        self.assertEqual(self.temp_f_2.read(), b'The owl are not what they seem')

    """Tests for content API methods"""
    def test_can_get_content_with_id(self):
        # pass content_id
        root_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root").content_id
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c1", "c2"])
        actual_output = api.immediate_children(channel_id=self.the_channel_id, content=str(root_id))
        self.assertEqual(set(expected_output), set(actual_output))

        # pass content_ids
        api.set_is_related(channel_id=self.the_channel_id, content1=str(expected_output[0].content_id), content2=str(root_id))

        # pass invalid type
        with self.assertRaises(TypeError):
            api.immediate_children(channel_id=self.the_channel_id, content=432)

    def test_update_content_copy(self):
        """
        test adding same content copies, and deleting content copy
        """
        # add same content copy twise, there should be no duplication
        fpath_1 = self.temp_f_1.name
        fm_1 = content.Format.objects.using(self.the_channel_id).get(format_size=102)
        fm_3 = content.Format.objects.using(self.the_channel_id).get(format_size=46)
        file_1 = content.File.objects.using(self.the_channel_id).get(format=fm_1)
        api.update_content_copy(file_1, fpath_1)
        file_3 = content.File.objects.using(self.the_channel_id).filter(format=fm_3)[1]
        api.update_content_copy(file_3, fpath_1)
        self.assertEqual(1, len(os.listdir(os.path.join(settings.CONTENT_COPY_DIR, '0', '9'))))

        # swap the content copy in file_3
        fpath_2 = self.temp_f_2.name
        self.assertEqual(file_3.extension, '.pdf')
        api.update_content_copy(file_3, fpath_2)
        self.assertEqual(file_3.extension, '.mp4')

        # because file_3 and file_2 all have reference pointing to this content copy,
        # erase the reference from file_2 won't delete the content copy
        fm_2 = content.Format.objects.using(self.the_channel_id).get(format_size=51)
        file_2 = content.File.objects.using(self.the_channel_id).get(format=fm_2)
        api.update_content_copy(file_2, fpath_2)
        self.assertTrue(file_2.content_copy)
        api.update_content_copy(file_2, None)
        self.assertFalse(file_2.content_copy)
        content_copy_path = os.path.join(settings.CONTENT_COPY_DIR, '3', '3', '335782204c8215e0061516c6b3b80271.mp4')
        self.assertTrue(os.path.isfile(content_copy_path))

        # all reference pointing to this content copy is gone,
        # the content copy should be deleted
        api.update_content_copy(file_3, None)
        self.assertFalse(os.path.isfile(content_copy_path))
        self.assertFalse(file_2.content_copy)
        self.assertFalse(file_2.checksum)

        # update None content copy on empty File object should be silent and have no effect
        api.update_content_copy(file_2, None)

        # test File __str__ method
        self.assertEqual(file_1.__str__(), '09293abba61d4fcfa4e3bd804bcaba43.pdf')

        # test MimeType __str__ method
        self.assertEqual(fm_1.mimetype.__str__(), 'video_high')

        # test for non File object exception
        with self.assertRaises(TypeError):
            api.update_content_copy(None, None)

    def test_get_content_with_id(self):
        # test for single content_id
        the_content_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root").content_id
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title="root")
        actual_output = api.get_content_with_id(self.the_channel_id, the_content_id)
        self.assertEqual(set(expected_output), set(actual_output))

        # test for a list of content_ids
        the_content_ids = [cm.content_id for cm in content.ContentMetadata.objects.using(self.the_channel_id).all() if cm.title in ["root", "c1", "c2c2"]]
        expected_output2 = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["root", "c1", "c2c2"])
        actual_output2 = api.get_content_with_id(self.the_channel_id, the_content_ids)
        self.assertEqual(set(expected_output2), set(actual_output2))

        # test ContentMetadata __str__ method
        self.assertEqual(actual_output[0].__str__(), 'root')

        # test License __str__ method
        self.assertEqual(actual_output[0].license.__str__(), 'WTFPL')

    def test_get_ancestor_topics(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2c3")
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["root", "c2"])
        actual_output = api.get_ancestor_topics(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_immediate_children(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c1", "c2"])
        actual_output = api.immediate_children(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_leaves(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c2c1", "c2c2", "c2c3"])
        actual_output = api.leaves(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_get_all_formats(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        expected_output = content.Format.objects.using(self.the_channel_id).filter(format_size=46)
        actual_output = api.get_all_formats(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_get_available_formats(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        expected_output = []
        actual_output = api.get_available_formats(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_get_possible_formats(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        expected_output = content.Format.objects.using(self.the_channel_id).filter(format_size__in=[51, 102])
        actual_output = api.get_possible_formats(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_get_files_for_quality(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        fm = content.Format.objects.using(self.the_channel_id).get(format_size=102)
        expected_output = content.File.objects.using(self.the_channel_id).filter(format=fm)
        actual_output = api.get_files_for_quality(channel_id=self.the_channel_id, content=p, format_quality="high")
        self.assertEqual(set(expected_output), set(actual_output))

    def test_get_missing_files(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        expected_output = content.File.objects.using(self.the_channel_id).filter(id__in=[1, 2])
        actual_output = api.get_missing_files(channel_id=self.the_channel_id, content=p)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_get_all_prerequisites(self):
        """
        test the directional characteristic of prerequisite relationship
        """
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        # if root is the prerequisite of c1
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["root"])
        actual_output = api.get_all_prerequisites(channel_id=self.the_channel_id, content=c1)
        self.assertEqual(set(expected_output), set(actual_output))
        # then c1 should not be the prerequisite of root
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c1"])
        actual_output = api.get_all_prerequisites(channel_id=self.the_channel_id, content=root)
        self.assertNotEqual(set(actual_output), set(expected_output))

    def test_get_all_related(self):
        """
        test the nondirectional characteristic of related relationship
        """
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        # if c1 is related to c2
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c2"])
        actual_output = api.get_all_related(channel_id=self.the_channel_id, content=c1)
        self.assertEqual(set(expected_output), set(actual_output))
        # then c2 should be related to c1
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c1"])
        actual_output = api.get_all_related(channel_id=self.the_channel_id, content=c2)
        self.assertEqual(set(expected_output), set(actual_output))

    def test_set_prerequisite(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        self.assertFalse(api.get_all_prerequisites(channel_id=self.the_channel_id, content=root))
        api.set_prerequisite(channel_id=self.the_channel_id, content1=c2, content2=root)
        self.assertTrue(api.get_all_prerequisites(channel_id=self.the_channel_id, content=root))

    def test_set_prerequisite_self_reference(self):
        c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        # test for self reference exception
        with self.assertRaises(IntegrityError):
            api.set_prerequisite(channel_id=self.the_channel_id, content1=c2, content2=c2)

    def test_set_prerequisite_uniqueness(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        api.set_prerequisite(channel_id=self.the_channel_id, content1=c2, content2=root)
        # test for uniqueness exception
        with self.assertRaises(IntegrityError):
            api.set_prerequisite(channel_id=self.the_channel_id, content1=c2, content2=root)

    def test_set_prerequisite_immediate_cyclic(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        api.set_prerequisite(channel_id=self.the_channel_id, content1=c2, content2=root)
        # test for immediate cyclic exception
        with self.assertRaises(IntegrityError):
            api.set_prerequisite(channel_id=self.the_channel_id, content1=root, content2=c2)

    # <the exception hasn't been implemented yet, may add in the future>
    # def test_set_prerequisite_distant_cyclic(self):
    #     root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
    #     c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
    #     api.set_prerequisite(channel_id=self.the_channel_id, content1=c2, content2=root)
    #     # test for distant cyclic exception
    #     c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
    #     with self.assertRaises(Exception):
    #         api.set_prerequisite(channel_id=self.the_channel_id, content1=c1, content2=c2)

    def test_set_is_related(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        self.assertFalse(root in api.get_all_related(channel_id=self.the_channel_id, content=c1))
        api.set_is_related(channel_id=self.the_channel_id, content1=c1, content2=root)
        self.assertTrue(root in api.get_all_related(channel_id=self.the_channel_id, content=c1))

    def test_set_is_related_self_reference(self):
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        # test for self reference exception
        with self.assertRaises(IntegrityError):
            api.set_is_related(channel_id=self.the_channel_id, content1=c1, content2=c1)

    def test_set_is_related_uniqueness(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        api.set_is_related(channel_id=self.the_channel_id, content1=c1, content2=root)
        # test for uniqueness exception
        with self.assertRaises(IntegrityError):
            api.set_is_related(channel_id=self.the_channel_id, content1=c1, content2=root)

    def test_set_is_related_immediate_cyclic(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        api.set_is_related(channel_id=self.the_channel_id, content1=c1, content2=root)
        # test for silently canceling save on immediate cyclic related_relationship
        try:
            api.set_is_related(channel_id=self.the_channel_id, content1=root, content2=c1)
        except:
            self.assertTrue(False)

    def test_children_of_kind(self):
        p = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        expected_output = content.ContentMetadata.objects.using(self.the_channel_id).filter(title__in=["c2", "c2c2", "c2c3"])
        actual_output = api.children_of_kind(channel_id=self.the_channel_id, content=p, kind="topic")
        self.assertEqual(set(expected_output), set(actual_output))

    @classmethod
    def tearDownClass(self):
        """
        clean up files/folders created during the test
        """
        try:
            shutil.rmtree(settings.CONTENT_COPY_DIR)
            shutil.rmtree(self.test_dir)
        except:
            pass


@override_settings(
    CONTENT_COPY_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/test_content_copy"
)
class ContentMetadataAPITestCase(APITestCase):
    """
    Testcase for content API methods
    """
    fixtures = ['channel_test.json', 'content_test.json']
    multi_db = True
    the_channel_id = 'content_test'
    connections.databases[the_channel_id] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        # Create file in the temporary directory
        self.temp_f_1 = open(os.path.join(self.test_dir, 'test_1.pdf'), 'w')
        # Write something to it
        self.temp_f_1.write('The owls are not what they seem')

    def _reverse_channel_url(self, pattern_name, extra_kwargs):
        """Helper method to reverse a URL using the current channel ID"""
        kwargs = {"channelmetadata_channel_id": self.the_channel_id}
        kwargs.update(extra_kwargs)
        return reverse(pattern_name, kwargs=kwargs)

    def test_ancestor_topics_endpoint(self):
        c1_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-ancestor-topics", {"content_id": c1_id}))
        self.assertEqual(response.data[0]['title'], 'root')

    def test_immediate_children_endpoint(self):
        root_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-immediate-children", {"content_id": root_id}))
        self.assertEqual(response.data[0]['title'], 'c1')
        self.assertEqual(response.data[1]['title'], 'c2')

    def test_leaves_endpoint(self):
        root_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-leaves", {"content_id": root_id}))
        self.assertEqual(response.data[0]['title'], 'c1')
        self.assertEqual(response.data[1]['title'], 'c2c1')
        self.assertEqual(response.data[2]['title'], 'c2c2')
        self.assertEqual(response.data[3]['title'], 'c2c3')

    def test_all_prerequisites_endpoint(self):
        c1_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-all-prerequisites", {"content_id": c1_id}))
        self.assertEqual(response.data[0]['title'], 'root')

    def test_all_related_endpoint(self):
        c1_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-all-related", {"content_id": c1_id}))
        self.assertEqual(response.data[0]['title'], 'c2')

    def test_all_formats_endpoint(self):
        c2_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-all-formats", {"content_id": c2_id}))
        self.assertEqual(response.data[0]['format_size'], 46)

    def test_available_formats_endpoint(self):
        c2_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-available-formats", {"content_id": c2_id}))
        self.assertEqual(len(response.data), 0)

    def test_possible_formats_endpoint(self):
        c1_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-possible-formats", {"content_id": c1_id}))
        self.assertEqual(response.data[0]['format_size'], 102)
        self.assertEqual(response.data[1]['format_size'], 51)

    def test_missing_files_endpoint(self):
        c1_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata-missing-files", {"content_id": c1_id}))
        expected_output = content.File.objects.using(self.the_channel_id).filter(id__in=[1, 2])
        self.assertEqual(response.data[0]['format'], expected_output[0].format.id)
        self.assertEqual(response.data[1]['format'], expected_output[1].format.id)

    def test_files_for_quality_endpoint(self):
        c1_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata_files_for_quality", {"content_id": c1_id, "quality": "high"}))
        fm = content.Format.objects.using(self.the_channel_id).get(format_size=102)
        self.assertEqual(response.data[0]['format'], fm.id)

    def test_set_prerequisite_endpoint(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c2 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c2")
        self.assertFalse(api.get_all_prerequisites(channel_id=self.the_channel_id, content=root))
        self.client.put(self._reverse_channel_url("contentmetadata_set_prerequisite", {"content_id": c2.content_id, "prerequisite": root.content_id}))
        self.assertTrue(api.get_all_prerequisites(channel_id=self.the_channel_id, content=root))

    def test_set_is_related_endpoint(self):
        root = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root")
        c1 = content.ContentMetadata.objects.using(self.the_channel_id).get(title="c1")
        self.assertFalse(root in api.get_all_related(channel_id=self.the_channel_id, content=c1))
        self.client.put(self._reverse_channel_url("contentmetadata_set_is_related", {"content_id": c1.content_id, "related": root.content_id}))
        self.assertTrue(root in api.get_all_related(channel_id=self.the_channel_id, content=c1))

    def test_children_of_kind_endpoint(self):
        root_id = content.ContentMetadata.objects.using(self.the_channel_id).get(title="root").content_id
        response = self.client.get(self._reverse_channel_url("contentmetadata_children_of_kind", {"content_id": root_id, "kind": "topic"}))
        cn_titles = [k['title'] for k in response.data]
        self.assertEqual(cn_titles[0], 'c2')
        self.assertEqual(cn_titles[1], 'c2c2')
        self.assertEqual(cn_titles[2], 'c2c3')

    def test_update_content_copy_endpoint(self):
        # add same content copy twice, there should be no duplication
        fpath_1 = self.temp_f_1.name
        fm_1 = content.Format.objects.using(self.the_channel_id).get(format_size=102)
        fm_3 = content.Format.objects.using(self.the_channel_id).get(format_size=46)
        file_1 = content.File.objects.using(self.the_channel_id).get(format=fm_1)
        self.client.put(self._reverse_channel_url("file_update_content_copy", {"pk": file_1.pk, "content_copy": fpath_1}))
        file_3 = content.File.objects.using(self.the_channel_id).filter(format=fm_3)[1]
        self.client.put(self._reverse_channel_url("file_update_content_copy", {"pk": file_3.pk, "content_copy": fpath_1}))
        self.assertEqual(1, len(os.listdir(os.path.join(settings.CONTENT_COPY_DIR, 'd', '4'))))

    @classmethod
    def tearDownClass(self):
        """
        clean up files/folders created during the test
        """
        try:
            shutil.rmtree(settings.CONTENT_COPY_DIR)
            shutil.rmtree(self.test_dir)
        except:
            pass
