"""
Scrape EveryTrail trip page(s) and download their contents, including GPS data,
story, and photos.
"""
import os

import re
import time

import requests
import simplejson as json
from pyquery import PyQuery as pq

DEFAULT_RETRIES_MESSAGE = "Retried too many times. Maybe EveryTrail is down?"

URL_BASE = 'http://www.everytrail.com'
TRIP_URL_RE = re.compile('\/view_trip\.php\?trip_id=(\d+)')
TRIP_URL_TEMPLATE = '/view_trip.php?trip_id={0}'
GPX_URL_TEMPLATE = '/downloadGPX.php?trip_id={0}'
KML_URL_TEMPLATE = '/downloadKML.php?trip_id={0}'

def normalize_arg_to_id(arg):
    if re.match('^\d+$', arg):
        return arg
    else:
        result = TRIP_URL_RE.search(arg)
        if result:
            return result.group(1)
        else:
            raise Exception("Argument is neither trip ID nor trip page URL: {0}".format(arg))

def trip_name_to_directory_name(name):
    """Convert a name like "Mt. Tam: Ridgecrest Blvd to Alpine Lake via..." to
    something like "mt-tam-ridgecrest-blvd-to-alpi".
    """
    out = name.lower()
    out = re.sub('[:/\ ]', '-', out)
    out = re.sub('[.,]', '', out)
    out = re.sub('--+', '-', out)
    out = out[:30]
    return out

def save_to_file(trip_dir, filename, content, mode='w'):
    dest = os.path.join(trip_dir, filename)
    with open(dest,  mode) as f:
        f.write(content)
    print "  Saved", dest

def encode_html_for_file(html):
    """Hack in a meta tag at the top of an HTML snippet to make the resulting
    file display correctly in a web browser."""
    return ('<meta charset="utf-8">\n' + html).encode('utf-8')

class EveryTrailScraper(object):
    DEFAULT_MAX_RETRIES = 5

    def __init__(self, out_dir, trailauth_cookie=None, skip_photos=False, max_retries=DEFAULT_MAX_RETRIES):
        self._out_dir = out_dir
        self._trailauth_cookie = trailauth_cookie
        self._skip_photos = skip_photos
        self._max_retries = max_retries

    def get_trip_ids_from_listing_page(self, trips_page_url):
        print "Scraping {0} for trip URLs...".format(trips_page_url)
        trips_page = self.get_html(trips_page_url)
        trip_ids = sorted([
            normalize_arg_to_id(url)
            for url in
            trips_page.find('a').map(lambda _, a: a.attrib['href'])
            if TRIP_URL_RE.search(url)
        ])
        print "Found links to {0} trips: {1}".format(len(trip_ids), " ".join(trip_ids))
        return trip_ids

    def download_trip(self, trip_id):
        trip_url = URL_BASE + TRIP_URL_TEMPLATE.format(trip_id)
        print "Downloading", format(trip_url)

        trip_page = self.get_html(trip_url)

        title = trip_page.find('h1 span').text()
        location = re.sub('^(-\s+)+', '', trip_page.find('h1').remove('span').text())

        # Output dir == something like 'trails/1820769-mt-tam-ridgecrest-blvd-to-al'
        trip_dir = os.path.join(self._out_dir, '-'.join([trip_id, trip_name_to_directory_name(title)]))
        try:
            os.makedirs(trip_dir)
        except OSError:
            pass

        print "  {0} - {1}".format(title, location)
        save_to_file(trip_dir, 'title.txt', '\n'.join([title, location]))

        info_html = trip_page.find('.main-column-container.left > div > div').eq(0).html()
        save_to_file(trip_dir, 'info.html', encode_html_for_file(info_html))

        stats_html = trip_page.find('.right-column.left .content').filter(
            lambda _, e: 'Trip Info' in pq(e).text()
        ).html()
        save_to_file(trip_dir, 'stats.html', encode_html_for_file(stats_html))

        if self._trailauth_cookie:
            print "  Saving GPX and KML files..."

            gpx_url = URL_BASE + GPX_URL_TEMPLATE.format(trip_id)
            print "  Downloading", gpx_url
            gpx = self.get_gpx(gpx_url)
            save_to_file(trip_dir, '{0}.gpx'.format(trip_id), gpx)

            # The main reason to download this is that the GPX file does not include
            # manually-added waypoints, but the KML does.
            kml_url = URL_BASE + KML_URL_TEMPLATE.format(trip_id)
            print "  Downloading", kml_url
            kmz = self.get_kml(kml_url)
            save_to_file(trip_dir, '{0}.kmz'.format(trip_id), kmz, mode='wb')
        else:
            print "  ----- Skipping GPX and KML files, since no TRAILAUTH cookie was provided. -----"

        if not self._skip_photos:
            photos_link = trip_page.find('a').filter(lambda _, a: 'See all pictures' in pq(a).text())
            if photos_link:
                photos_page_url = URL_BASE + photos_link.eq(0).attr('href')
                self.download_photos(trip_dir, photos_page_url)

    def download_photos(self, trip_dir, photos_page_url):
        images_dir = os.path.join(trip_dir, 'images')
        try:
            os.makedirs(images_dir)
        except OSError:
            pass

        print "  Downloading photos page:", photos_page_url
        photos_page = self.get_html(photos_page_url)
        photo_urls = [
            URL_BASE + e.attrib['href']
            for e
            in photos_page.find('.pictures-container .center a')
        ]

        photo_info = []
        for i, photo_url in enumerate(photo_urls):
            print "  Photo {0}/{1}:".format(i + 1, len(photo_urls))
            time.sleep(1)
            photo_info.append(
                self.extract_info_and_download_full_photo(images_dir, photo_url)
            )

        save_to_file(trip_dir, 'photo_info.json', json.dumps(photo_info, indent=4 * ' ').encode('utf-8'))

    def extract_info_and_download_full_photo(self, images_dir, photo_url):
        print "    Downloading photo info page:", photo_url
        photo_page = self.get_html(photo_url)
        lat_lng = re.search('GLatLng\(([^)]+)\)', photo_page.html()).group(1)
        lat, lng = map(float, lat_lng.split(', '))
        photo_title = photo_page.find('h2.big-title').text()

        original_image_page_url = URL_BASE + photo_page.find('a').filter(
            lambda _, a: 'View Original' in pq(a).text()
        ).attr('href')

        print "    Finding full photo:", original_image_page_url
        original_image_page = self.get_html(original_image_page_url)
        image_url = original_image_page.find('img').attr('src')
        image_filename = image_url.split('/')[-1]
        dest_filename = os.path.join(images_dir, image_filename)

        print "    Downloading full photo:", image_url
        with open(dest_filename, 'wb') as f:
            for chunk in requests.get(image_url, stream=True):
                f.write(chunk)
        print '    Saved "{0}" to {1}'.format(photo_title, dest_filename)

        return {
            'lat': lat,
            'lng': lng,
            'title': photo_title,
            'filename': image_filename,
        }

    def get_html(self, url, retry_count=0):
        resp = self._get_with_retries(url, max_retries_message=DEFAULT_RETRIES_MESSAGE)
        return pq(resp.content)

    def get_gpx(self, url):
        error_help = """Did you enter your TRAILAUTH cookie correctly?
Can you access {0} directly from your browser?""".format(url)

        resp = self._get_with_retries(url, max_retries_message="Retried too many times.\n" + error_help)

        expected_content_type = 'application/gpx+xml'
        if resp.headers['Content-type'] != expected_content_type:
            raise Exception('\n'.join([
                'GPX response came back with content-type "{0}", expected "{1}"'.format(resp.headers['Content-type'], expected_content_type),
                'Content: "{0}"'.format(resp.content[:100]),
                error_help]))

        return resp.content

    def get_kml(self, url):
        # Presumably, if we made it to this point after downloading the GPX file,
        # then a failure isn't due to cookie problems, so use the default message
        resp = self._get_with_retries(url, max_retries_message=DEFAULT_RETRIES_MESSAGE)
        return resp.content

    def _get_with_retries(self, url, max_retries_message, retry_count=0):
        if retry_count >= self._max_retries:
            raise Exception(max_retries_message)
        resp = requests.get(url, cookies={'TRAILAUTH': self._trailauth_cookie})

        problem = None
        if resp.status_code != 200:
            problem = "Response came back with HTTP status {0}".format(resp.status_code)
        elif "Application error" in resp.content:
            problem = 'Response came back "Application error"'

        if problem:
            seconds = 2 ** (retry_count + 1)
            print "{0}; trying again in {1} seconds...".format(problem, seconds)
            time.sleep(seconds)
            return self._get_with_retries(url, max_retries_message, retry_count=retry_count + 1)
        else:
            return resp
