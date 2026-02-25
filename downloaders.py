# -*- coding: utf-8 -*-
"""
Module for download-related classes and functions.
"""

from __future__ import print_function

import logging
import math
import os
import subprocess
import sys
import time

import requests

#
# Below are file downloaders, they are wrappers for external downloaders.
#

class Downloader(object):
    """
    Base downloader class.
    """

    def _start_download(self, url, filename, resume):
        raise NotImplementedError("Subclasses should implement this")

    def download(self, url, filename, resume=False):
        try:
            self._start_download(url, filename, resume)
        except KeyboardInterrupt as e:
            if not resume:
                logging.info('Keyboard Interrupt -- Removing partial file: %s',
                             filename)
                try:
                    os.remove(filename)
                except OSError:
                    pass
            raise e


class ExternalDownloader(Downloader):
    """
    Downloads files with an external downloader.
    """

    bin = None

    def __init__(self, session, bin=None, downloader_arguments=None):
        self.session = session
        self.bin = bin or self.__class__.bin
        self.downloader_arguments = downloader_arguments or []

        if not self.bin:
            raise RuntimeError("No bin specified")

        self._check_bin()

    def _prepare_cookies(self, command, url):
        req = requests.models.Request()
        req.method = 'GET'
        req.url = url

        cookie_values = requests.cookies.get_cookie_header(
            self.session.cookies, req)

        if cookie_values:
            self._add_cookies(command, cookie_values)

    def _enable_resume(self, command):
        raise RuntimeError("Subclass should implement this")

    def _add_cookies(self, command, cookie_values):
        raise RuntimeError("Subclasses should implement this")

    def _create_command(self, url, filename):
        raise NotImplementedError("Subclasses should implement this")

    def _check_bin(self):
        try:
            ret = subprocess.run([self.bin, "--version"])
        except FileNotFoundError:
            raise RuntimeError(f"Downloader '{self.bin}' not found")

        if(ret.returncode != 0):
            raise RuntimeError(f"Downloader '{self.bin}' returned a non-zero exit status")

    def _start_download(self, url, filename, resume):
        command = self._create_command(url, filename)
        command.extend(self.downloader_arguments)
        self._prepare_cookies(command, url)
        if resume:
            self._enable_resume(command)

        logging.debug('Executing %s: %s', self.bin, command)
        
        # --- MODIFICACIÓN PARA GUI: Avisar nombre de archivo ---
        logging.info('DOWNLOADING_FILE: %s', os.path.basename(filename))
        # -------------------------------------------------------

        try:
            subprocess.call(command)
        except OSError as e:
            msg = "{0}. Are you sure that '{1}' is the right bin?".format(
                e, self.bin)
            raise OSError(msg)


class WgetDownloader(ExternalDownloader):
    bin = 'wget'

    def _enable_resume(self, command):
        command.append('-c')

    def _add_cookies(self, command, cookie_values):
        command.extend(['--header', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-O', filename, '--no-cookies',
                '--no-check-certificate']


class CurlDownloader(ExternalDownloader):
    bin = 'curl'

    def _enable_resume(self, command):
        command.extend(['-C', '-'])

    def _add_cookies(self, command, cookie_values):
        command.extend(['--cookie', cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-k', '-#', '-L', '-o', filename]


class Aria2Downloader(ExternalDownloader):
    bin = 'aria2c'

    def _enable_resume(self, command):
        command.append('-c')

    def _add_cookies(self, command, cookie_values):
        command.extend(['--header', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, url, '-o', filename,
                '--check-certificate=false', '--log-level=notice',
                '--max-connection-per-server=4', '--min-split-size=1M']


class AxelDownloader(ExternalDownloader):
    bin = 'axel'

    def _enable_resume(self, command):
        logging.warn('Resume download not implemented for this '
                     'downloader!')

    def _add_cookies(self, command, cookie_values):
        command.extend(['-H', "Cookie: " + cookie_values])

    def _create_command(self, url, filename):
        return [self.bin, '-o', filename, '-n', '4', '-a', url]


def format_bytes(bytes):
    """
    Get human readable version of given bytes.
    """
    if bytes is None:
        return 'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return '{0:.2f}{1}'.format(converted, suffix)


class DownloadProgress(object):
    """
    Report download progress.
    """

    def __init__(self, total):
        if total in [0, '0', None]:
            self._total = None
        else:
            self._total = int(total)

        self._current = 0
        self._start = 0
        self._now = 0

        self._finished = False
        self._last_percent = -1  # Para controlar el envío a la GUI

    def start(self):
        self._now = time.time()
        self._start = self._now

    def stop(self):
        self._now = time.time()
        self._finished = True
        self._total = self._current
        self.report_progress()

    def read(self, bytes):
        self._now = time.time()
        self._current += bytes
        self.report_progress()

    def report(self, bytes):
        self._now = time.time()
        self._current = bytes
        self.report_progress()

    def calc_percent(self):
        if self._total is None:
            return '--%'
        if self._total == 0:
            return '100% done'
        
        percentage = int(float(self._current) / float(self._total) * 100.0)
        
        # --- MODIFICACIÓN PARA GUI: Enviar señal solo si cambia el % ---
        if percentage != self._last_percent:
            logging.info('PROGRESS_BAR:%d', percentage)
            self._last_percent = percentage
        # -------------------------------------------------------------

        done = int(percentage / 2)
        return '[{0: <50}] {1}%'.format(done * '#', percentage)

    def calc_speed(self):
        dif = self._now - self._start
        if self._current == 0 or dif < 0.001:
            return '---b/s'
        return '{0}/s'.format(format_bytes(float(self._current) / dif))

    def report_progress(self):
        """Report download progress."""
        percent = self.calc_percent()
        total = format_bytes(self._total)

        speed = self.calc_speed()
        total_speed_report = '{0} at {1}'.format(total, speed)

        report = '\r{0: <56} {1: >30}'.format(percent, total_speed_report)

        if self._finished:
            print(report)
            # Asegurar 100% al final
            logging.info('PROGRESS_BAR:100')
        else:
            print(report, end="")
        sys.stdout.flush()


class NativeDownloader(Downloader):
    """
    'Native' python downloader -- slower than the external downloaders.
    """

    def __init__(self, session):
        self.session = session

    def _start_download(self, url, filename, resume=False):
        # resume has no meaning if the file doesn't exists!
        resume = resume and os.path.exists(filename)

        headers = {}
        filesize = None
        if resume:
            filesize = os.path.getsize(filename)
            headers['Range'] = 'bytes={}-'.format(filesize)
            logging.info('Resume downloading %s -> %s', url, filename)
        else:
            logging.info('Downloading %s -> %s', url, filename)

        # --- MODIFICACIÓN PARA GUI: Avisar nombre de archivo limpio ---
        logging.info('DOWNLOADING_FILE: %s', os.path.basename(filename))
        # --------------------------------------------------------------

        max_attempts = 3
        attempts_count = 0
        error_msg = ''
        
        while attempts_count < max_attempts:
            try:
                r = self.session.get(url, stream=True, headers=headers)

                if r.status_code != 200:
                    if resume and r.status_code == 206:
                        pass
                    elif resume and r.status_code == 416:
                        logging.info('%s already downloaded', filename)
                        r.close()
                        logging.info('PROGRESS_BAR:100') # GUI Fix
                        return True
                    else:
                        print('%s %s %s' % (r.status_code, url, filesize))
                        logging.warn('Probably the file is missing from the AWS '
                                     'repository...  waiting.')

                        if r.reason:
                            error_msg = r.reason + ' ' + str(r.status_code)
                        else:
                            error_msg = 'HTTP Error ' + str(r.status_code)

                        raise requests.exceptions.RequestException(error_msg)

                if resume and r.status_code == 200:
                    resume = False

                content_length = r.headers.get('content-length')
                total_length = int(content_length) if content_length else None
                
                # Manejo especial para contenido parcial en la barra de progreso
                if r.status_code == 206:
                     # Si es 206, content-length es lo que falta, no el total.
                     # Intentamos calcular el total real para la GUI si es posible
                     pass 

                chunk_sz = 1048576 # 1MB original (puedes bajarlo a 256*1024 si quieres más fluidez)
                progress = DownloadProgress(total_length)
                progress.start()
                
                f = open(filename, 'ab') if resume else open(filename, 'wb')
                
                for chunk in r.iter_content(chunk_size=chunk_sz):
                    if chunk:
                        f.write(chunk)
                        progress.read(len(chunk))
                
                progress.stop()
                f.close()
                r.close()
                return True

            except Exception as e:
                logging.warning('Error downloading (attempt %d/%d): %s',
                                attempts_count + 1, max_attempts, str(e))
                wait_interval = 2 ** (attempts_count + 1)
                time.sleep(wait_interval)
                attempts_count += 1
                continue

        if attempts_count == max_attempts:
            logging.warn('Skipping, can\'t download file ...')
            logging.error(error_msg)
            return False


def get_downloader(session, class_name, args):
    """
    Decides which downloader to use.
    """

    external = {
        'wget': WgetDownloader,
        'curl': CurlDownloader,
        'aria2': Aria2Downloader,
        'axel': AxelDownloader,
    }

    for bin, class_ in external.items():
        if getattr(args, bin):
            return class_(session, bin=getattr(args, bin),
                          downloader_arguments=args.downloader_arguments)

    return NativeDownloader(session)