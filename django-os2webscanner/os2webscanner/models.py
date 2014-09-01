# encoding: utf-8
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

"""Contains Django models for the Webscanner."""

import os
import shutil
from subprocess import Popen
import re
import datetime
import json

from django.db import models
from django.contrib.auth.models import User
from recurrence.fields import RecurrenceField

from .utils import notify_user
from django.conf import settings


# Sensitivity values
class Sensitivity:

    """Name space for sensitivity values."""

    HIGH = 2
    LOW = 1
    OK = 0

    choices = (
        (OK, u'Grøn'),
        (LOW, u'Gul'),
        (HIGH, u'Rød'),
    )


class Organization(models.Model):

    """Represents the organization for each user and scanner, etc.

    Users can only see material related to their own organization.
    """

    name = models.CharField(max_length=256, unique=True, verbose_name='Navn')
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name='Telefon')

    def __unicode__(self):
        """Return the name of the organization."""
        return self.name


class UserProfile(models.Model):

    """OS2 Web Scanner specific user profile.

    Each user MUST be associated with an organization.
    """

    organization = models.ForeignKey(Organization,
                                     null=False,
                                     verbose_name='Organisation')
    user = models.ForeignKey(User,
                             unique=True,
                             related_name='profile',
                             verbose_name='Bruger')

    def __unicode__(self):
        """Return the user's username."""
        return self.user.username


class Domain(models.Model):

    """Represents a domain to be scanned."""

    # Validation status

    VALID = 1
    INVALID = 0

    validation_choices = (
        (INVALID, "Ugyldig"),
        (VALID, "Gyldig"),
    )

    # Validation methods

    ROBOTSTXT = 0
    WEBSCANFILE = 1
    METAFIELD = 2

    validation_method_choices = (
        (ROBOTSTXT, 'robots.txt'),
        (WEBSCANFILE, 'webscan.html'),
        (METAFIELD, 'Meta-felt'),
    )

    url = models.CharField(max_length=2048, verbose_name='Url')
    organization = models.ForeignKey(Organization,
                                     null=False,
                                     related_name='domains',
                                     verbose_name='Organisation')
    validation_status = models.IntegerField(choices=validation_choices,
                                            default=INVALID,
                                            verbose_name='Valideringsstatus')
    validation_method = models.IntegerField(choices=validation_method_choices,
                                            default=ROBOTSTXT,
                                            verbose_name='Valideringsmetode')
    exclusion_rules = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Ekskluderingsregler')
    sitemap = models.FileField(upload_to='sitemaps',
                               blank=True,
                               verbose_name='Sitemap')

    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return "Domain '%s'" % self.root_url

    def exclusion_rule_list(self):
        """Return the exclusion rules as a list of strings or regexes."""
        REGEX_PREFIX = "regex:"
        rules = []
        for line in self.exclusion_rules.splitlines():
            line = line.strip()
            if line.startswith(REGEX_PREFIX):
                rules.append(re.compile(line[len(REGEX_PREFIX):],
                                        re.IGNORECASE))
            else:
                rules.append(line)
        return rules

    @property
    def root_url(self):
        """Return the root url of the domain."""
        if (not self.url.startswith('http://') and not
            self.url.startswith('https://')):
            return 'http://%s/' % self.url
        else:
            return self.url

    @property
    def sitemap_full_path(self):
        """Get the absolute path to the uploaded sitemap.xml file."""
        return "%s/%s" % (settings.BASE_DIR, self.sitemap.url)

    def get_absolute_url(self):
        """Get the absolute URL for domains."""
        return '/domains/'

    def __unicode__(self):
        """Return the URL for the domain."""
        return self.url


class RegexRule(models.Model):

    """Represents matching rules based on regular expressions."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    match_string = models.CharField(max_length=1024, blank=False,
                                    verbose_name='Udtryk')

    description = models.TextField(verbose_name='Beskrivelse')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

    @property
    def display_name(self):
        """The name used when displaying the regexrule on the web page."""
        return "Regel '%s'" % self.name

    def get_absolute_url(self):
        """Get the absolute URL for rules."""
        return '/rules/'

    def __unicode__(self):
        """Return the name of the rule."""
        return self.name


class Scanner(models.Model):

    """A scanner, i.e. a template for actual scanning jobs."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    whitelisted_names = models.TextField(max_length=4096, blank=True,
                                         default="",
                                         verbose_name='Godkendte navne')
    domains = models.ManyToManyField(Domain, related_name='scanners',
                                     null=False, verbose_name='Domæner')
    do_cpr_scan = models.BooleanField(default=True, verbose_name='CPR')
    do_name_scan = models.BooleanField(default=True, verbose_name='Navn')
    do_ocr = models.BooleanField(default=True, verbose_name='Scan billeder?')
    regex_rules = models.ManyToManyField(RegexRule,
                                         blank=True,
                                         null=True,
                                         verbose_name='Regex regler')

    # DON'T USE DIRECTLY !!!
    # Use process_urls property instead.
    encoded_process_urls = models.CharField(
        max_length=262144,
        null=True,
        blank=True
    )
    # Booleans for control of scanners run from web service.
    do_run_synchronously = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)

    def _get_process_urls(self):
        s = self.encoded_process_urls
        if s:
            urls = json.loads(s)
        else:
            urls = []
        return urls

    def _set_process_urls(self, urls):
        self.encoded_process_urls = json.dumps(urls)

    process_urls = property(_get_process_urls, _set_process_urls)

    # First possible start time
    FIRST_START_TIME = datetime.time(18, 0)
    # Amount of quarter-hours that can be added to the start time
    STARTTIME_QUARTERS = 6 * 4

    def get_start_time(self):
        """The time of day the Scanner should be automatically started."""
        added_minutes = 15 * (self.pk % Scanner.STARTTIME_QUARTERS)
        added_hours = int(added_minutes / 60)
        added_minutes -= added_hours * 60
        return Scanner.FIRST_START_TIME.replace(
            hour=Scanner.FIRST_START_TIME.hour + added_hours,
            minute=Scanner.FIRST_START_TIME.minute + added_minutes
        )

    @classmethod
    def modulo_for_starttime(cls, time):
        """Convert a datetime.time object to the corresponding modulo value.

        The modulo value can be used to search the database for scanners that
        should be started at the given time by filtering a query with:
            (Scanner.pk % Scanner.STARTTIME_QUARTERS) == <modulo_value>
        """
        if(time < cls.FIRST_START_TIME):
            return None
        hours = time.hour - cls.FIRST_START_TIME.hour
        minutes = 60 * hours + time.minute - cls.FIRST_START_TIME.minute
        return int(minutes / 15)

    @property
    def display_name(self):
        """The name used when displaying the scanner on the web page."""
        return "Scanner '%s'" % self.name

    @property
    def schedule_description(self):
        """A lambda for creating schedule description strings."""
        f = lambda s: "Schedule: " + s
        return f

    @property
    def has_active_scans(self):
        """Whether the scanner has active scans."""
        active_scanners = Scan.objects.filter(scanner=self, status__in=(
                        Scan.NEW, Scan.STARTED)).count()
        return active_scanners > 0

    def run(self, test_only=False):
        """Run a scan with the Scanner.

        Return the Scan object if we started the scanner.
        Return None if there is already a scanner running,
        or if there was a problem running the scanner.
        If test_only is True, only check if we can run a scan, don't actually
        run one.
        """
        if self.has_active_scans:
            return None
        # Create a new Scan
        scan = Scan(scanner=self, status=Scan.NEW)
        scan.save()
        # Get path to run script
        SCRAPY_WEBSCANNER_DIR = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(
                os.path.realpath(__file__)))), "scrapy-webscanner")

        if test_only:
            return scan
        try:
            process = Popen([os.path.join(SCRAPY_WEBSCANNER_DIR, "run.sh"),
                         str(scan.pk)], cwd=SCRAPY_WEBSCANNER_DIR)
        except Exception as e:
            return None
        return scan

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/scanners/'

    def __unicode__(self):
        """Return the name of the scanner."""
        return self.name


class Scan(models.Model):

    """An actual instance of the scanning process done by a scanner."""

    scanner = models.ForeignKey(Scanner, null=False, verbose_name='Scanner',
                                related_name='scans')
    start_time = models.DateTimeField(blank=True, null=True,
                                      verbose_name='Starttidspunkt')
    end_time = models.DateTimeField(blank=True, null=True,
                                    verbose_name='Sluttidspunkt')

    # Scan status
    NEW = "NEW"
    STARTED = "STARTED"
    DONE = "DONE"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (STARTED, "I gang"),
        (DONE, "OK"),
        (FAILED, "Fejlet"),
    )

    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW)

    @property
    def status_text(self):
        """A display text for the scan's status.

        Relies on the restriction that the status must be one of the allowed
        values.
        """
        text = [t for s, t in Scan.status_choices if self.status == s][0]
        return text

    @property
    def scan_dir(self):
        """The directory associated with this scan."""
        return os.path.join(settings.VAR_DIR, 'scan_%s' % self.pk)

    # Reason for failure
    reason = models.CharField(max_length=1024, blank=True, default="",
                              verbose_name='Årsag')
    pid = models.IntegerField(null=True, blank=True, verbose_name='Pid')

    def get_number_of_failed_conversions(self):
        """The number conversions that has failed during this scan."""
        return ConversionQueueItem.objects.filter(
            url__scan=self,
            status=ConversionQueueItem.FAILED
        ).count()

    def __unicode__(self):
        """Return the name of the scan's scanner."""
        return "SCAN: " + self.scanner.name

    def save(self, *args, **kwargs):
        """Save changes to the scan.

        Sets the end_time for the scan, notifies the associated user by email,
        deletes any remaining queue items and deletes the temporary directory
        used by the scan.
        """
        # Pre-save stuff
        if (self.status in [Scan.DONE, Scan.FAILED] and
            (self._old_status != self.status)):
            self.end_time = datetime.datetime.now()
        # Actual save
        super(Scan, self).save(*args, **kwargs)
        # Post-save stuff

        if (self.status in [Scan.DONE, Scan.FAILED] and
            (self._old_status != self.status)):
            # Send email
            notify_user(self)

            # Delete all pending conversionqueue items
            ConversionQueueItem.objects.filter(
                url__scan=self,
                status=ConversionQueueItem.NEW
            ).delete()

            # remove all files associated with the scan
            scan_dir = self.scan_dir
            if os.access(scan_dir, os.W_OK):
                shutil.rmtree(scan_dir, True)
            self._old_status = self.status

    def __init__(self, *args, **kwargs):
        """Initialize a new scan.

        Stores the old status of the scan for later use.
        """
        super(Scan, self).__init__(*args, **kwargs)
        self._old_status = self.status
        
    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('report', args=[str(self.id)])




class Url(models.Model):

    """A representation of an actual URL on a domain with its MIME type."""

    url = models.CharField(max_length=2048, verbose_name='Url')
    mime_type = models.CharField(max_length=256, verbose_name='Mime-type')
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan')

    def __unicode__(self):
        """Return the URL."""
        return self.url

    @property
    def tmp_dir(self):
        """The path to the temporary directory associated with this url."""
        return os.path.join(self.scan.scan_dir, 'url_item_%d' % (self.pk))


class Match(models.Model):

    """The data associated with a single match in a single URL."""

    url = models.ForeignKey(Url, null=False, verbose_name='Url')
    scan = models.ForeignKey(Scan, null=False, verbose_name='Scan')
    matched_data = models.CharField(max_length=1024, verbose_name='Data match')
    matched_rule = models.CharField(max_length=256, verbose_name='Regel match')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

    def get_matched_rule_display(self):
        """Return a display name for the rule."""
        if self.matched_rule == 'cpr':
            return "CPR"
        elif self.matched_rule == 'name':
            return "Navn"
        else:
            return self.matched_rule

    def get_sensitivity_class(self):
        """Return the bootstrap CSS class for the sensitivty."""
        if self.sensitivity == Sensitivity.HIGH:
            return "danger"
        elif self.sensitivity == Sensitivity.LOW:
            return "warning"
        elif self.sensitivity == Sensitivity.OK:
            return "success"

    def __unicode__(self):
        """Return a string representation of the match."""
        return u"Match: %s; [%s] %s <%s>" % (self.get_sensitivity_display(),
                                             self.matched_rule,
                                             self.matched_data, self.url)


class ConversionQueueItem(models.Model):

    """Represents an item in the conversion queue."""

    file = models.CharField(max_length=4096, verbose_name='Fil')
    type = models.CharField(max_length=256, verbose_name='Type')
    url = models.ForeignKey(Url, null=False, verbose_name='Url')

    # Note that SUCCESS is indicated by just deleting the record
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"

    status_choices = (
        (NEW, "Ny"),
        (PROCESSING, "I gang"),
        (FAILED, "Fejlet"),
    )
    status = models.CharField(max_length=10, choices=status_choices,
                              default=NEW, verbose_name='Status')

    process_id = models.IntegerField(blank=True, null=True,
                                     verbose_name='Proces id')
    process_start_time = models.DateTimeField(
        blank=True, null=True, verbose_name='Proces starttidspunkt'
    )

    @property
    def file_path(self):
        """Return the full path to the conversion queue item's file."""
        return self.file

    @property
    def tmp_dir(self):
        """The path to the temporary dir associated with this queue item."""
        return os.path.join(
            self.url.scan.scan_dir,
            'queue_item_%d' % (self.pk)
        )
