""" License manager module. Define a license key and a license manager classes.
"""
from __future__ import print_function

import datetime
import hashlib
from os.path import isfile, join
import logging
from six import PY3
from six import string_types

from traits.api import Any, Bool, Date, HasStrictTraits, Instance, List, \
    on_trait_change, Property, Str
from traitsui.api import Item, Label, OKCancelButtons, VGroup, View
from pyface.api import error

from app_common.traitsui.common_traitsui_groups import make_window_title_group

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y%m%d"

VALIDATION_ERROR_MSG = ("The license key that was found is invalid. Please "
                        "contact your software provider.")


class LicenseKey(HasStrictTraits):
    """ Wrapper for a license key capable of validating itself.
    """
    #: License key
    key = Str

    #: Validity state
    is_valid_format = Property(Bool, depends_on="key, username")

    #: Username of the user
    username = Str

    #: Email users should contact if they have an issue or need a license
    support_email = Str

    #: Custom View class if any, to customize it (icon, size, ...)
    view_klass = Any

    def default_traits_view(self):
        instructions = "Please (re)enter your email address, and license key."\
                       " If you don't have one, please contact your\n" \
                       "administrator or software provider at <{}>."
        instructions = instructions.format(self.support_email)
        view = self.view_klass(
            VGroup(
                make_window_title_group("Enter license info"),
                VGroup(
                    Label(instructions),
                ),
                Item("username", label="User Email", width=500),
                Item("key", label="License Key", width=500),
            ),
            buttons=OKCancelButtons, resizable=True, width=600,
            title="Please specify a valid license key"
        )
        return view

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _get_is_valid_format(self):
        return self.validate_string_format() and self.username != ""

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def validate_string_format(self):
        """ A valid key format is a salted hash of 32 characters, and then 3
        dates following the DATE_FORMAT (8 characters). See the license manager
        class for the validation of the content.
        """
        key_elements = self.key.split(":")
        if [len(e) for e in key_elements] != [32, 8, 8, 8]:
            msg = "The key elements don't have the expected structure."
            logger.error(msg)
            return False

        for i in range(1, 4):
            try:
                datetime.datetime.strptime(key_elements[i], DATE_FORMAT)
            except ValueError as e:
                msg = ("Valid to convert the element {} to the expected date "
                       "format. Error was {}.".format(i, e))
                logger.warning(msg)
                return False

        return True

    def _view_klass_default(self):
        return View


class LicenseManager(HasStrictTraits):
    """ License manager for Reveal Chromatography product.

    The license key to validate is stored in a file in the default application
    folder and is expected to contain any number of comments at the top marked
    by a # symbol and then the key, assumed to be the first line that is not a
    comment.

    It is expected that license managers will typically be created with all
    default arguments to look for the license file in the default location. It
    is also possible to create a manager around a provided a license key passed
    at creation. It is also possible to create licenseManager instances around
    other license files that are not in the default location.
    """
    #: Name of the license file
    file_name = Str

    #: Directory to search for the license file_name
    license_folder = Str

    #: Full license file path
    license_file = Property(Str)

    #: Name of the file where the username is stored
    auth_filename = Str

    #: Path to the authentication file
    auth_filepath = Property(Str)

    #: Current date
    current_date = Date

    #: License string/key
    license_key = Instance(LicenseKey)

    #: License string components
    license_strings = Property(List, depends_on='license_key')

    #: Date the application was last used
    last_date = Date

    #: Date after wich the license is valid
    start_date = Date

    #: Date before which the license is valid
    stop_date = Date

    #: User name or email of the user the license is for
    username = Str

    #: Secret salt used in the hash function
    salt = Str

    #: Alternate secret salt used in the hash function
    alt_salt = Str

    #: Email users should contact if they have an issue or need a license
    support_email = Str

    #: Custom View class if any, to customize it (icon, size, ...)
    view_klass = Any

    def __init__(self, key=None, **traits):
        if key is not None:
            license_key = LicenseKey(key=key)
            traits["license_key"] = license_key

        for date in ["start_date", "stop_date", "last_date"]:
            if traits.get(date, "") and isinstance(traits[date], string_types):
                traits[date] = datetime.datetime.strptime(traits[date],
                                                          DATE_FORMAT)

        super(LicenseManager, self).__init__(**traits)

        if not self.username:
            self.read_username()

        self.license_key.username = self.username
        self.license_key.support_email = self.support_email
        self.license_key.view_klass = self.view_klass

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def validate_license_key(self, salt="default"):
        """ Parse license file, extract key, and returns whether it's valid.

        If the key found is valid and if the current date is different from the
        last use date, the license file's last use date is re-generated. Also
        make sure there is an authentication file and a license file after this
        process so the application does't keep asking for the license info.
        """
        if not self.license_key.key:
            self._parse_license_file()

        valid = self.is_valid(salt=salt)
        if valid:
            if self.current_date.date() > self.last_date.date():
                msg = "Writing new valid license key to file {}."
                logger.debug(msg.format(self.license_file))
                self.regenerate_license()
            else:
                self.overwrite_license()

            self.write_username()

        return valid

    def invalidate_current_license(self):
        """ Erase current license key (for example because it isn't valid).
        """
        self.overwrite_license(license_key="")

    def generate_key(self, last_use_date, salt="default"):
        """ Generate a license key (hash + 3 dates) for the provided last use
        date and the current instance's start and stop dates.
        """
        salted_hash = self.generate_hash(last_use_date, salt=salt)
        return ':'.join([salted_hash, self.start_date.strftime(DATE_FORMAT),
                         last_use_date.strftime(DATE_FORMAT),
                         self.stop_date.strftime(DATE_FORMAT)])

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def is_valid(self, salt="default"):
        """ Check that the license key is valid.

        A key is valid if all the following is True:
            1. the key is correctly formatted, as defined by
            LicenseString.validate_string_format
            2. the salted hash part of the key is identical to the one
            generated from the username and dates found in the key.
            3. the current date is after the last use date.
            4. the current date is before the expiration date

        Parameters
        ----------
        salt : str [OPTIONAL, default='default']
            Which hash salt to test against? Should be either 'default' or
            'alt' to use the regular hash salt, or the alternative one
            `alt_salt`.
        """
        if not self.license_key.is_valid_format:
            valid_format = False
            hash_match_check = False
            key_expired_check = False
            key_current_time_check1 = False
            key_current_time_check2 = False
        else:
            valid_format = True
            hash_match_check = self._hash_match_check(salt=salt)
            key_expired_check = self._key_expired_check()
            key_current_time_check1 = self._key_current_time_after_last_check()
            key_current_time_check2 = \
                self._key_current_time_after_start_check()

        valid = (valid_format and hash_match_check and key_expired_check and
                 key_current_time_check1 and key_current_time_check2)
        if valid:
            msg = "Validated license key. Results are: {}, {}, {}, {}, {}"
            msg = msg.format(valid_format, hash_match_check, key_expired_check,
                             key_current_time_check1, key_current_time_check2)
        else:
            # Print the key in the open only when it fails to simplify
            # troubleshooting
            msg = "Did NOT validate key {} (username {}). Results are: {}, " \
                  "{}, {}, {}, {}"
            msg = msg.format(self.license_key.key, self.username, valid_format,
                             hash_match_check, key_expired_check,
                             key_current_time_check1, key_current_time_check2)
        logger.info(msg)
        return valid

    def read_username(self):
        """ Read (and return) username from current user config.
        """
        if not isfile(self.auth_filepath):
            msg = "No authentication file found. Expected {}."
            msg = msg.format(self.auth_filepath)
            logger.warning(msg)
            self.username = ""
        else:
            with open(self.auth_filepath) as f:
                self.username = f.read().strip()

        return self.username

    def write_username(self, overwrite=""):
        """ Write username from current user to file.

        Parameters
        ----------
        overwrite : str [OPTIONAL]
            Username to write and set. If not provided, current username is
            written to file.
        """
        if overwrite:
            self.username = overwrite

        with open(self.auth_filepath, "w") as f:
            f.write(self.username.strip() + "\n")

    def generate_hash(self, last_use_date, salt="default"):
        """ Generate hash for the combination of username and dates requested.

        Parameters
        ----------
        last_use_date : datetime.datetime
            Datetime of the last time the software was used since it is part of
            the license key.

        salt : str [OPTIONAL, default='default']
            Which hash salt to test against? Should be either 'default' or
            'alt' to use the regular hash salt, or the alternative one
            `alt_salt`.
        """
        hashed_string = ':'.join([self.start_date.strftime(DATE_FORMAT),
                                  last_use_date.strftime(DATE_FORMAT),
                                  self.stop_date.strftime(DATE_FORMAT)])
        if salt == "default":
            hashed_string = self.salt + hashed_string + self.username
        elif salt == "alt":
            if not self.alt_salt:
                msg = "Not alternate salt provided."
                logger.exception(msg)
                raise ValueError(msg)

            hashed_string = self.alt_salt + hashed_string + self.username

        if PY3:
            hashed_string = hashed_string.encode("utf-8")

        salted_hash = hashlib.md5(hashed_string).hexdigest()
        return salted_hash

    def regenerate_license(self):
        """ Update key to use current date as last used date.
        """
        license_key = self.generate_key(self.current_date)
        self.overwrite_license(license_key=license_key)

    def overwrite_license(self, license_key=None):
        """ Overwrite and store key into license file.
        """
        if license_key:
            self.license_key.key = license_key
        else:
            license_key = self.license_key.key

        with open(self.license_file, 'w') as license_file:
            license_file.write("###### DO NOT MODIFY THIS FILE ######\n")
            license_file.write(license_key)
            license_file.write("\n")

    def _parse_license_file(self):
        """ Update license_key's key attribute from the license file content.
        """
        if isfile(self.license_file):
            msg = "Loading license key from {} and username from {}"
            msg = msg.format(self.license_file, self.auth_filepath)
            logger.debug(msg)
            with open(self.license_file, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    else:
                        self.license_key.key = line.strip()
        else:
            msg = "License file {} not found.".format(self.license_file)
            logger.debug(msg)

    def prompt_for_license_info(self):
        """ Bring up UI to allow users to enter license information.

        Returns whether entries were valid.
        """
        msg = "Proposing to the user to enter new license info..."
        logger.debug(msg)
        self.license_key.configure_traits()
        if not self.license_key.is_valid_format:
            return False
        else:
            self.username = self.license_key.username
            return bool(self.username)

    def _hash_match_check(self, salt="default"):
        """ Check that the hash part of the key matches what is expected from
        the dates.

        Parameters
        ----------
        salt : str [OPTIONAL, default='default']
            Which hash salt to test against? Should be either 'default' or
            'alt' to use the regular hash salt, or the alternative one
            `alt_salt`.
        """
        file_hash = self.license_strings[0]
        last_date_hash = self.generate_hash(self.last_date, salt=salt)
        return file_hash == last_date_hash

    def _key_expired_check(self):
        return self.current_date <= self.stop_date

    def _key_current_time_after_last_check(self):
        return self.current_date >= self.last_date

    def _key_current_time_after_start_check(self):
        return self.current_date >= self.start_date

    # Initial values ----------------------------------------------------------

    def _current_date_default(self):
        return datetime.datetime.now()

    def _license_key_default(self):
        return LicenseKey(username=self.username)

    # Property getters and setters --------------------------------------------

    def _get_license_file(self):
        return join(self.license_folder, self.file_name)

    def _get_auth_filepath(self):
        return join(self.license_folder, self.auth_filename)

    def _get_license_strings(self):
        return self.license_key.key.strip().split(':')

    @on_trait_change('license_key.key')
    def update_dates(self):
        license_strings = self.license_strings
        if not len(license_strings) == 4:
            return

        self.start_date = datetime.datetime.strptime(license_strings[1],
                                                     DATE_FORMAT)
        self.last_date = datetime.datetime.strptime(license_strings[2],
                                                    DATE_FORMAT)
        self.stop_date = datetime.datetime.strptime(license_strings[3],
                                                    DATE_FORMAT)


def check_license(manager=None, **manager_traits):
    """ Utility to create a LicenseManager and validate the license key.

    If there is no license file, a new key will be requested by a UI.

    Parameters
    ----------
    manager : LicenseManager [OPTIONAL]
        Manager to use. Leave blank to create a new one.

    manager_traits : dict [OPTIONAL]
        Attributes of the LicenseManager to create if non is passed.

    Returns
    -------
    bool
        Whether the license found is valid.
    """
    if manager is None:
        manager = LicenseManager(**manager_traits)

    try:
        valid = manager.validate_license_key()
        if valid:
            return valid, "1"
        if not valid:
            valid2 = manager.validate_license_key(salt="alt")
            return valid2, "2"
    except Exception as e:
        msg = "Failed to run the validation check. Error was {}".format(e)
        logger.exception(msg)
        error(None, VALIDATION_ERROR_MSG, "Unable to validate license")


def generate_license_key(start_date, stop_date, manager, salt="default"):
    """Create and return a new valid license key (string).

    The last use date will be set to the start date.

    Parameters
    ----------
    start_date : str or datetime
        Date in the format set by DATE_FORMAT for the license to start working.

    stop_date : str or datetime
        Date in the format set by DATE_FORMAT for the license to stop working.

    manager : LicenseManager
        License manager configured with the desired parameters (salt, username,
        ...).

    salt : str
        Salt to use for the hashing. Set to 'alt' to use the alternate salt if
        any available.
    """
    if isinstance(start_date, string_types):
        start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)

    if isinstance(stop_date, string_types):
        stop_date = datetime.datetime.strptime(stop_date, DATE_FORMAT)

    manager.start_date = start_date
    manager.stop_date = stop_date
    return manager.generate_key(start_date, salt=salt)
