# -*- coding: utf-8 -*-

import logging

import nagiosplugin as np
from datetime import datetime

from check_pa.xml_reader import XMLReader, Finder

_log = logging.getLogger('nagiosplugin')


def get_now():
    """
    Extract method for mocking datetime.now.

    :return: datetime.today() object
    """
    return datetime.today()  # pragma: no cover


def create_check(args):
    """
    Creates and configures a check for the antivirus command.

    :return: the throughput check.
    """
    return np.Check(
        Antivirus(args.host, args.token),
        np.ScalarContext('av-release-days', args.warn, args.crit),
        AntivirusSummary())


class Antivirus(np.Resource):
    """
    Will fetch the antivirus definition date from the REST API and returns
    a warning if the definition date is between the value of warning (e. g. 1)
    and critical (e. g. 2).
    """

    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.cmd = '<show><system><info></info></system></show>'
        self.xml_obj = XMLReader(self.host, self.token, self.cmd)

    def probe(self):
        """
        Querys the REST-API and create antivirus metrics.

        :return: antivirus metric.
        """
        _log.info('Reading XML from: %s', self.xml_obj.build_request_url())
        soup = self.xml_obj.read()
        result = soup.result
        av_release_date = Finder.find_item(result, 'av-release-date').split(' ')[0]
        # 2019/01/06  04:03:50
        now = get_now()
        date_object = datetime.strptime(av_release_date, '%Y/%m/%d')
        av_version = Finder.find_item(result, 'av-version')

        difference = now - date_object
        _log.info('Difference: %s days (%s -- %s)'  % (difference.days, av_release_date, get_now()))

        return [np.Metric('av-release-days', difference.days, context='av-release-days')]


class AntivirusSummary(np.Summary):
    def ok(self, results):
        l = []
        for result in results.results:
            s = '%s: %s' % (result.metric.name, result.metric.value)
            _log.debug('Add result %r', s)
            l.append(s)
        _log.debug('Result count: %d' % len(l))
        output = ", ".join(l)
        return str(output)
