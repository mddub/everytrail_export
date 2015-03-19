import os
import re
import time

import requests
import simplejson as json
from pyquery import PyQuery as pq

URL_BASE = 'http://www.everytrail.com'
TRIP_URL_TEMPLATE = '/view_trip.php?trip_id={0}'
OUT_DIR = 'trails'

def trip_name_to_directory_name(name):
    """Convert a name like "Mt. Tam: Ridgecrest Blvd to Alpine Lake via..." to
    something like "mt-tam-ridgecrest-blvd-to-alpi".
    """
    out = name.lower()
    out = re.sub('[:/\ ]', '-', out)
    out = re.sub('\.', '', out)
    out = re.sub('--+', '-', out)
    out = out[:30]
    return out

def get_html(url, retry_count=0):
    if retry_count >= 3:
        raise Exception("Retried too many times. Maybe EveryTrail is down?")
    resp = requests.get(url)
    if resp.status_code == 200:
        return pq(resp.content)
    else:
        print "----- Response came back with HTTP status {0}; trying again... -----".format(resp.status_code)
        return get_html(url, retry_count=retry_count+1)

def save_to_file(trip_dir, filename, content):
    dest = os.path.join(trip_dir, filename)
    with open(dest,  'w') as f:
        f.write(content)
    print "  Saved", dest

def download_trip(trip_id):
    trip_url = URL_BASE + TRIP_URL_TEMPLATE.format(trip_id)
    print "Downloading {0}".format(trip_url)
    trip_page = get_html(trip_url)

    title = trip_page.find('h1 span').text()
    location = re.sub('^(-\s+)+', '', trip_page.find('h1').remove('span').text())

    # Output dir == something like 'trails/1820769-mt-tam-ridgecrest-blvd-to-al'
    trip_dir = os.path.join(OUT_DIR, '-'.join([trip_id, trip_name_to_directory_name(title)]))
    try:
        os.makedirs(trip_dir)
    except OSError:
        pass

    print "  {0} - {1}".format(title, location)
    save_to_file(trip_dir, 'title.txt', '\n'.join([title, location]))

    info_html = trip_page.find('.main-column-container.left > div > div').eq(0).html()
    save_to_file(trip_dir, 'info.html', info_html.encode('utf-8'))

    stats_html = trip_page.find('.right-column.left .content').filter(
        lambda _, e: 'Trip Info' in pq(e).text()
    ).html()
    save_to_file(trip_dir, 'stats.html', stats_html.encode('utf-8'))

    photos_link = trip_page.find('a').filter(lambda _, a: 'See all pictures' in pq(a).text())
    if photos_link:
        photos_page_url = URL_BASE + photos_link.eq(0).attr('href')
        download_photos(trip_dir, photos_page_url)

def download_photos(trip_dir, photos_page_url):
    images_dir = os.path.join(trip_dir, 'images')
    try:
        os.makedirs(images_dir)
    except OSError:
        pass

    print "  Downloading photos page:", photos_page_url
    photos_page = get_html(photos_page_url)
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
            extract_info_and_download_full_photo(images_dir, photo_url)
        )

    save_to_file(trip_dir, 'photo_info.json', json.dumps(photo_info, indent=4 * ' ').encode('utf-8'))

def extract_info_and_download_full_photo(images_dir, photo_url):
    print "    Downloading photo info page:", photo_url
    photo_page = get_html(photo_url)
    lat_lng = re.search('GLatLng\(([^)]+)\)', photo_page.html()).group(1)
    lat, lng = map(float, lat_lng.split(', '))
    photo_title = photo_page.find('h2.big-title').text()

    original_image_page_url = URL_BASE + photo_page.find('a').filter(
        lambda _, a: 'View Original' in pq(a).text()
    ).attr('href')

    print "    Finding full photo:", original_image_page_url
    original_image_page = get_html(original_image_page_url)
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

# TODO: could get this from a user's trip listing page
my_trips = ["1550019", "1673357", "1693258", "1733157", "1741278", "1820769", "1924844", "1924847", "2022884", "2053816", "2108623", "2301920", "2348794", "2671553", "2991898"]

for i, trip_id in enumerate(my_trips):
    print "Trip {0}/{1}:".format(i + 1, len(my_trips))
    download_trip(trip_id)
