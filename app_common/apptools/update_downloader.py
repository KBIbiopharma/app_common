""" Objects, utility and GUI to check for and download any available update for
the current version and user.

See downstream projects for the test suite.
"""
import re
import json
from time import sleep
from os.path import dirname, isdir, isfile, join
import os
from logging import getLogger
import getpass
from six import string_types, PY2

from pyface.api import error, information
from traits.api import Bool, Button, cached_property, Directory, \
    HasStrictTraits, Int, List, Property, Str, Tuple
from traitsui.api import Action, HGroup, Handler, Item, Label, VGroup, View

from app_updater.updater import initialize_local_egg_repo, LOCAL_EGG_REPO
from app_common.traitsui.common_traitsui_groups import make_window_title_group
from app_common.traitsui.label_with_html import LabelWithHyperlinks

if PY2:
    from urllib2 import urlopen
    from urlparse import urljoin
else:
    from urllib.request import urlopen
    from urllib.parse import urljoin

logger = getLogger(__name__)

RELEASE_LIST_FNAME = "release_list.json"

RELEASE_CONTENT_FNAME = "content_{}_{}.json"

RELEASE_CONTENT_RE_PATTERN = "content_(.+)_(.+).json"

ALL_USER_DESCRIPTION = "all"

MYCLOUD_DOWNLOAD_SUFFIX = "/download"

# Number of download attempts
NUM_ATTEMPTS = 3

# NUmber of seconds between subsequent download attempts
ATTEMPT_SLEEP = 3

NO_RELEASE = ""

YesButton = Action(name="Download", action="do_update",
                   visible_when="new_release_list")

NoButton = Action(name="Not Now", action="do_close",
                  visible_when="new_release_list")

CloseButton = Action(name="Close", action="do_close",
                     visible_when="not new_release_list")


class UpdateDownloaderHandler(Handler):
    def do_update(self, info):
        downloader = info.object
        if downloader.new_release_list:
            downloader.download_button = True

        info.ui.dispose()

    def do_close(self, info):
        info.ui.dispose()


class UpdateDownloader(HasStrictTraits):
    """ Base GUI tool to check if a new release has been made.

    It responsibilities are to query a URL for a list of available releases,
    collect the list of releases targeting the current implementation (version
    and user) and download the newest one

    To implement, subclass and implement the following attributes and methods:

        * egg_repo_url
        * current_version
        * local_updater_folder
        * initialize()

    TODO: convert the egg_repo_url to a list of URLs that can be checked.
    """
    #: URL to connect to to find new releases
    egg_repo_url = Str

    #: URL to the changelog online
    changelog_url = Str

    #: Application title
    app_title = Str

    #: Local folder to download eggs to
    local_egg_repo = Str(LOCAL_EGG_REPO)

    #: Folder for updater files
    local_updater_folder = Directory

    #: Current version and build running
    current_version = Tuple

    # Local file containing release data.
    release_data_file = Str

    #: Data about all releases made
    release_data = List

    #: Available releases for the version running
    new_release_list = Property(List, depends_on="release_data")

    #: Newest version and build released
    newest_release = Property(Str, depends_on="release_list")

    #: Version and build of the newest version possible to update to
    newest_release_msg = Property(Str, depends_on="newest_release")

    #: String to display the version currently running
    current_version_msg = Property(Str, depends_on="current_version")

    #: Check button
    check_button = Button("Check")

    #: Download button
    download_button = Button("Download newest release")

    #: Number of attempts to dowload software updates before giving up
    num_download_attempts = Int(NUM_ATTEMPTS)

    #: Window view class (customization possible by subclassing View)
    updater_view = View

    #: Help information about updating the version
    _help_str = Str

    #: Allow pop up dialogs? Turn off for testing.
    allow_dlg = Bool(True)

    #: Additional TraitsUI groups to display before the default update block
    adtl_top_view_groups = List

    #: Additional TraitsUI groups to display after the default update block
    adtl_bottom_view_groups = List

    #: View height
    view_height = Int

    #: View width
    view_width = Int(600)

    def traits_view(self):
        main_group = VGroup(
            make_window_title_group(title="Software Update"),
            Item("current_version_msg", label="Current version",
                 style="readonly"),
            # What to display when there is an update
            VGroup(
                HGroup(
                    Label("A new software update is available, do you want"
                          " to upgrade?"),
                ),
                Item("newest_release_msg", label="Available version",
                     style="readonly"),
                HGroup(
                    Item("_help_str", editor=LabelWithHyperlinks(),
                         style="readonly", show_label=False,
                         resizable=True),
                ),
                visible_when="new_release_list",
            ),
            # What to display when there is an update
            HGroup(
                Label("No new software update available: please check "
                      "again later."),
                visible_when="not new_release_list"
            ),
            show_border=True
        )

        groups = self.adtl_top_view_groups + [main_group] + \
            self.adtl_bottom_view_groups

        view = self.updater_view(
            VGroup(*groups),
            title="Software Upgrade for {}".format(self.app_title),
            buttons=[NoButton, YesButton, CloseButton],
            default_button=YesButton,
            handler=UpdateDownloaderHandler(),
            height=self.view_height, width=self.view_width
        )
        return view

    def __init__(self, **traits):
        # If providing current version as a string, convert to tuple form:
        if "current_version" in traits:
            if isinstance(traits["current_version"][0], string_types):
                version = version_str_to_version(traits["current_version"][0])
                traits["current_version"] = list(traits["current_version"])
                traits["current_version"][0] = version

        super(UpdateDownloader, self).__init__(**traits)
        self.initialize()

    def initialize(self):
        """ Initialize resources for downloader files.
        """
        pass

    def update_release_data_file(self):
        """ Download the latest release list.
        """
        release_file_url = urljoin(self.egg_repo_url, RELEASE_LIST_FNAME)
        tgt_file = join(self.local_updater_folder, RELEASE_LIST_FNAME)
        retrieve_file_from_url(release_file_url, tgt_file)
        self.release_data_file = tgt_file

    def download_newest_version(self):
        """ Try and download the newest available release.

        If all attempts fail, delete all downloaded files.
        """
        released = self.newest_release
        for attempt in range(self.num_download_attempts):
            try:
                download_version(released, egg_repo_url=self.egg_repo_url,
                                 local_egg_repo=self.local_egg_repo)
                msg = "Successfully downloaded version {} from online " \
                      "egg repo.".format(released)
                logger.debug(msg)
                return True
            except Exception as e:
                msg = "Failed to download version {} from online egg " \
                      "repo. Error was {}.".format(released, e)
                logger.warning(msg)
                sleep(ATTEMPT_SLEEP)

        msg = "Failed to download newest version ({}) to update to ({} " \
              "attempts).".format(released, self.num_download_attempts)
        logger.error(msg)
        try:
            delete_failed_download_files(released)
        except Exception as e:
            msg = "Failed to delete local files after failed " \
                  "release download. Error was {}.".format(e)
            logger.error(msg)

        return False

    def parse_release_file(self):
        """ Parse the release file to build the list of releases the current
        install can update to.
        """
        # Find all updates that this version can consider.
        release_descr_file_list = []
        curr_v, curr_b = self.current_version
        curr_v_str = ".".join([str(x) for x in curr_v])
        for data in self.release_data:
            version_match = (re.match(data["target_versions"], curr_v_str) and
                             re.match(data["target_builds"], str(curr_b)))

            user_match = self.get_user_match(data["target_users"])
            if version_match and user_match:
                release_descr_file_list += data["release_filenames"]

        msg = "Release list for current version: {}".format(
            release_descr_file_list)
        logger.debug(msg)
        return release_descr_file_list

    @staticmethod
    def get_release_version(release_filename):
        """ Extract the version string and the build number from release filename.

        Parameters
        ----------
        release_filename : str
            File name to parse, containing the version and build numbers it
            describes.

        Returns
        -------
        tuple
            Version and build number (integer), grouped in a tuple described by
            the release filename provided.
        """
        pattern = RELEASE_CONTENT_RE_PATTERN
        match = re.match(pattern, release_filename)
        if match is None:
            msg = "Filename provided ({}) doesn't follow the expected " \
                  "pattern {}.".format(release_filename, pattern)
            logger.exception(msg)
            raise ValueError(msg)

        version_str, b = match.groups()
        version = version_str_to_version(version_str)
        return tuple([el for el in version] + [int(b)])

    def get_user_match(self, user_description):
        """ Evaluate if the user description matches the current user.
        """
        if user_description == ALL_USER_DESCRIPTION:
            return True
        else:
            current_user = self.get_current_user()
            match = re.match(user_description, current_user)
            return match is not None

    @staticmethod
    def get_current_user():
        """ Collect an identification of the current user.

        Subclass to implement other strategies.
        """
        return getpass.getuser()

    # Traits listeners --------------------------------------------------------

    def _release_data_file_changed(self):
        self.release_data = json.load(open(self.release_data_file, "r"))

    def _check_button_fired(self):
        self.update_release_data_file()

    def _download_button_fired(self):
        success = self.download_newest_version()
        title = "Software Upgrade for {}".format(self.app_title)
        if success:
            msg = "Successfully downloaded release {}. It will be installed " \
                  "next time the application is restarted."
            msg = msg.format(self.newest_release_msg)
            logger.debug(msg)
            if self.allow_dlg:
                information(None, msg, title=title)
        else:
            msg = "Failed to install the newest version {}. Please report " \
                  "this issue (see the Help menu for instructions)."
            msg = msg.format(self.newest_release_msg)
            logger.debug(msg)
            if self.allow_dlg:
                error(None, msg, title=title)

    # Traits property getters/setters -----------------------------------------

    @cached_property
    def _get_new_release_list(self):
        """ Return the list of update content file which the current version
        is authorized to update to.
        """
        release_descr_file_list = self.parse_release_file()

        # Filter out the ones that are older than current version:
        if release_descr_file_list:
            new_releases = [release for release in release_descr_file_list
                            if self.release_newer_than_current(release)]
        else:
            new_releases = []

        return new_releases

    def release_newer_than_current(self, release):
        """ Returns whether provided release is newer than currently running
        version.
        """
        curr_v, curr_b = self.current_version
        release_version = self.get_release_version(release)
        # Tuple comparison involving the build number:
        newer = release_version > tuple([el for el in curr_v] + [curr_b])
        return newer

    @cached_property
    def _get_current_version_msg(self):
        version = self.current_version[0]
        version = version_to_version_str(version)
        build = self.current_version[1]
        return "{} (build: {})".format(version, build)

    @cached_property
    def _get_newest_release_msg(self):
        if self.new_release_list:
            release_version = self.get_release_version(self.newest_release)
            version = release_version[:-1]
            version = version_to_version_str(version)
            build = release_version[-1]
            return "{} (build: {})".format(version, build)
        else:
            return ""

    @cached_property
    def _get_newest_release(self):
        if self.new_release_list:
            return sorted(self.new_release_list)[-1]
        else:
            return NO_RELEASE

    # Traits initialization methods -------------------------------------------

    def __help_str_default(self):
        help_str = r'Not sure? Check the release descriptions <a ' \
                   r'href={}>here</a>.'.format(self.changelog_url)
        return help_str

    def _view_height_default(self):
        return 500


def version_str_to_version(version_str):
    """ Convert a string version to a tuple of integers.
    """
    curr_v = version_str.split(".")
    for i, element in enumerate(curr_v):
        try:
            curr_v[i] = int(element)
        except ValueError:
            pass

    return tuple(curr_v)


def version_to_version_str(version):
    """ Convert a version list/tuple to a string representation.
    """
    return ".".join([str(el) for el in version])


def download_version(release_content_fname, egg_repo_url="",
                     local_egg_repo=LOCAL_EGG_REPO):
    """ Download in to the local egg repo all eggs described in the release.

    TODO: add md5 checksums to avoid files partially downloaded.
    """
    initialize_local_egg_repo(local_egg_repo)

    release_desc_url = urljoin(egg_repo_url, release_content_fname)
    local_release_fname = join(local_egg_repo, release_content_fname)
    # Download the content file first so that we can revert the process:
    retrieve_file_from_url(release_desc_url, local_release_fname)

    # Now download the content of the release:
    with open(local_release_fname, "r") as f:
        egg_list = json.load(f)

    for egg_data in egg_list:
        egg_name = egg_data["egg_name"]
        egg_url = egg_data["url"]
        is_mycloud_url = "mycloud.kbibiopharma" in egg_url
        if is_mycloud_url and not egg_url.endswith(MYCLOUD_DOWNLOAD_SUFFIX):
            egg_url += MYCLOUD_DOWNLOAD_SUFFIX

        tgt_egg_file = join(local_egg_repo, egg_name)
        if not isfile(tgt_egg_file):
            retrieve_file_from_url(egg_url, tgt_egg_file)


def retrieve_file_from_url(url, target_file):
    """ Download the content of a URL if the URL's response is valid.
    """
    msg = "Downloading file from URL {}.".format(url)
    logger.debug(msg)
    try:
        resp = urlopen(url)
    except Exception as e:
        msg = "Failed to download file at URL {}. Error was {}.".format(url, e)
        logger.exception(msg)
        raise
    else:
        target_folder = dirname(target_file)
        if not isdir(target_folder):
            os.makedirs(target_folder)

        open(target_file, "wb").write(resp.read())


def delete_failed_download_files(content_fname, local_egg_repo=LOCAL_EGG_REPO):
    """ A download failed. Delete all files to avoid leaving partial releases
    locally.
    """
    local_release_fname = join(local_egg_repo, content_fname)
    # Download didn't start, or did finish correctly:
    if not isfile(local_release_fname):
        return

    with open(local_release_fname, "r") as f:
        egg_dict = json.load(f)

    for egg_name in egg_dict.keys():
        tgt_egg_file = join(local_egg_repo, egg_name)
        if isfile(tgt_egg_file):
            try:
                os.remove(tgt_egg_file)
            except Exception:
                # Not a big issue if a file is left behind
                pass

    os.remove(local_release_fname)
